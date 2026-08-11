"""Materialize the current fixed and seeded research suites as JSON files."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import random

from dag_heuristic.benchmark import Benchmark, write_benchmark
from benchmark_generate.convert import (
    dag_to_benchmark,
    multi_resource_to_benchmark,
    parallel_chains_to_benchmark,
)


@dataclass(frozen=True)
class ExportedCase:
    benchmark: Benchmark
    relative_path: Path


def current_cases(*, samples: int, seed: int) -> list[ExportedCase]:
    from dag_heuristic.algorithms.single_channel.parallel_chain.solver import ParallelChain
    from benchmark_generate.scenarios import (
        fixed_beam_counterexample,
        last_blocker_overboost_counterexample,
        multi_resource_motifs,
        random_multi_resource_instance,
        random_parallel_chains,
        random_join_dag,
        scaled_five_four_family,
        tight_optional_wait_family,
    )
    from benchmark_generate.legacy_dag import adversarial_benchmarks, llm_motif_benchmarks

    exported: list[ExportedCase] = []
    parallel_rng = random.Random(seed)
    general_rng = random.Random(seed + 1)
    multi_rng = random.Random(seed + 2)
    parallel_cases = {
        "adversarial": [
            ("tight_optional_wait_m20", tight_optional_wait_family(20)),
            ("scaled_five_four_s4", scaled_five_four_family(4)),
            ("fixed_beam_counterexample", fixed_beam_counterexample()),
        ],
        "random": [
            (f"random_chain_{index}", random_parallel_chains(parallel_rng))
            for index in range(samples)
        ],
        "real": [
            ("1f1b_chain_projection", (
                ParallelChain((2, 2, 1), (3, 2, 1), 0),
                ParallelChain((1, 2, 2), (2, 3, 1), 1),
                ParallelChain((2, 1, 2), (2, 2, 2), 2),
            )),
            ("zero_bubble_chain_projection", (
                ParallelChain((2, 1, 1), (3, 1, 2), 0),
                ParallelChain((1, 1, 2), (2, 2, 1), 1),
                ParallelChain((1, 2), (1, 3), 2),
            )),
        ],
    }
    for category, cases in parallel_cases.items():
        for name, instance in cases:
            benchmark = parallel_chains_to_benchmark(
                name, category, instance,
                metadata={"generator": "parallel_chain", "seed": seed if category == "random" else None},
            )
            exported.append(_case(benchmark, "single_channel", "parallel_chain", category))
    general_cases = {
        "adversarial": [*adversarial_benchmarks(), last_blocker_overboost_counterexample()],
        "random": [random_join_dag(general_rng, index) for index in range(samples)],
        "real": llm_motif_benchmarks(),
    }
    for category, cases in general_cases.items():
        for index, dag in enumerate(cases):
            benchmark = dag_to_benchmark(
                dag, category,
                metadata={"generator": "general_dag", "seed": seed + 1 if category == "random" else None},
            )
            if category == "random":
                benchmark = _with_id(benchmark, f"general_random_{index:03d}")
            exported.append(_case(benchmark, "single_channel", "general_dag", category))
    multi_cases = {
        "adversarial": multi_resource_motifs(),
        "random": [random_multi_resource_instance(multi_rng, index) for index in range(samples)],
    }
    for category, cases in multi_cases.items():
        for index, instance in enumerate(cases):
            benchmark = multi_resource_to_benchmark(
                instance, category,
                metadata={"generator": "multi_channel", "seed": seed + 2 if category == "random" else None},
            )
            if category == "random":
                benchmark = _with_id(benchmark, f"multi_random_{index:03d}")
            exported.append(_case(benchmark, "multi_channel", "multi_resource_dag", category))
    return exported


def export_suite(
    root: Path,
    *,
    samples: int = 10,
    seed: int = 260819,
    categories: set[str] | None = None,
) -> list[dict]:
    rows = []
    for item in current_cases(samples=samples, seed=seed):
        if categories is not None and item.benchmark.category not in categories:
            continue
        target = root / item.relative_path
        write_benchmark(item.benchmark, target)
        digest = hashlib.sha256(target.read_bytes()).hexdigest()
        rows.append({
            "id": item.benchmark.benchmark_id,
            "path": item.relative_path.as_posix(),
            "scenario": item.benchmark.scenario,
            "family": item.benchmark.family,
            "category": item.benchmark.category,
            "sha256": digest,
        })
    generated_paths = {row["path"] for row in rows}
    for target in sorted(root.rglob("*.json")):
        if "schema" in target.parts or "reference_results" in target.parts:
            continue
        relative = target.relative_to(root).as_posix()
        if relative in generated_paths:
            continue
        from dag_heuristic.benchmark import load_benchmark

        benchmark = load_benchmark(target)
        rows.append({
            "id": benchmark.benchmark_id,
            "path": relative,
            "scenario": benchmark.scenario,
            "family": benchmark.family,
            "category": benchmark.category,
            "sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
        })
    rows.sort(key=lambda row: (row["scenario"], row["family"], row["category"], row["id"]))
    (root / "index.jsonl").write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )
    return rows


def _case(benchmark: Benchmark, scenario: str, family: str, category: str) -> ExportedCase:
    return ExportedCase(benchmark, Path(scenario) / family / category / f"{benchmark.benchmark_id}.json")


def _with_id(benchmark: Benchmark, benchmark_id: str) -> Benchmark:
    from dataclasses import replace

    return replace(benchmark, benchmark_id=benchmark_id)

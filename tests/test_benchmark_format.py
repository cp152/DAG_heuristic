from __future__ import annotations

import json
from pathlib import Path

import pytest

from dag_heuristic.benchmark import BenchmarkValidationError, benchmark_from_dict, load_benchmark


ROOT = Path(__file__).resolve().parents[1]


def benchmark_files() -> list[Path]:
    return sorted(
        path
        for path in (ROOT / "benchmark").rglob("*.json")
        if "schema" not in path.parts and "reference_results" not in path.parts
    )


def test_every_committed_benchmark_loads() -> None:
    files = benchmark_files()
    assert len(files) == 57
    loaded = [load_benchmark(path) for path in files]
    assert {item.scenario for item in loaded} == {"single_channel", "multi_channel"}
    assert {item.category for item in loaded} == {"random", "adversarial", "real"}


def test_index_matches_files_and_hashes() -> None:
    import hashlib

    rows = [json.loads(line) for line in (ROOT / "benchmark/index.jsonl").read_text(encoding="utf-8").splitlines()]
    assert len(rows) == 57
    for row in rows:
        path = ROOT / "benchmark" / row["path"]
        assert path.exists()
        assert hashlib.sha256(path.read_bytes()).hexdigest() == row["sha256"]


def test_reference_results_match_problem_hashes() -> None:
    import hashlib

    references = sorted((ROOT / "benchmark/reference_results").rglob("*.json"))
    assert references
    for reference in references:
        payload = json.loads(reference.read_text(encoding="utf-8"))
        relative = reference.relative_to(ROOT / "benchmark/reference_results")
        problem = ROOT / "benchmark" / relative
        assert problem.exists()
        assert payload["benchmark_sha256"] == hashlib.sha256(problem.read_bytes()).hexdigest()


def test_cycle_is_rejected() -> None:
    payload = {
        "schema_version": "1.0",
        "id": "cycle",
        "scenario": "single_channel",
        "family": "general_dag",
        "category": "adversarial",
        "objective": "makespan",
        "time_unit": "tick",
        "semantics": {
            "preemptive": False,
            "decision_epoch": "task_completion",
            "optional_idle": True,
            "compute_model": "unbounded_parallel",
            "resource_model": "exclusive",
        },
        "resources": [{"id": "channel:0", "kind": "channel"}],
        "tasks": [
            {"id": "a", "kind": "compute", "duration": 1, "dependencies": ["b"], "resources": []},
            {"id": "b", "kind": "compute", "duration": 1, "dependencies": ["a"], "resources": []},
        ],
    }
    with pytest.raises(BenchmarkValidationError, match="cycle"):
        benchmark_from_dict(payload)

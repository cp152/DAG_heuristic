"""Load and write canonical DAG benchmark JSON files."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from benchmark.model import Benchmark, Resource, Task
from benchmark.validator import BenchmarkValidationError, validate_benchmark


def benchmark_from_dict(payload: dict[str, Any]) -> Benchmark:
    required = {
        "schema_version", "id", "scenario", "family", "category", "objective",
        "time_unit", "semantics", "resources", "tasks",
    }
    missing = required - payload.keys()
    if missing:
        raise BenchmarkValidationError(f"missing top-level fields: {sorted(missing)}")
    expected_semantics = {
        "preemptive": False,
        "decision_epoch": "task_completion",
        "optional_idle": True,
        "compute_model": "unbounded_parallel",
        "resource_model": "exclusive",
    }
    if payload["semantics"] != expected_semantics:
        raise BenchmarkValidationError("unsupported scheduling semantics")
    try:
        benchmark = Benchmark(
            benchmark_id=str(payload["id"]),
            scenario=payload["scenario"],
            family=str(payload["family"]),
            category=str(payload["category"]),
            tasks=tuple(
                Task(
                    task_id=str(task["id"]),
                    kind=task["kind"],
                    duration=int(task["duration"]),
                    dependencies=tuple(task.get("dependencies", ())),
                    resources=tuple(task.get("resources", ())),
                    metadata=dict(task.get("metadata", {})),
                )
                for task in payload["tasks"]
            ),
            resources=tuple(
                Resource(
                    resource_id=str(resource["id"]),
                    kind=str(resource["kind"]),
                    metadata=dict(resource.get("metadata", {})),
                )
                for resource in payload["resources"]
            ),
            time_unit=str(payload["time_unit"]),
            metadata=dict(payload.get("metadata", {})),
            schema_version=str(payload["schema_version"]),
            objective=str(payload["objective"]),
        )
    except (KeyError, TypeError, ValueError) as error:
        raise BenchmarkValidationError(f"invalid benchmark fields: {error}") from error
    validate_benchmark(benchmark)
    return benchmark


def benchmark_to_dict(benchmark: Benchmark) -> dict[str, Any]:
    validate_benchmark(benchmark)
    return {
        "schema_version": benchmark.schema_version,
        "id": benchmark.benchmark_id,
        "scenario": benchmark.scenario,
        "family": benchmark.family,
        "category": benchmark.category,
        "objective": benchmark.objective,
        "time_unit": benchmark.time_unit,
        "semantics": {
            "preemptive": False,
            "decision_epoch": "task_completion",
            "optional_idle": True,
            "compute_model": "unbounded_parallel",
            "resource_model": "exclusive",
        },
        "resources": [
            {"id": item.resource_id, "kind": item.kind, **({"metadata": item.metadata} if item.metadata else {})}
            for item in benchmark.resources
        ],
        "tasks": [
            {
                "id": task.task_id,
                "kind": task.kind,
                "duration": task.duration,
                "dependencies": list(task.dependencies),
                "resources": list(task.resources),
                **({"metadata": task.metadata} if task.metadata else {}),
            }
            for task in benchmark.tasks
        ],
        **({"metadata": benchmark.metadata} if benchmark.metadata else {}),
    }


def load_benchmark(path: str | Path) -> Benchmark:
    source = Path(path)
    try:
        payload = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise BenchmarkValidationError(f"cannot read {source}: {error}") from error
    if not isinstance(payload, dict):
        raise BenchmarkValidationError("benchmark root must be a JSON object")
    return benchmark_from_dict(payload)


def write_benchmark(benchmark: Benchmark, path: str | Path) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(benchmark_to_dict(benchmark), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

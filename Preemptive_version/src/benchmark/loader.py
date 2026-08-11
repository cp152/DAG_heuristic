from __future__ import annotations
"""Load and write canonical DAG benchmark JSON files."""
"""相较于原版loader，新增了将一个dag输出到控制台的部分，用于与 c++ 部分代码交流。"""
import json
from pathlib import Path
from typing import Any

try:
    from benchmark.model import Benchmark, Resource, Task
except:
    from model import Benchmark, Resource, Task
try:
    from benchmark.validator import BenchmarkValidationError, validate_benchmark
except:
    from validator import BenchmarkValidationError, validate_benchmark


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
        newline="\n",
    )

def print_dag(data: dict[str, Any]) -> None:
    """读取 dict，按规范格式打印 DAG 信息到标准输出。

    要求：
    - 检查 resources 是否仅有一种 kind，否则报错。
    - 第一行输出：任务数量 依赖总数
    - 将任务从 1 开始顺序编号（按 tasks 列表顺序）。
    - 每个任务一行：类型（c 表示计算节点，t 表示通信节点） 时长
    - 每个依赖一行：前置任务编号 后继任务编号
    """

    # 1. 检查 resources
    resources = data.get("resources", [])
    if not resources:
        raise ValueError("至少需要一个资源")
    resource_kinds = {r["kind"] for r in resources}
    if len(resource_kinds) != 1:
        raise ValueError(f"resources 种类必须唯一，当前存在: {resource_kinds}")

    # 2. 获取任务列表
    tasks = data.get("tasks", [])
    if not tasks:
        print("0 0")
        return

    # 3. 建立 原始id -> 新编号 的映射（按任务列表顺序，从1开始）
    id_to_num: dict[str, int] = {}
    for idx, task in enumerate(tasks, start=1):
        task_id = task["id"]
        if task_id in id_to_num:
            raise ValueError(f"重复的任务 id: {task_id}")
        id_to_num[task_id] = idx

    # 4. 计算依赖总数
    total_deps = sum(len(task.get("dependencies", [])) for task in tasks)

    # 5. 输出第一行
    print(f"{len(tasks)} {total_deps}")

    # 6. 输出每个任务的类型和时长
    for task in tasks:
        kind = task["kind"]
        if kind == "compute":
            type_char = "c"
        elif kind == "communication":
            type_char = "t"
        else:
            raise ValueError(f"不支持的任务类型: {kind}（仅支持 compute 和 communication）")
        duration = task["duration"]
        print(f"{type_char} {duration}")

    # 7. 输出所有依赖关系（u 必须在 v 开始前完成，即 u -> v）
    for task in tasks:
        v_num = id_to_num[task["id"]]
        for dep_id in task.get("dependencies", []):
            u_num = id_to_num[dep_id]
            print(f"{u_num} {v_num}")

# 示例调用（假设 data 已经读取）:
# if __name__ == "__main__":
#     import json
#     raw = json.loads(sys.stdin.read())
#     print_dag(raw)
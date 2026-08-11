from pathlib import Path

from dag_heuristic.benchmark import load_benchmark
from dag_heuristic.registry import solve


ROOT = Path(__file__).resolve().parents[1]


def _load(relative: str):
    return load_benchmark(ROOT / "benchmark" / relative)


def test_parallel_chain_file_reproduces_longest_tail() -> None:
    benchmark = _load("single_channel/parallel_chain/adversarial/tight_optional_wait_m20.json")
    assert solve(benchmark, "longest_tail").makespan == 41


def test_general_dag_file_reproduces_rollout() -> None:
    benchmark = _load("single_channel/general_dag/adversarial/longest_tail_counterexample.json")
    assert solve(benchmark, "rollout_wait2").makespan == 8


def test_multi_channel_file_reproduces_optional_rollout() -> None:
    benchmark = _load("multi_channel/multi_resource_dag/adversarial/nonmaximal_start_np.json")
    assert solve(benchmark, "rollout_optional2").makespan == 8

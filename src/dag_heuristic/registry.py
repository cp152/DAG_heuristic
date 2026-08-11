"""Stable algorithm registry operating on public Benchmark objects."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from dag_heuristic.benchmark import Benchmark
from dag_heuristic.core.conversion import (
    to_internal_dag,
    to_multi_resource_instance,
    to_parallel_chains,
)


@dataclass(frozen=True)
class Algorithm:
    name: str
    scenario: str
    family: str
    solve: Callable[[Benchmark], object]
    description: str
    exact: bool = False
    supports_wait: bool = False


def _parallel_registry() -> dict[str, Algorithm]:
    from dag_heuristic.algorithms.single_channel.parallel_chain import solver

    convert = to_parallel_chains
    return {
        "longest_tail": Algorithm("longest_tail", "single_channel", "parallel_chain", lambda b: solver.schedule_priority(convert(b), "dynamic_tail"), "Dynamic residual longest-tail priority."),
        "rollout_flow2": Algorithm("rollout_flow2", "single_channel", "parallel_chain", lambda b: solver.schedule_rollout(convert(b), top_k=2, allow_wait=False), "Two whole-flow rollout candidates."),
        "rollout_wait2": Algorithm("rollout_wait2", "single_channel", "parallel_chain", lambda b: solver.schedule_rollout(convert(b), top_k=2, allow_wait=True), "Two whole-flow candidates plus WAIT.", supports_wait=True),
        "beam_wait8": Algorithm("beam_wait8", "single_channel", "parallel_chain", lambda b: solver.beam_search(convert(b), width=8, allow_wait=True), "Beam width 8 with optional idle.", supports_wait=True),
        "beam_wait32": Algorithm("beam_wait32", "single_channel", "parallel_chain", lambda b: solver.beam_search(convert(b), width=32, allow_wait=True), "Beam width 32 with optional idle.", supports_wait=True),
        "exact_optional": Algorithm("exact_optional", "single_channel", "parallel_chain", lambda b: solver.exact_dp(convert(b), optional_idle=True), "Exact small-instance DP.", exact=True, supports_wait=True),
    }


def _general_registry() -> dict[str, Algorithm]:
    from dag_heuristic.algorithms.single_channel.general_dag import solver
    from dag_heuristic.core.oracle import exact_oracle

    convert = to_internal_dag
    return {
        "longest_tail": Algorithm("longest_tail", "single_channel", "general_dag", lambda b: solver.schedule_priority(convert(b)), "Dynamic residual longest-tail priority."),
        "join_bonus": Algorithm("join_bonus", "single_channel", "general_dag", lambda b: solver.schedule_priority(convert(b), "raw_join"), "Longest tail plus optimistic join bonus."),
        "rollout_flow2": Algorithm("rollout_flow2", "single_channel", "general_dag", lambda b: solver.schedule_rollout(convert(b), top_k=2, allow_wait=False), "Two whole-flow rollout candidates."),
        "rollout_wait2": Algorithm("rollout_wait2", "single_channel", "general_dag", lambda b: solver.schedule_rollout(convert(b), top_k=2, allow_wait=True), "Two whole-flow candidates plus WAIT.", supports_wait=True),
        "depth2_wait2": Algorithm("depth2_wait2", "single_channel", "general_dag", lambda b: solver.schedule_rollout(convert(b), top_k=2, allow_wait=True, candidate_mode="hybrid", depth=2), "Depth-2 hybrid rollout with WAIT.", supports_wait=True),
        "beam_wait8": Algorithm("beam_wait8", "single_channel", "general_dag", lambda b: solver.beam_search(convert(b), width=8), "Beam width 8 with optional idle.", supports_wait=True),
        "exact_optional": Algorithm("exact_optional", "single_channel", "general_dag", lambda b: exact_oracle(convert(b), mode="optional_idle"), "Exact small-instance oracle.", exact=True, supports_wait=True),
    }


def _multi_registry() -> dict[str, Algorithm]:
    from dag_heuristic.algorithms.multi_channel import solver

    convert = to_multi_resource_instance
    return {
        "longest_tail_pack": Algorithm("longest_tail_pack", "multi_channel", "multi_resource_dag", lambda b: solver.schedule_greedy(convert(b), "dynamic_tail"), "Compatible packing in longest-tail order."),
        "resource_pack": Algorithm("resource_pack", "multi_channel", "multi_resource_dag", lambda b: solver.schedule_greedy(convert(b), "resource_tail"), "Residual resource-load tie breaking."),
        "bottleneck_pack": Algorithm("bottleneck_pack", "multi_channel", "multi_resource_dag", lambda b: solver.schedule_greedy(convert(b), "bottleneck_first"), "Remaining bottleneck resource first."),
        "rollout_maximal2": Algorithm("rollout_maximal2", "multi_channel", "multi_resource_dag", lambda b: solver.schedule_rollout(convert(b), top_k=2, optional_actions=False), "Roll out maximal compatible sets."),
        "rollout_optional2": Algorithm("rollout_optional2", "multi_channel", "multi_resource_dag", lambda b: solver.schedule_rollout(convert(b), top_k=2, optional_actions=True), "Roll out optional compatible sets and WAIT.", supports_wait=True),
        "exact_optional": Algorithm("exact_optional", "multi_channel", "multi_resource_dag", lambda b: solver.exact_oracle(convert(b), mode="optional_idle"), "Exact small-instance resource oracle.", exact=True, supports_wait=True),
    }


def algorithms_for(benchmark: Benchmark) -> dict[str, Algorithm]:
    if benchmark.family == "parallel_chain":
        return _parallel_registry()
    if benchmark.family == "general_dag":
        return _general_registry()
    if benchmark.family == "multi_resource_dag":
        return _multi_registry()
    raise ValueError(f"unsupported benchmark family: {benchmark.family}")


def solve(benchmark: Benchmark, algorithm_name: str) -> object:
    algorithms = algorithms_for(benchmark)
    try:
        algorithm = algorithms[algorithm_name]
    except KeyError as error:
        raise ValueError(
            f"unknown algorithm {algorithm_name}; available: {', '.join(sorted(algorithms))}"
        ) from error
    return algorithm.solve(benchmark)

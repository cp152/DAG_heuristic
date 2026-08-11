"""Pure generators for random and adversarial benchmark scenarios."""

from __future__ import annotations

from dataclasses import replace
import random

from dag_heuristic.algorithms.single_channel.parallel_chain.solver import (
    ParallelChain,
    to_benchmark_dag,
)
from dag_heuristic.core.dag import BenchmarkDAG, _Builder
from dag_heuristic.core.resource import MultiResourceInstance


def random_parallel_chains(
    rng: random.Random,
    *,
    min_chains: int = 2,
    max_chains: int = 5,
    max_operations: int = 3,
    max_comm: int = 4,
    max_delay: int = 6,
) -> tuple[ParallelChain, ...]:
    return tuple(
        ParallelChain(
            tuple(rng.randint(1, max_comm) for _ in range(operations)),
            tuple(rng.randint(0, max_delay) for _ in range(operations)),
        )
        for operations in (
            rng.randint(1, max_operations)
            for _ in range(rng.randint(min_chains, max_chains))
        )
    )


def tight_optional_wait_family(magnitude: int) -> tuple[ParallelChain, ...]:
    return (
        ParallelChain((magnitude,), (0,)),
        ParallelChain((1,), (magnitude,), initial_delay=1),
    )


def scaled_five_four_family(scale: int) -> tuple[ParallelChain, ...]:
    return (
        ParallelChain((2 * scale, 2 * scale), (3 * scale + 1, 0)),
        ParallelChain((scale, 3 * scale), (2 * scale, 0)),
    )


def fixed_beam_counterexample() -> tuple[ParallelChain, ...]:
    return (
        ParallelChain((6,), (6,)),
        ParallelChain((8,), (1,)),
        ParallelChain((1, 6, 4, 1), (8, 12, 9, 3)),
        ParallelChain((3,), (3,)),
        ParallelChain((2, 1), (2, 9)),
        ParallelChain((2, 1, 8), (1, 7, 8)),
    )


def random_join_dag(rng: random.Random, index: int) -> BenchmarkDAG:
    builder = _Builder(
        f"random_join_{index}", "random_general",
        "Random small DAG with branch releases, second flows and a final join.",
    )
    endpoints: list[str] = []
    branches = rng.randint(2, 5)
    for branch in range(branches):
        release = builder.add(f"r{branch}", "compute", rng.randint(0, 3), role="release")
        first = builder.add(
            f"c{branch}_0", "comm", rng.randint(1, 4), (release,),
            role=rng.choice(("pp", "tp", "dp")),
        )
        compute = builder.add(
            f"x{branch}_0", "compute", rng.randint(1, 6), (first,),
            role="backbone" if branch == 0 else "side",
        )
        if rng.random() < 0.7:
            endpoints.append(builder.add(
                f"c{branch}_1", "comm", rng.randint(1, 4), (compute,),
                role=rng.choice(("pp", "dp")),
            ))
        else:
            endpoints.append(compute)
    if branches >= 3 and rng.random() < 0.6:
        nested = builder.add(
            "nested_join", "compute", rng.randint(1, 3), tuple(endpoints[:2]), role="join",
        )
        endpoints = [nested, *endpoints[2:]]
    join = builder.add(
        "optimizer_join", "compute", rng.randint(1, 3), tuple(endpoints), role="optimizer",
    )
    if rng.random() < 0.7:
        final = builder.add("final_comm", "comm", rng.randint(1, 3), (join,), role="pp")
        builder.add("sink", "compute", rng.randint(1, 4), (final,), role="sink")
    return builder.finish(branches=branches)


def last_blocker_overboost_counterexample() -> BenchmarkDAG:
    builder = _Builder(
        "last_blocker_overboost", "adversarial",
        "Directly adding join last-blocker urgency over-prioritizes a long flow.",
    )
    r0 = builder.add("r0", "compute", 3)
    c00 = builder.add("c0_0", "comm", 3, (r0,))
    x00 = builder.add("x0_0", "compute", 4, (c00,))
    c01 = builder.add("c0_1", "comm", 1, (x00,))
    r1 = builder.add("r1", "compute", 1)
    c10 = builder.add("c1_0", "comm", 3, (r1,))
    x10 = builder.add("x1_0", "compute", 1, (c10,))
    r2 = builder.add("r2", "compute", 2)
    c20 = builder.add("c2_0", "comm", 4, (r2,))
    x20 = builder.add("x2_0", "compute", 2, (c20,))
    c21 = builder.add("c2_1", "comm", 1, (x20,))
    nested = builder.add("nested_join", "compute", 2, (c01, x10), role="join")
    optimizer = builder.add("optimizer_join", "compute", 1, (nested, c21), role="optimizer")
    final = builder.add("final_comm", "comm", 1, (optimizer,))
    builder.add("sink", "compute", 4, (final,))
    return builder.finish()


def combined_chain_probes() -> list[BenchmarkDAG]:
    wanted = {14, 70, 86}
    rng = random.Random(260813)
    result = []
    for index in range(max(wanted) + 1):
        chains = random_parallel_chains(rng)
        if index in wanted:
            dag, _flow_ids = to_benchmark_dag(chains)
            result.append(replace(dag, name=f"combined_chain_{index}", category="combined_probe"))
    return result


def multi_resource_motifs() -> list[MultiResourceInstance]:
    result = []
    builder = _Builder("disjoint_routes_np", "r4_motif", "disjoint overlap")
    left = builder.add("left", "comm", 4)
    right = builder.add("right", "comm", 4)
    builder.add("left_tail", "compute", 3, (left,))
    builder.add("right_tail", "compute", 3, (right,))
    result.append(MultiResourceInstance(builder.finish(), {"left": frozenset({"r0"}), "right": frozenset({"r1"})}))

    builder = _Builder("shared_route_np", "r4_motif", "shared bottleneck")
    left = builder.add("left", "comm", 4)
    right = builder.add("right", "comm", 4)
    builder.add("left_tail", "compute", 3, (left,))
    builder.add("right_tail", "compute", 3, (right,))
    result.append(MultiResourceInstance(builder.finish(), {"left": frozenset({"shared"}), "right": frozenset({"shared"})}))

    builder = _Builder("nonmaximal_start_np", "r4_motif", "Non-maximal start protects a future critical flow.")
    release = builder.add("release_c", "compute", 1)
    builder.add("a", "comm", 4)
    builder.add("b", "comm", 5)
    c = builder.add("c", "comm", 1, (release,))
    builder.add("c_tail", "compute", 6, (c,))
    result.append(MultiResourceInstance(builder.finish(), {"a": frozenset({"r0"}), "b": frozenset({"r1"}), "c": frozenset({"r1"})}))

    builder = _Builder("active_reservation_np", "r4_motif", "An active flow keeps its route reserved.")
    builder.add("a", "comm", 4)
    b = builder.add("b", "comm", 1)
    builder.add("c", "comm", 1, (b,))
    result.append(MultiResourceInstance(builder.finish(), {"a": frozenset({"shared"}), "b": frozenset({"other"}), "c": frozenset({"shared"})}))
    return result


def random_multi_resource_instance(rng: random.Random, index: int) -> MultiResourceInstance:
    dag = random_join_dag(rng, index)
    resources = {}
    fabrics = ("pp-fabric", "dp-fabric", "tp-fabric")
    for position, task in enumerate(task for task in dag.tasks if task.kind == "comm"):
        role_index = {"pp": 0, "dp": 1, "tp": 2}.get(task.role, position % 3)
        values = {f"nic-{rng.randrange(3)}", fabrics[role_index]}
        if rng.random() < 0.35:
            values.add("shared-uplink")
        resources[task.task_id] = frozenset(values)
    return MultiResourceInstance(dag, resources)

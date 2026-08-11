"""Convert a SimAI pipeline workload into a standalone DAG benchmark."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import math
from pathlib import Path

from benchmark import Benchmark, Resource, Task as BenchmarkTask, write_benchmark
from benchmark_generate.simai.bootstrap import SIMAI_ROOT  # noqa: F401

from src.static_analysis.passes.pipeline_task_serializers import (
    BidirectionalPipelineSerializer,
    DualPipeSerializer,
    InterleavedOneFOneBSerializer,
    ZeroBubbleSerializer,
)
from src.static_analysis.passes.routing import BfsStrategy
from src.static_analysis.passes.task_serializer import ExecutionPlan, OneFOneBSerializer
from src.static_analysis.passes.topology_loader import TopologyLoader
from src.workload_format.schema import Job, ParallelismConfig, P2PWorkload
from src.workload_generator.aicb_parser import AicbHeader, AicbParser, AicbWorkItem
from src.workload_generator.builders.bidirectional_pipeline_builder import (
    BidirectionalPipelineWorkloadBuilder,
)
from src.workload_generator.builders.dualpipe_pipeline_builder import (
    DualPipePipelineWorkloadBuilder,
)
from src.workload_generator.builders.interleaved_pipeline_builder import (
    InterleavedPipelineWorkloadBuilder,
)
from src.workload_generator.builders.zero_bubble_pipeline_builder import (
    ZeroBubblePipelineWorkloadBuilder,
)
from src.workload_generator.rank_grouper import MegatronRankGrouper
from src.workload_generator.workload_builder import WorkloadBuilder


MODES = ("1f1b", "interleaved_1f1b", "zero_bubble", "bidirectional", "dualpipe")


@dataclass(frozen=True)
class BuiltWorkload:
    mode: str
    workload: P2PWorkload
    plan: ExecutionPlan
    header: AicbHeader
    job: Job


def make_job(header: AicbHeader) -> Job:
    dp = header.all_gpus // (header.tp * header.pp)
    return Job(
        job_id=0,
        name="benchmark-export",
        assigned_nodes=list(range(header.all_gpus)),
        parallelism=ParallelismConfig(tp=header.tp, dp=dp, pp=header.pp, ep=header.ep),
    )


def build_synthetic_input(
    *, pp: int = 2, tp: int = 1, dp: int = 1, ga: int = 4, layers: int = 2,
) -> tuple[AicbHeader, list[AicbWorkItem]]:
    """Create a small deterministic input for examples and integration tests."""
    header = AicbHeader(
        tp=tp,
        ep=1,
        pp=pp,
        vpp=layers,
        ga=ga,
        all_gpus=pp * tp * dp,
        pp_comm_size=1_048_576,
    )

    def item(name: str, fwd: int, bwd: int, weight: int) -> AicbWorkItem:
        return AicbWorkItem(
            name=name,
            forward_compute_time=fwd,
            forward_comm="ALLREDUCE" if tp > 1 else "NONE",
            forward_comm_size=524_288 if tp > 1 else 0,
            backward_compute_time=bwd,
            backward_comm="ALLREDUCE" if tp > 1 else "NONE",
            backward_comm_size=524_288 if tp > 1 else 0,
            dp_compute_time=weight,
            dp_comm="NONE",
            dp_comm_size=0,
            process_time=100,
        )

    grad = item("grad_param_comm", 1_000, 1_000, 1_000)
    if dp > 1:
        grad.dp_comm = "ALLREDUCE"
        grad.dp_comm_size = 2_097_152
    items = [grad]
    for _microbatch in range(ga):
        for layer in range(layers):
            items.append(item(
                f"layer{layer}",
                900_000 + layer * 100_000,
                1_500_000 + layer * 100_000,
                600_000 + layer * 50_000,
            ))
    items.append(item("optimizer1", 0, 0, 0))
    return header, items


def _stage_map(job: Job) -> dict[int, int]:
    grouper = MegatronRankGrouper(job.assigned_nodes, job.parallelism)
    width = grouper.dp * grouper.tp
    return {
        node: stage
        for stage in range(grouper.pp)
        for node in grouper.nodes[stage * width:(stage + 1) * width]
    }


def build_workload(
    mode: str,
    header: AicbHeader,
    items: list[AicbWorkItem],
    *,
    vpp: int = 2,
    gradient_sync_bytes: int = 2_097_152,
    job: Job | None = None,
) -> BuiltWorkload:
    """Build the P2P workload and add serializer-owned compute resource order."""
    if mode not in MODES:
        raise ValueError(f"unknown mode {mode}; choose one of {', '.join(MODES)}")
    job = make_job(header) if job is None else job
    sidecar: dict[int, object] = {}
    if mode == "1f1b":
        builder = WorkloadBuilder()
    elif mode == "interleaved_1f1b":
        builder = InterleavedPipelineWorkloadBuilder(vpp, sidecar)
    elif mode == "zero_bubble":
        builder = ZeroBubblePipelineWorkloadBuilder(sidecar)
    elif mode == "bidirectional":
        builder = BidirectionalPipelineWorkloadBuilder(
            sidecar, gradient_sync_bytes=gradient_sync_bytes,
        )
    else:
        builder = DualPipePipelineWorkloadBuilder(
            sidecar, gradient_sync_bytes=gradient_sync_bytes,
        )
    workload = builder.build_from_aicb(header, items, job, comm_algo="ring")
    errors = workload.validate()
    if errors:
        raise ValueError(f"invalid SimAI workload: {errors}")

    if mode == "1f1b":
        serializer = OneFOneBSerializer(pp=header.pp, node_to_stage=_stage_map(job))
    elif mode == "interleaved_1f1b":
        serializer = InterleavedOneFOneBSerializer(
            virtual_pipeline_size=vpp,
            expansion_task_info=sidecar,
        )
    elif mode == "zero_bubble":
        serializer = ZeroBubbleSerializer(expansion_task_info=sidecar)
    elif mode == "bidirectional":
        serializer = BidirectionalPipelineSerializer(expansion_task_info=sidecar)
    else:
        serializer = DualPipeSerializer(expansion_task_info=sidecar)
    plan = serializer.serialize(workload)
    validation = serializer.validate(workload, plan.compute_order)
    if validation:
        raise ValueError(f"invalid compute order: {validation}")
    return BuiltWorkload(mode, workload, plan, header, job)


def _effective_dependencies(built: BuiltWorkload) -> dict[int, set[int]]:
    dependencies = {
        task.task_id: set(task.deps)
        for task in built.workload.tasks
    }
    for order in built.plan.compute_order.values():
        for source, target in zip(order, order[1:]):
            dependencies[target].add(source)
    return dependencies


def to_benchmark(
    built: BuiltWorkload,
    benchmark_id: str,
    *,
    bandwidth_gbps: float = 200.0,
    topology_path: Path | None = None,
    include_nic_resources: bool = True,
) -> Benchmark:
    """Project a SimAI workload into the repository's non-preemptive model."""
    if bandwidth_gbps <= 0:
        raise ValueError("bandwidth_gbps must be positive")
    bytes_per_us = bandwidth_gbps * 125.0
    dependencies = _effective_dependencies(built)
    route_resources: dict[int, tuple[str, ...]] = {}
    resources: dict[str, Resource] = {}

    if topology_path is None:
        resources["channel:0"] = Resource("channel:0", "channel")
        for task in built.workload.tasks:
            if task.is_flow():
                route_resources[task.task_id] = ("channel:0",)
        scenario = "single_channel"
    else:
        topology = TopologyLoader().load(topology_path)
        routes = BfsStrategy().compute_routes(built.workload, topology)
        for task in built.workload.tasks:
            if not task.is_flow():
                continue
            path = routes.get_path(task)
            names = []
            for source, target in zip(path, path[1:]):
                name = f"link:{source}->{target}"
                names.append(name)
                resources[name] = Resource(name, "directed_link")
            if include_nic_resources:
                tx = f"nic_tx:{task.src}"
                rx = f"nic_rx:{task.dst}"
                names.extend((tx, rx))
                resources[tx] = Resource(tx, "nic_tx")
                resources[rx] = Resource(rx, "nic_rx")
            route_resources[task.task_id] = tuple(sorted(set(names)))
        scenario = "muti_channel"

    tasks = []
    for task in built.workload.tasks:
        is_compute = task.is_compute()
        duration = int(task.duration_us or 0) if is_compute else max(
            1, math.ceil(int(task.size_bytes or 0) / bytes_per_us),
        )
        metadata = {
            "phase": task.phase.value,
            "iteration": task.iteration,
            "layer_id": task.layer_id,
        }
        if is_compute:
            metadata["rank"] = task.node
        else:
            metadata.update({
                "src": task.src,
                "dst": task.dst,
                "size_bytes": task.size_bytes,
                "comm_type": task.comm_type.value,
            })
        tasks.append(BenchmarkTask(
            task_id=str(task.task_id),
            kind="compute" if is_compute else "communication",
            duration=duration,
            dependencies=tuple(str(value) for value in sorted(dependencies[task.task_id])),
            resources=() if is_compute else route_resources[task.task_id],
            metadata=metadata,
        ))
    return Benchmark(
        benchmark_id=benchmark_id,
        scenario=scenario,
        family="complex_chain",
        category="real",
        tasks=tuple(tasks),
        resources=tuple(resources[name] for name in sorted(resources)),
        time_unit="us",
        metadata={
            "source": "simai-flow-scheduler",
            "pipeline_mode": built.mode,
            "bandwidth_gbps": bandwidth_gbps,
            "topology": str(topology_path) if topology_path else None,
        },
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--aicb", type=Path, help="AICB workload; omit for a small synthetic input")
    parser.add_argument("--mode", choices=MODES, default="1f1b")
    parser.add_argument("--id", dest="benchmark_id", default="simai_pipeline")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--topology", type=Path, help="When set, emit fixed route resources")
    parser.add_argument("--bandwidth-gbps", type=float, default=200.0)
    parser.add_argument("--vpp", type=int, default=2)
    args = parser.parse_args()

    if args.aicb:
        header, items = AicbParser().parse(args.aicb)
    else:
        header, items = build_synthetic_input()
    built = build_workload(args.mode, header, items, vpp=args.vpp)
    benchmark = to_benchmark(
        built,
        args.benchmark_id,
        bandwidth_gbps=args.bandwidth_gbps,
        topology_path=args.topology,
    )
    write_benchmark(benchmark, args.output)
    print(f"wrote {benchmark.benchmark_id} with {len(benchmark.tasks)} tasks to {args.output}")


if __name__ == "__main__":
    main()

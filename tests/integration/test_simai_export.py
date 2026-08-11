from __future__ import annotations

from benchmark import validate_benchmark
from benchmark_generate.simai.bootstrap import SIMAI_ROOT
from benchmark_generate.simai.export import (
    MODES,
    build_synthetic_input,
    build_workload,
    to_benchmark,
)


def test_all_pipeline_modes_export_valid_single_channel_benchmarks() -> None:
    header, items = build_synthetic_input()
    for mode in MODES:
        built = build_workload(mode, header, items)
        case = to_benchmark(built, f"synthetic_{mode}")

        validate_benchmark(case)
        assert case.scenario == "single_channel"
        assert len(case.tasks) == len(built.workload.tasks)
        assert all(
            task.resources == ("channel:0",)
            for task in case.tasks
            if task.kind == "communication"
        )


def test_topology_export_records_fixed_route_resources() -> None:
    header, items = build_synthetic_input()
    built = build_workload("1f1b", header, items)
    topology = (
        SIMAI_ROOT
        / "inputs/topologies/AlibabaHPN_16g_8gps_DualToR_DualPlane_200Gbps_A100"
    )
    case = to_benchmark(built, "synthetic_routes", topology_path=topology)

    validate_benchmark(case)
    assert case.scenario == "muti_channel"
    assert any(resource.kind == "directed_link" for resource in case.resources)
    assert all(
        task.resources
        for task in case.tasks
        if task.kind == "communication"
    )

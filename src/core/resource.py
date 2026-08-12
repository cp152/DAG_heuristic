"""Internal fixed-resource instance used by multi-channel schedulers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Hashable

from core.dag import BenchmarkDAG


ResourceId = Hashable


@dataclass(frozen=True)
class MultiResourceInstance:
    dag: BenchmarkDAG
    resources: dict[str, frozenset[ResourceId]]

    def validate(self) -> list[str]:
        errors = self.dag.validate()
        task_map = self.dag.task_map()
        comm_ids = {task.task_id for task in self.dag.tasks if task.kind == "comm"}
        missing = comm_ids - self.resources.keys()
        extra = self.resources.keys() - comm_ids
        if missing:
            errors.append(f"communications without resources: {sorted(missing)}")
        if extra:
            errors.append(f"resources for non-communications: {sorted(extra)}")
        for task_id, values in self.resources.items():
            if task_id in task_map and not isinstance(values, frozenset):
                errors.append(f"{task_id}: resource set must be a frozenset")
            if task_id in task_map and task_map[task_id].duration <= 0:
                errors.append(f"{task_id}: communication duration must be positive")
        return errors

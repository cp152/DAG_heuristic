"""Do not collect optional integration tests when no SimAI checkout exists."""

from __future__ import annotations

import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
candidates = []
if configured := os.environ.get("SIMAI_FLOW_SCHEDULER_ROOT"):
    candidates.append(Path(configured))
candidates.extend(
    (
        ROOT / "third_party/simai-flow-scheduler",
        ROOT.parent / "simai-flow-scheduler",
    )
)

if not any((candidate / "src/workload_format/schema.py").is_file() for candidate in candidates):
    collect_ignore_glob = ["test_*.py"]

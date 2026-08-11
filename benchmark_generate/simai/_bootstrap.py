"""Locate the optional SimAI checkout without coupling the algorithm package."""

from __future__ import annotations

import os
from pathlib import Path
import sys


DAG_ROOT = Path(__file__).resolve().parents[2]


def find_simai_root() -> Path:
    candidates = []
    configured = os.environ.get("SIMAI_FLOW_SCHEDULER_ROOT")
    if configured:
        candidates.append(Path(configured))
    candidates.extend((DAG_ROOT / "third_party" / "simai-flow-scheduler", DAG_ROOT.parent))
    for candidate in candidates:
        resolved = candidate.resolve()
        if (resolved / "src/workload_format/schema.py").is_file():
            return resolved
    raise RuntimeError(
        "SimAI checkout not found. Initialize third_party/simai-flow-scheduler "
        "or set SIMAI_FLOW_SCHEDULER_ROOT."
    )


SIMAI_ROOT = find_simai_root()
if str(SIMAI_ROOT) not in sys.path:
    sys.path.insert(0, str(SIMAI_ROOT))

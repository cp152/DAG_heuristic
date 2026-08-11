from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_core_has_no_simai_or_legacy_package_imports() -> None:
    violations = []
    for path in (ROOT / "src/dag_heuristic").rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                if node.module == "src" or node.module.startswith("src.") or node.module.startswith("DAG_heuristic"):
                    violations.append(f"{path.relative_to(ROOT)}:{node.lineno}: {node.module}")
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == "src" or alias.name.startswith("src.") or alias.name.startswith("DAG_heuristic"):
                        violations.append(f"{path.relative_to(ROOT)}:{node.lineno}: {alias.name}")
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                if isinstance(node.func.value, ast.Attribute) and node.func.value.attr == "path" and node.func.attr == "insert":
                    violations.append(f"{path.relative_to(ROOT)}:{node.lineno}: sys.path.insert")
    assert violations == []

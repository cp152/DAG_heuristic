from pathlib import Path

from benchmark_generate.export_current import export_suite
from dag_heuristic.benchmark import load_benchmark


def _payloads(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob("*.json")
    }


def test_random_generation_is_seeded_and_language_neutral(tmp_path: Path) -> None:
    left = tmp_path / "left"
    right = tmp_path / "right"
    export_suite(left, samples=2, seed=7, categories={"random"})
    export_suite(right, samples=2, seed=7, categories={"random"})

    assert _payloads(left) == _payloads(right)
    files = sorted(left.rglob("*.json"))
    assert len(files) == 6
    assert all(load_benchmark(path).category == "random" for path in files)

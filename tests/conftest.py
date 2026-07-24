import subprocess
import sys
import pathlib
import yaml
import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent


@pytest.fixture
def make_hub(tmp_path):
    """把 registry dict 写成一个临时 hub 目录,返回该目录路径。"""
    def _make(registry: dict) -> pathlib.Path:
        reg_dir = tmp_path / "registry"
        reg_dir.mkdir(parents=True, exist_ok=True)
        (reg_dir / "services.yaml").write_text(
            yaml.safe_dump(registry, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )
        (tmp_path / "docs").mkdir(exist_ok=True)
        return tmp_path
    return _make


def run_check(hub_dir: pathlib.Path):
    """以子进程运行 registry-check.py,返回 CompletedProcess。"""
    return subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "registry-check.py"), str(hub_dir)],
        capture_output=True, text=True,
    )


def run_graph(hub_dir: pathlib.Path):
    return subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "registry-graph.py"), str(hub_dir)],
        capture_output=True, text=True,
    )

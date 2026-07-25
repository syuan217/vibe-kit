import subprocess
import sys

from conftest import REPO_ROOT


def test_prompts_in_sync_with_skills():
    """prompts/ 与应用仓库 prompt 副本必须由 sync-prompts.py 生成且与 skill 同源。"""
    r = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "sync-prompts.py"), "--check"],
        capture_output=True, text=True,
    )
    assert r.returncode == 0, r.stdout

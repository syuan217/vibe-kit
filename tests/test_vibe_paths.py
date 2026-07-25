import pathlib
import subprocess
import sys

from conftest import REPO_ROOT, run_paths
from test_registry_check import _valid_v3


def _git_repo_with_remote(path: pathlib.Path, remote: str) -> pathlib.Path:
    """在 path 建一个带 origin remote 的空 git 仓库(不提交)。"""
    path.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", "-q", str(path)], check=True)
    subprocess.run(["git", "-C", str(path), "remote", "add", "origin", remote], check=True)
    return path


def test_hub_dir_arg_accepted(make_hub, tmp_path):
    """`vibe-paths.py <hub目录> list` 的 hub 参数应被剥离,而不是报未知子命令。"""
    hub = make_hub(_valid_v3())
    r = run_paths(str(hub), "list")
    assert "未知子命令" not in r.stdout
    assert r.returncode == 0, r.stdout + r.stderr


def test_add_ssh_remote_matches_https_registry(make_hub, tmp_path):
    """registry 记 https、本地 origin 是 git@ ssh 形式时,归一化后应判为匹配(不 WARN)。"""
    reg = _valid_v3()
    reg["services"][0]["repo"] = "https://github.com/org/order-service"
    hub = make_hub(reg)
    repo = _git_repo_with_remote(tmp_path / "order-service", "git@github.com:org/order-service.git")
    r = run_paths(str(hub), "add", "order-service", str(repo))
    assert r.returncode == 0, r.stdout + r.stderr
    assert "不匹配" not in r.stdout
    # check 子命令同样不 WARN
    r = run_paths(str(hub), "check")
    assert r.returncode == 0, r.stdout
    assert "不匹配" not in r.stdout


def test_add_mismatched_remote_warns(make_hub, tmp_path):
    """clone 了真正不同的仓库(fork/错仓库)时仍应 WARN,但不阻止。"""
    hub = make_hub(_valid_v3())
    repo = _git_repo_with_remote(tmp_path / "order-fork", "git@github.com:someone/order-fork.git")
    r = run_paths(str(hub), "add", "order-service", str(repo))
    assert r.returncode == 0, r.stdout + r.stderr
    assert "不匹配" in r.stdout


def test_add_ssh_remote_with_port_matches_https_registry(make_hub, tmp_path):
    """自建 GitLab 的 ssh URL 常带端口,端口不应参与仓库身份比较。"""
    reg = _valid_v3()
    reg["services"][0]["repo"] = "https://git.corp.internal/org/order-service"
    hub = make_hub(reg)
    repo = _git_repo_with_remote(
        tmp_path / "order-service", "ssh://git@git.corp.internal:2222/org/order-service.git")
    r = run_paths(str(hub), "add", "order-service", str(repo))
    assert r.returncode == 0, r.stdout + r.stderr
    assert "不匹配" not in r.stdout


def test_typo_subcommand_is_not_swallowed(make_hub):
    """拼错的子命令不能被当成 hub 目录吃掉(那样会静默退出 0)。"""
    hub = make_hub(_valid_v3())
    r = run_paths(str(hub), "lst")
    assert r.returncode == 1
    assert "未知子命令: lst" in r.stdout


def test_typo_subcommand_with_arg_names_the_typo(make_hub):
    """报错要指向拼错的那个 token,而不是它后面的参数。"""
    hub = make_hub(_valid_v3())
    r = run_paths(str(hub), "resolv", "order-service")
    assert r.returncode == 1
    assert "未知子命令: resolv" in r.stdout


def test_vibe_release_hub_dir_arg_accepted():
    """`vibe-release.py <hub目录> check` 的 hub 参数应被剥离(用本仓库做只读校验)。"""
    r = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "vibe-release.py"), str(REPO_ROOT), "check"],
        capture_output=True, text=True,
    )
    assert "未知子命令" not in r.stdout
    assert "skills" in r.stdout  # 确认真正执行了 check


def test_vibe_release_typo_subcommand_is_not_swallowed():
    r = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "vibe-release.py"), "chek"],
        capture_output=True, text=True, cwd=str(REPO_ROOT),
    )
    assert r.returncode == 1
    assert "未知子命令: chek" in r.stdout

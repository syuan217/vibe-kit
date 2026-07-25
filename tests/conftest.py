import json
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


def run_paths(*args):
    """以子进程运行 vibe-paths.py,args 原样透传(可含 hub 目录参数)。"""
    return subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "vibe-paths.py"), *args],
        capture_output=True, text=True,
    )


def run_release(*args):
    """以子进程运行 vibe-release.py,args 原样透传(可含 hub 目录参数)。"""
    return subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "vibe-release.py"), *args],
        capture_output=True, text=True,
    )


@pytest.fixture
def make_kit(tmp_path):
    """造一个最小可校验的 kit 目录(registry + 五处版本 + skills),供 vibe-release check 使用。

    _make(version=..., skills={目录名: frontmatter name}, **覆盖项) 返回目录路径;
    传 zcode_skills=None 可制造缺 "skills" 字段的清单。
    """
    def _make(version="1.0.0", skills=None, plugin_name="vibe-kit",
              zcode_name=None, zcode_skills="skills"):
        skills = {"vibe-init": "vibe-init"} if skills is None else skills
        (tmp_path / "registry").mkdir(parents=True, exist_ok=True)
        (tmp_path / "registry" / "services.yaml").write_text("version: 3\n", encoding="utf-8")
        (tmp_path / "VERSION").write_text(version + "\n", encoding="utf-8")

        (tmp_path / "plugin" / ".claude-plugin").mkdir(parents=True, exist_ok=True)
        (tmp_path / "plugin" / ".claude-plugin" / "plugin.json").write_text(
            json.dumps({"name": plugin_name, "version": version}), encoding="utf-8")

        (tmp_path / "plugin" / ".zcode-plugin").mkdir(parents=True, exist_ok=True)
        zj = {"name": zcode_name or plugin_name, "version": version}
        if zcode_skills is not None:
            zj["skills"] = zcode_skills
        (tmp_path / "plugin" / ".zcode-plugin" / "plugin.json").write_text(
            json.dumps(zj), encoding="utf-8")

        (tmp_path / ".claude-plugin").mkdir(parents=True, exist_ok=True)
        roster = ", ".join(sorted(skills))
        (tmp_path / ".claude-plugin" / "marketplace.json").write_text(json.dumps({
            "version": version,
            "plugins": [{"version": version, "description": f"{len(skills)} skills: {roster}"}],
        }), encoding="utf-8")

        for dirname, fm_name in skills.items():
            d = tmp_path / "plugin" / "skills" / dirname
            d.mkdir(parents=True, exist_ok=True)
            body = "" if fm_name is None else f"---\nname: {fm_name}\ndescription: d\n---\n\n# {dirname}\n"
            (d / "SKILL.md").write_text(body or "无 frontmatter\n", encoding="utf-8")
        return tmp_path
    return _make

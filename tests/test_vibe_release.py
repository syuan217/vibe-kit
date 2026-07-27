"""vibe-release.py check —— 它是 plugin-release CI 的唯一校验入口,规则必须有测试兜底。"""
import json

from conftest import run_release


def test_valid_kit_passes(make_kit):
    r = run_release(str(make_kit()), "check")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "0 错误" in r.stdout


def test_version_drift_detected(make_kit):
    kit = make_kit()
    mp = kit / ".claude-plugin" / "marketplace.json"
    data = json.loads(mp.read_text(encoding="utf-8"))
    data["plugins"][0]["version"] = "9.9.9"  # 七处之一漂移
    mp.write_text(json.dumps(data), encoding="utf-8")
    r = run_release(str(kit), "check")
    assert r.returncode == 1
    assert "应七处相同" in r.stdout


def test_plugin_name_must_be_kebab_case(make_kit):
    r = run_release(str(make_kit(plugin_name="Vibe_Kit")), "check")
    assert r.returncode == 1
    assert "kebab-case" in r.stdout


def test_zcode_name_must_match_claude(make_kit):
    r = run_release(str(make_kit(zcode_name="something-else")), "check")
    assert r.returncode == 1
    assert "name 不一致" in r.stdout


def test_zcode_must_declare_skills_dir(make_kit):
    """zcode 靠 "skills": "skills" 发现 skills 目录,缺了插件装上也没有 skill。"""
    r = run_release(str(make_kit(zcode_skills=None)), "check")
    assert r.returncode == 1
    assert "skills" in r.stdout


def test_kimi_name_must_match_claude(make_kit):
    r = run_release(str(make_kit(kimi_name="something-else")), "check")
    assert r.returncode == 1
    assert "name 不一致" in r.stdout


def test_kimi_must_declare_skills_dir(make_kit):
    """kimi 靠 "skills" 字段发现 skills 目录(plugin 内 ./skills/,仓库根 ./plugin/skills/)。"""
    r = run_release(str(make_kit(kimi_skills=None)), "check")
    assert r.returncode == 1
    assert "skills" in r.stdout
    r = run_release(str(make_kit(root_kimi_skills=None)), "check")
    assert r.returncode == 1
    assert "skills" in r.stdout


def test_skill_missing_frontmatter(make_kit):
    r = run_release(str(make_kit(skills={"vibe-init": None})), "check")
    assert r.returncode == 1
    assert "frontmatter" in r.stdout


def test_skill_frontmatter_name_must_match_dir(make_kit):
    """目录名是调用方看到的 skill id,与 frontmatter name 不一致会导致调用不到。"""
    r = run_release(str(make_kit(skills={"vibe-init": "vibe-innit"})), "check")
    assert r.returncode == 1
    assert "与目录名不一致" in r.stdout


def test_skill_roster_drift_detected(make_kit):
    """marketplace description 的名册漏了一个 skill 时应报错。"""
    kit = make_kit(skills={"vibe-init": "vibe-init", "sync-docs": "sync-docs"})
    mp = kit / ".claude-plugin" / "marketplace.json"
    data = json.loads(mp.read_text(encoding="utf-8"))
    data["plugins"][0]["description"] = "1 skills: vibe-init"
    mp.write_text(json.dumps(data), encoding="utf-8")
    r = run_release(str(kit), "check")
    assert r.returncode == 1
    assert "skills" in r.stdout

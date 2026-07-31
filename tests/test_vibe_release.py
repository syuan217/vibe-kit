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


# --- AGENTS.md 的 skill 名册与数量(它是 AI 的上下文入口,名单错会让 AI 以为某 skill 不存在)---

AGENTS_LINE = "- `plugin/skills/<name>/SKILL.md` — {n} 个 skills:{roster};每个 skill 就是一个 SKILL.md\n"


def _write_agents_md(kit, n, roster):
    (kit / "AGENTS.md").write_text(AGENTS_LINE.format(n=n, roster=roster), encoding="utf-8")


def test_agents_md_roster_matching_passes(make_kit):
    """名册与实际一致(含括注、顺序不同)时不报错。"""
    kit = make_kit(skills={"vibe-init": "vibe-init", "sync-docs": "sync-docs"})
    _write_agents_md(kit, 2, "sync-docs(日常)、vibe-init")
    r = run_release(str(kit), "check")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "0 错误" in r.stdout


def test_agents_md_roster_drift_detected(make_kit):
    """AGENTS.md 名册漏了一个 skill 时应报错(名册不能被 bump 自动修,所以是 error 不是 warning)。"""
    kit = make_kit(skills={"vibe-init": "vibe-init", "sync-docs": "sync-docs"})
    _write_agents_md(kit, 2, "vibe-init")
    r = run_release(str(kit), "check")
    assert r.returncode == 1
    assert "AGENTS.md 的 skill 名册与实际不符" in r.stdout
    assert "缺 ['sync-docs']" in r.stdout


def test_agents_md_skill_count_drift_warned(make_kit):
    """AGENTS.md 数字不对只报 warning —— bump 的 fix_skill_count_in_docs 会自动修。"""
    kit = make_kit(skills={"vibe-init": "vibe-init", "sync-docs": "sync-docs"})
    _write_agents_md(kit, 7, "sync-docs、vibe-init")
    r = run_release(str(kit), "check")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "AGENTS.md: 出现「7 个 skills」但实际 2 个 skill" in r.stdout


def test_agents_md_without_roster_line_is_ok(make_kit):
    """AGENTS.md 没写名册行时不校验(只有写了才守)。"""
    kit = make_kit()
    (kit / "AGENTS.md").write_text("# 无名册行\n", encoding="utf-8")
    r = run_release(str(kit), "check")
    assert r.returncode == 0, r.stdout + r.stderr

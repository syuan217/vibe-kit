#!/usr/bin/env python3
"""发版助手:校验版本漂移 + 半自动 bump。

用法:
  python3 scripts/vibe-release.py check              # 只读校验,报告漂移
  python3 scripts/vibe-release.py bump <new-version>  # 改版本号+修描述+起草 CHANGELOG+重打包
  python3 scripts/vibe-release.py bump <v> --yes      # 跳过确认提示

bump 起草 CHANGELOG 时会调起 $EDITOR(默认 vi)让你校对,类似 `git commit` 无 -m。
退出码: 0 通过(允许 WARN);1 存在 ERROR。
"""
from __future__ import annotations

import json
import os
import pathlib
import re
import subprocess
import sys
from datetime import date


def find_hub() -> pathlib.Path:
    """脚本可随插件分发,定位 hub(含 registry/services.yaml)。"""
    candidates: list[pathlib.Path] = []
    # 命令行第一个非 flag 参数若不是子命令且是目录,则视为 hub 目录
    if len(sys.argv) > 1 and not sys.argv[1].startswith("-") and sys.argv[1] not in {"check", "bump"}:
        candidates.append(pathlib.Path(sys.argv[1]))
    if os.environ.get("VIBE_HUB"):
        candidates.append(pathlib.Path(os.environ["VIBE_HUB"]))
    candidates.append(pathlib.Path.cwd())
    candidates.append(pathlib.Path(__file__).resolve().parent.parent)
    for c in candidates:
        if (c / "registry" / "services.yaml").is_file():
            return c.resolve()
    sys.exit(
        "未找到 hub(缺少 registry/services.yaml)。\n"
        "用法: vibe-release.py [hub目录] <check|bump>,或设 $VIBE_HUB,或在 hub 根目录运行。"
    )


ROOT = find_hub()
PLUGIN_JSON = ROOT / "plugin" / ".claude-plugin" / "plugin.json"
MARKETPLACE_JSON = ROOT / ".claude-plugin" / "marketplace.json"
VERSION_FILE = ROOT / "VERSION"
CHANGELOG = ROOT / "CHANGELOG.md"
PLUGIN_README = ROOT / "plugin" / "README.md"
USAGE = ROOT / "plugin" / "USAGE.md"
README = ROOT / "README.md"
SKILLS_DIR = ROOT / "plugin" / "skills"

# 语义化版本正则
SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")
# 「N 个 skills」中英变体(数字部分单独 group 便于替换)
SKILL_COUNT_PATTERNS = [
    re.compile(r"(\d+)\s*个\s*skills\b"),
    re.compile(r"(\d+)\s*skills\b"),
]


def read_json(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def actual_skill_ids() -> list[str]:
    """扫 plugin/skills/ 下的目录名(已按字母序)。"""
    if not SKILLS_DIR.is_dir():
        return []
    return sorted(
        d.name for d in SKILLS_DIR.iterdir()
        if d.is_dir() and (d / "SKILL.md").is_file()
    )


def parse_marketplace_skill_description(desc: str) -> tuple[int | None, list[str] | None]:
    """从 marketplace.json 的 plugins[0].description 解析「N skills: a, b, c」格式。

    返回 (数字, skill 名册);解析不到返回 (None, None)。
    """
    m = re.search(r"(\d+)\s*skills?\s*:\s*(.+?)(?:\"\s*$|$)", desc)
    if not m:
        return None, None
    count = int(m.group(1))
    # 从冒号后的部分提取 skill 名:逗号或括号分割,取 token
    roster_part = m.group(2)
    # 去掉括注 (onboard repo) 等,按逗号切
    cleaned = re.sub(r"\([^)]*\)", "", roster_part)
    names = [t.strip().strip("`").strip() for t in cleaned.split(",") if t.strip()]
    return count, names


# ----------------------------- check 模式 -----------------------------

def cmd_check() -> int:
    errors: list[str] = []
    warnings: list[str] = []

    # 1. 版本号四处一致性
    try:
        plugin_v = read_json(PLUGIN_JSON)["version"]
    except (OSError, KeyError, json.JSONDecodeError) as e:
        print(f"ERROR: 读 {PLUGIN_JSON.relative_to(ROOT)} 失败: {e}")
        return 1
    try:
        mp = read_json(MARKETPLACE_JSON)
    except (OSError, json.JSONDecodeError) as e:
        print(f"ERROR: 读 {MARKETPLACE_JSON.relative_to(ROOT)} 失败: {e}")
        return 1
    version_file_v = VERSION_FILE.read_text(encoding="utf-8").strip() if VERSION_FILE.is_file() else None

    versions = {
        "VERSION": version_file_v,
        "plugin.json": plugin_v,
        "marketplace.json (top)": mp.get("version"),
        "marketplace.json (plugins[0])": mp.get("plugins", [{}])[0].get("version") if mp.get("plugins") else None,
    }
    for k, v in versions.items():
        if v is None:
            errors.append(f"{k} 版本号缺失")
        elif not SEMVER_RE.match(str(v)):
            errors.append(f"{k} 版本号格式不合规: {v}(需 X.Y.Z)")
    unique = {v for v in versions.values() if v}
    if len(unique) > 1:
        errors.append(f"版本号不一致: {versions}(应四处相同)")

    # 2. skill 数量/名册
    actual = actual_skill_ids()
    actual_set = set(actual)

    # marketplace.json 的 description
    desc = mp.get("plugins", [{}])[0].get("description", "") if mp.get("plugins") else ""
    desc_count, desc_names = parse_marketplace_skill_description(desc)
    if desc_count is not None and desc_count != len(actual):
        errors.append(
            f"marketplace.json description 写「{desc_count} skills」但实际 {len(actual)} 个"
            f"(实际: {', '.join(actual)})"
        )
    if desc_names is not None and set(desc_names) != actual_set:
        missing = actual_set - set(desc_names)
        extra = set(desc_names) - actual_set
        detail = []
        if missing:
            detail.append(f"缺 {sorted(missing)}")
        if extra:
            detail.append(f"多 {sorted(extra)}")
        errors.append(f"marketplace.json description 的 skill 名册与实际不符({'; '.join(detail)})")

    # README / USAGE / plugin/README 里的「N 个 skills」「N skills」
    for path in (README, PLUGIN_README, USAGE):
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        for pat in SKILL_COUNT_PATTERNS:
            for m in pat.finditer(text):
                n = int(m.group(1))
                if n != len(actual):
                    rel = path.relative_to(ROOT)
                    warnings.append(
                        f"{rel}: 出现「{m.group(0)}」但实际 {len(actual)} 个 skill"
                    )

    # 3. CHANGELOG 完整性
    if not CHANGELOG.is_file():
        warnings.append("CHANGELOG.md 不存在(发版前用 `vibe-release.py bump` 建立)")
    else:
        cl = CHANGELOG.read_text(encoding="utf-8")
        # 取 CHANGELOG 里最新的已发布版本(第一个 ## [X.Y.Z] - date)
        m = re.search(r"^##\s*\[(\d+\.\d+\.\d+)\]", cl, re.MULTILINE)
        if m and plugin_v and m.group(1) != plugin_v:
            warnings.append(
                f"CHANGELOG 最新版本是 {m.group(1)} 但 plugin.json 是 {plugin_v}"
                f"(bump 时未更新 CHANGELOG?)"
            )

    # 输出
    for w in warnings:
        print(f"WARN:  {w}")
    for e in errors:
        print(f"ERROR: {e}")
    summary = f"{len(actual)} skills, 版本 {plugin_v or '?'}, {len(errors)} 错误, {len(warnings)} 警告"
    print(f"\n{summary}")
    return 1 if errors else 0


# ----------------------------- bump 模式 -----------------------------

def update_version_files(new_v: str) -> list[str]:
    """改 4 处版本号。返回改动文件相对 ROOT 的列表。"""
    changed: list[str] = []

    # VERSION
    VERSION_FILE.write_text(new_v + "\n", encoding="utf-8")
    changed.append("VERSION")

    # plugin.json
    pj = read_json(PLUGIN_JSON)
    pj["version"] = new_v
    PLUGIN_JSON.write_text(json.dumps(pj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    changed.append(str(PLUGIN_JSON.relative_to(ROOT)))

    # marketplace.json(两处)
    mp = read_json(MARKETPLACE_JSON)
    mp["version"] = new_v
    if mp.get("plugins"):
        mp["plugins"][0]["version"] = new_v
    MARKETPLACE_JSON.write_text(json.dumps(mp, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    changed.append(str(MARKETPLACE_JSON.relative_to(ROOT)))

    return changed


def rewrite_marketplace_skill_description(actual: list[str]) -> bool:
    """根据 plugin/skills/ 重写 marketplace.json plugins[0].description 的「N skills: ...」。

    保留冒号前的描述风格,只更新数字和名册。返回是否改动。
    """
    mp = read_json(MARKETPLACE_JSON)
    if not mp.get("plugins"):
        return False
    desc = mp["plugins"][0].get("description", "")
    # 匹配「<前缀> N skills: <名册>」,前缀部分保留
    m = re.search(r"^(.*?)(\d+)\s*skills?\s*:\s*(.+)$", desc)
    if not m:
        return False
    prefix = m.group(1)
    # 名册用「<skill-id> (<简短角色>)」风格——这里从原 desc 抽每个 skill 的角色注解保育
    # 简化策略:新名册只列 skill-id,去掉旧角色注解(后者容易漂移,本来就不该在这里)
    new_roster = ", ".join(actual)
    new_desc = f"{prefix}{len(actual)} skills: {new_roster}"
    if new_desc == desc:
        return False
    mp["plugins"][0]["description"] = new_desc
    MARKETPLACE_JSON.write_text(json.dumps(mp, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return True


def fix_skill_count_in_docs(actual_n: int) -> list[str]:
    """修正 README / plugin/README / USAGE 里「N 个 skills」「N skills」的数字。返回改动文件列表。"""
    changed: list[str] = []
    for path in (README, PLUGIN_README, USAGE):
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        # 中文形式「N 个 skills」整体保留「个」,只换数字
        new_text = re.sub(r"\d+(\s*个\s*skills\b)", lambda m: f"{actual_n}{m.group(1)}", text)
        # 英文形式「N skills」(前面不是「个」)只换数字
        new_text = re.sub(r"(?<!个)\b\d+(\s+skills\b)", lambda m: f"{actual_n}{m.group(1)}", new_text)
        if new_text != text:
            path.write_text(new_text, encoding="utf-8")
            changed.append(str(path.relative_to(ROOT)))
    return changed


def collect_git_log_since_last_tag() -> str:
    """从上个 tag 到 HEAD 的 git log --oneline。无 tag 则取全部。"""
    try:
        # 找最近 tag
        r = subprocess.run(
            ["git", "-C", str(ROOT), "describe", "--tags", "--abbrev=0"],
            capture_output=True, text=True, timeout=5,
        )
        if r.returncode == 0:
            last_tag = r.stdout.strip()
            r = subprocess.run(
                ["git", "-C", str(ROOT), "log", "--oneline", f"{last_tag}..HEAD"],
                capture_output=True, text=True, timeout=10,
            )
        else:
            r = subprocess.run(
                ["git", "-C", str(ROOT), "log", "--oneline"],
                capture_output=True, text=True, timeout=10,
            )
        return r.stdout.strip()
    except (subprocess.SubprocessError, OSError) as e:
        return f"(git log 失败: {e})"


def draft_changelog_entry(new_v: str, git_log: str) -> str:
    """起草新版本的 CHANGELOG 条目(草稿,待用户校对)。"""
    today = date.today().isoformat()
    lines = [f"## [{new_v}] - {today}", "", "> 草稿,请校对/润色后保存。git log 如下,按需归类到 Added/Changed/Fixed:", ""]
    # 把 git log 贴进去做参考(用引用块,提示用户改完删除)
    for ln in git_log.splitlines():
        if ln.strip():
            lines.append(f"> {ln}")
    lines.append("")
    lines.append("### Added")
    lines.append("")
    lines.append("### Changed")
    lines.append("")
    lines.append("### Fixed")
    lines.append("")
    return "\n".join(lines)


def update_changelog(new_v: str, git_log: str) -> bool:
    """更新 CHANGELOG.md。

    策略:
    - 若 [Unreleased] 段有实质内容 → 把它整段「剪切」到新版本标题 [new_v] - today 下,Unreleased 留空标题
    - 若 [Unreleased] 段为空 → 起草新版本草稿(含 git log 引用),调起编辑器校对
    """
    if not CHANGELOG.is_file():
        print("ERROR: CHANGELOG.md 不存在,先手动建立(参考 keepachangelog 格式)")
        return False

    text = CHANGELOG.read_text(encoding="utf-8")
    today = date.today().isoformat()

    # 已有同版本条目,不重复加
    if re.search(rf"^##\s*\[{re.escape(new_v)}\]", text, re.MULTILINE):
        print(f"CHANGELOG 已有 [{new_v}] 条目,跳过(请人工核对内容)")
        return False

    # 按行切,定位 [Unreleased] 标题行与下一个 ## 标题行
    lines = text.splitlines(keepends=True)
    ur_title_idx = None
    next_section_idx = None
    for i, ln in enumerate(lines):
        stripped = ln.strip()
        if stripped.startswith("## ") and "[Unreleased]" in stripped:
            ur_title_idx = i
        elif ur_title_idx is not None and stripped.startswith("## ") and "[Unreleased]" not in stripped:
            next_section_idx = i
            break
    if ur_title_idx is None:
        # 没有 Unreleased 段,追加到末尾
        print("WARN:  CHANGELOG 无 [Unreleased] 段,起草新条目追加到头部")
        draft = draft_changelog_entry(new_v, git_log)
        new_text = text.rstrip() + "\n\n## [Unreleased]\n\n" + draft
        CHANGELOG.write_text(new_text, encoding="utf-8")
        open_in_editor(CHANGELOG)
        return True

    if next_section_idx is None:
        next_section_idx = len(lines)

    # Unreleased 段内容 = ur_title_idx+1 .. next_section_idx-1
    unreleased_body = "".join(lines[ur_title_idx + 1:next_section_idx]).strip()

    if unreleased_body:
        # 有内容:剪切到新版本块,Unreleased 只留标题 + 空行
        new_section = f"## [{new_v}] - {today}\n\n{unreleased_body}\n"
        # 重组:原文件头 + Unreleased 标题 + 空行 + 新版本块 + 后续内容
        head = lines[:ur_title_idx + 1]              # 含 Unreleased 标题行
        tail = lines[next_section_idx:]              # 从下一个 ## 开始
        # Unreleased 标题后留一个空行
        new_lines = head + ["\n", new_section + "\n"] + tail
        CHANGELOG.write_text("".join(new_lines), encoding="utf-8")
        print(f"✓ 已把 [Unreleased] 内容降为 [{new_v}] - {today}(请人工核对)")
    else:
        # Unreleased 为空:起草草稿,调起编辑器
        draft = draft_changelog_entry(new_v, git_log)
        head = lines[:ur_title_idx + 1]              # 含 Unreleased 标题行
        tail = lines[next_section_idx:]
        new_lines = head + ["\n", draft + "\n"] + tail
        CHANGELOG.write_text("".join(new_lines), encoding="utf-8")
        open_in_editor(CHANGELOG)

    return True


def open_in_editor(path: pathlib.Path) -> None:
    """调起 $EDITOR 打开文件,类似 git commit 无 -m。失败则提示手动改。"""
    editor = os.environ.get("EDITOR", "vi")
    print(f"\n请在编辑器({editor})里校对 {path.relative_to(ROOT)} 的草稿...")
    try:
        subprocess.run([editor, str(path)], check=True)
    except (subprocess.SubprocessError, OSError) as e:
        print(f"WARN:  无法调起 {editor}({e}),请手动编辑 {path}")
    except KeyboardInterrupt:
        print("(编辑器中断,文件草稿已写入,请手动校对)")


def repackage_plugin() -> bool:
    """重打包 vibe-kit.plugin。返回是否成功。"""
    try:
        r = subprocess.run(
            ["zip", "-r", "../vibe-kit.plugin", ".", "-x", "*.DS_Store"],
            cwd=str(PLUGIN_JSON.parent.parent),  # plugin/ 目录
            capture_output=True, text=True, timeout=30,
        )
        return r.returncode == 0
    except (subprocess.SubprocessError, OSError) as e:
        print(f"ERROR: 重打包失败: {e}")
        return False


def cmd_bump(args: list[str]) -> int:
    if not args or args[0].startswith("-"):
        print("用法: vibe-release.py bump <new-version> [--yes]")
        return 1
    new_v = args[0]
    auto_yes = "--yes" in args[1:]

    if not SEMVER_RE.match(new_v):
        print(f"ERROR: 版本号 {new_v} 不合规(需 X.Y.Z)")
        return 1

    # 先 check 一下当前状态,作为 bump 的前置报告
    print("=" * 60)
    print(f"准备 bump 到 {new_v}")
    print("=" * 60)
    actual = actual_skill_ids()
    cur_v = read_json(PLUGIN_JSON).get("version", "?")
    print(f"当前版本: {cur_v}")
    print(f"实际 skills({len(actual)}): {', '.join(actual)}")
    print("")

    if not auto_yes:
        print("将执行:1) 改 4 处版本号  2) 修 skill 数量/名册描述  3) 起草/更新 CHANGELOG(调起编辑器)  4) 重打包 .plugin")
        ans = input("继续?[y/N] ").strip().lower()
        if ans != "y":
            print("已取消")
            return 1

    # 1. 版本号
    changed = update_version_files(new_v)
    print(f"✓ 版本号已改: {', '.join(changed)}")

    # 2. skill 名册描述(marketplace.json) + 文档里的数字
    if rewrite_marketplace_skill_description(actual):
        print(f"✓ marketplace.json description 的 skill 名册已同步({len(actual)} 个)")
    if fix_skill_count_in_docs(len(actual)):
        print(f"✓ 文档里的 skill 数量已同步")
    else:
        print(f"i 文档里无 skill 数量需修正")

    # 3. CHANGELOG
    git_log = collect_git_log_since_last_tag()
    update_changelog(new_v, git_log)
    print(f"✓ CHANGELOG.md 已更新(请人工校对)")

    # 4. 重打包
    if repackage_plugin():
        print("✓ vibe-kit.plugin 已重打包")
    else:
        print("ERROR: .plugin 重打包失败,请手动 `cd plugin && zip -r ../vibe-kit.plugin . -x '*.DS_Store'`")

    # 5. 打印发版 checklist(剩余手动步骤)
    print("")
    print("=" * 60)
    print("发版 checklist(剩余手动步骤)")
    print("=" * 60)
    print(f"""
1. 校对 CHANGELOG.md(日期、分类、措辞)
2. 跑最终校验:  python3 scripts/vibe-release.py check
3. 提交(含 CHANGELOG):
   git add -A
   git commit -m "feat(vibe-kit): <本次主要改动一句话> (v{new_v})"
4. 推送 + 打 tag(CI 自动发 Release):
   git push && git tag v{new_v} && git push --tags
""")
    return 0


def main() -> int:
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return 0
    cmd = args[0]
    rest = args[1:]
    if cmd == "check":
        return cmd_check()
    if cmd == "bump":
        return cmd_bump(rest)
    print(f"未知子命令: {cmd}(可用: check / bump)")
    return 1


if __name__ == "__main__":
    sys.exit(main())

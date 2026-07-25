#!/usr/bin/env python3
"""从 plugin/skills/<name>/SKILL.md 生成同源 prompt 副本,防止手工同步漂移。

唯一源是 SKILL.md(去 frontmatter 后的正文);副本 = 标题 + 「> 用法」行 + 正文。
正文必须保持渠道中立(只写执行时看得到的路径,不写插件内部路径)。

生成目标:
- prompts/<name>.md                       —— SYNCED 中全部 6 个
- plugin/templates/app/prompts/<name>.md  —— 其中日常类 3 个(APP_COPIES),与 prompts/ 完全一致

用法:
  python3 scripts/sync-prompts.py --write   # 重新生成全部副本
  python3 scripts/sync-prompts.py --check   # 只校验(CI 用),有漂移退出码 1
退出码: 0 一致/写入成功;1 存在漂移或用法错误。
"""
from __future__ import annotations

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent

# name -> prompt 副本中标题下插入的「> 用法」行(唯一的渠道差异)
SYNCED = {
    "cross-app-spec": "> 用法:在 **hub 仓库**中对任意 AI 工具说\"按 prompts/cross-app-spec.md 建总 spec:<需求描述>\"。",
    "finalize-feature": "> 用法:`/speckit.implement` 完成、合 PR 前,对任意 AI 工具说\"按 prompts/finalize-feature.md 收尾 specs/NNN-xxx\"。",
    "rebuild-wiki": "> 用法:对任意 AI 工具说\"按 prompts/rebuild-wiki.md 执行\"。首次生成或目录结构大改后重建;日常增量维护走 finalize-feature / sync-docs。",
    "registry-sync": "> 用法:在**应用仓库**中对任意 AI 工具说\"按 hub 的 prompts/registry-sync.md 校准依赖\"。",
    "sync-docs": "> 用法:对任意 AI 编码工具说\"按 prompts/sync-docs.md 执行\"(可附 commit 区间或 PR 号限定范围)。",
    "vibe-init-docs": "> 用法:对任意 AI 编码工具说\"按 prompts/vibe-init-docs.md 执行\"。",
}

# 应用仓库放副本的日常类 prompt(与 prompts/ 完全一致;vibe-init 随模板拷入应用仓库)
APP_COPIES = ("finalize-feature", "rebuild-wiki", "sync-docs")

NOTICE = "> (本文件由 `scripts/sync-prompts.py` 从 `plugin/skills/{name}/SKILL.md` 生成,勿手改)"


def skill_body(name: str) -> str:
    """读 SKILL.md,去掉 YAML frontmatter,返回正文。"""
    path = ROOT / "plugin" / "skills" / name / "SKILL.md"
    text = path.read_text(encoding="utf-8")
    m = re.match(r"\A---\n.*?\n---\n+", text, re.S)
    if not m:
        sys.exit(f"ERROR: {path} 缺少 frontmatter")
    return text[m.end():].lstrip("\n")


def render_prompt(name: str) -> str:
    """由 skill 正文渲染 prompt 副本:标题 + 用法行 + 生成提示 + 正文其余部分。"""
    body = skill_body(name)
    title, _, rest = body.partition("\n")
    return f"{title}\n\n{SYNCED[name]}\n{NOTICE.format(name=name)}\n{rest}"


def targets(name: str) -> list[pathlib.Path]:
    paths = [ROOT / "prompts" / f"{name}.md"]
    if name in APP_COPIES:
        paths.append(ROOT / "plugin" / "templates" / "app" / "prompts" / f"{name}.md")
    return paths


def cmd_write() -> int:
    for name in SYNCED:
        content = render_prompt(name)
        for path in targets(name):
            path.write_text(content, encoding="utf-8")
            print(f"已生成 {path.relative_to(ROOT)}")
    return 0


def cmd_check() -> int:
    drift: list[str] = []
    for name in SYNCED:
        expected = render_prompt(name)
        for path in targets(name):
            if not path.is_file() or path.read_text(encoding="utf-8") != expected:
                drift.append(str(path.relative_to(ROOT)))
    if drift:
        print("ERROR: 以下 prompt 副本与 skill 不同源(改 SKILL.md 后运行 sync-prompts.py --write):")
        for d in drift:
            print(f"  - {d}")
        return 1
    print(f"OK: {len(SYNCED)} 个 skill 的 prompt 副本全部同源")
    return 0


def main() -> int:
    args = sys.argv[1:]
    if args == ["--write"]:
        return cmd_write()
    if args == ["--check"]:
        return cmd_check()
    print(__doc__)
    return 0 if not args else 1


if __name__ == "__main__":
    sys.exit(main())

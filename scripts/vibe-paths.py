#!/usr/bin/env python3
"""管理服务仓库的本地路径映射,让 AI 从 hub registry 的 service-id 直达本机代码目录。

用法:
  python3 scripts/vibe-paths.py list                   # 列出所有映射与失真
  python3 scripts/vibe-paths.py add <sid> <path>       # 添加映射(校验 git remote)
  python3 scripts/vibe-paths.py check                  # 仅校验,有问题返回 1
  python3 scripts/vibe-paths.py resolve <sid>          # 输出某服务的本地绝对路径(供管道)

映射文件 .vibe-paths.local.yaml 在 hub 根目录,不进版本控制(个人配置)。
退出码: 0 通过(允许 WARN);1 存在 ERROR 或未解析。
"""
from __future__ import annotations

import os
import pathlib
import subprocess
import sys

try:
    import yaml
except ImportError:
    sys.exit("缺少依赖 PyYAML,请先安装: pip install pyyaml")


def find_hub() -> pathlib.Path:
    """定位 hub(含 registry/services.yaml)。脚本可随插件分发,故不依赖自身位置。

    优先级: 命令行参数 > $VIBE_HUB > 当前目录 > 脚本上级目录(合一/hub 内运行的回退)。
    """
    candidates = []
    if len(sys.argv) > 1 and not sys.argv[1].startswith("-") and sys.argv[1] not in {"list", "add", "check", "resolve"}:
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
        "用法: vibe-paths.py [hub目录] <子命令>,或设 $VIBE_HUB,或在 hub 根目录运行。"
    )


ROOT = find_hub()
PATHS_FILE = ROOT / ".vibe-paths.local.yaml"
HEADER = """\
# 服务仓库本地路径映射(个人配置,不进版本控制)。
# 由 scripts/vibe-paths.py 维护,或参考 docs/local-paths.md 手工编辑。
# key = service-id(必须与 registry/services.yaml 的 id 一致)
# value = 该服务在本机的 clone 绝对路径
paths:
{}
"""


def load_registry_repos() -> dict[str, str]:
    """从 registry/services.yaml 读 {service-id: repo-url}。"""
    try:
        reg = yaml.safe_load((ROOT / "registry" / "services.yaml").read_text(encoding="utf-8"))
    except yaml.YAMLError as e:
        print(f"ERROR: registry yaml 解析失败: {e}")
        sys.exit(1)
    reg = reg or {}
    return {s["id"]: s.get("repo", "") for s in (reg.get("services") or []) if s.get("id")}


def load_local_paths() -> dict[str, str]:
    """读 .vibe-paths.local.yaml 的 {service-id: 本地路径}。文件不存在视为空。"""
    if not PATHS_FILE.is_file():
        return {}
    try:
        data = yaml.safe_load(PATHS_FILE.read_text(encoding="utf-8"))
    except yaml.YAMLError as e:
        print(f"ERROR: {PATHS_FILE.name} 解析失败: {e}")
        sys.exit(1)
    return (data or {}).get("paths") or {}


def get_remote_url(repo_path: pathlib.Path) -> str | None:
    """读本地仓库的 origin remote URL;失败返回 None。"""
    try:
        r = subprocess.run(
            ["git", "-C", str(repo_path), "remote", "get-url", "origin"],
            capture_output=True, text=True, timeout=5,
        )
        return r.stdout.strip() if r.returncode == 0 else None
    except (subprocess.SubprocessError, OSError):
        return None


def save_local_paths(paths: dict[str, str]) -> None:
    """落盘(带文件头注释)。保留 key 插入顺序。"""
    body = "\n".join(f"  {k}: {v}" for k, v in paths.items()) or ""
    # 空映射时占位注释,避免空 list 被 yaml 当成 null
    if not paths:
        body = "  # <service-id>: /absolute/path/to/repo"
    PATHS_FILE.write_text(HEADER.format(body), encoding="utf-8")


def cmd_list() -> int:
    reg = load_registry_repos()
    local = load_local_paths()
    all_ids = sorted(set(reg) | set(local))
    if not all_ids:
        print(f"(registry 无服务,{PATHS_FILE.name} 也无映射)")
        return 0

    print(f"{'service-id':<20} {'本地路径':<40} 状态")
    print("-" * 80)
    for sid in all_ids:
        path = local.get(sid)
        if sid not in reg:
            status = "WARN: 孤儿(registry 无此服务)"
        elif path is None:
            status = "未映射"
        else:
            remote = get_remote_url(pathlib.Path(path))
            if remote is None:
                status = "WARN: 路径不是 git 仓库或无 origin"
            elif remote != reg[sid] and remote not in (reg[sid],) and reg[sid] not in (remote,):
                # 只 WARN 不阻止(fork / ssh vs https 同仓库都允许)
                status = f"WARN: remote 不匹配(registry={reg[sid]}, local={remote})"
            else:
                status = "OK"
        print(f"{sid:<20} {path or '(未映射)':<40} {status}")
    return 0


def cmd_add(args: list[str]) -> int:
    if len(args) != 2:
        print("用法: vibe-paths.py add <service-id> <本地路径>")
        return 1
    sid, raw_path = args
    path = pathlib.Path(raw_path).expanduser().resolve()

    reg = load_registry_repos()
    if sid not in reg:
        print(f"ERROR: {sid} 未在 registry/services.yaml 登记(先登记服务再映射路径)")
        return 1
    if not path.is_dir():
        print(f"ERROR: {path} 不是目录")
        return 1
    if not (path / ".git").exists():
        print(f"ERROR: {path} 不是 git 仓库(缺少 .git/)")
        return 1

    remote = get_remote_url(path)
    if remote is None:
        print(f"ERROR: 无法读取 {path} 的 git remote(检查 origin 是否配置)")
        return 1
    if remote != reg[sid]:
        print(f"WARN:  remote 不匹配 —— registry={reg[sid]}, local={remote}")
        print(f'       (允许 fork / ssh-vs-https,继续写入;若 clone 错仓库请核对)')

    paths = load_local_paths()
    action = "更新" if sid in paths else "新增"
    paths[sid] = str(path)
    save_local_paths(paths)
    print(f"已{action}: {sid} -> {path}")
    print(f"写入 {PATHS_FILE.relative_to(ROOT)}")
    return 0


def cmd_check() -> int:
    reg = load_registry_repos()
    local = load_local_paths()
    errors: list[str] = []
    warnings: list[str] = []

    # 孤儿:本地有、registry 没有
    for sid in sorted(set(local) - set(reg)):
        warnings.append(f"{sid}: 本地映射存在但 registry 无此服务(孤儿,考虑删除)")

    # 未映射:registry 有、本地没有
    for sid in sorted(set(reg) - set(local)):
        warnings.append(f"{sid}: registry 登记但未映射本地路径(跨仓库跳转会失效)")

    # 已映射的逐项校验路径与 remote
    for sid in sorted(set(reg) & set(local)):
        path = pathlib.Path(local[sid])
        if not path.is_dir():
            errors.append(f"{sid}: 路径不存在或不是目录 ({path})")
            continue
        if not (path / ".git").exists():
            errors.append(f"{sid}: 不是 git 仓库 ({path})")
            continue
        remote = get_remote_url(path)
        if remote is None:
            errors.append(f"{sid}: 无法读取 git origin remote ({path})")
        elif remote != reg[sid]:
            warnings.append(f"{sid}: remote 不匹配 (registry={reg[sid]}, local={remote})")

    for w in warnings:
        print(f"WARN:  {w}")
    for e in errors:
        print(f"ERROR: {e}")
    total = len(set(reg))
    mapped = len(set(reg) & set(local))
    print(f"\n{mapped}/{total} 个服务已映射, {len(errors)} 个错误, {len(warnings)} 个警告")
    return 1 if errors else 0


def cmd_resolve(args: list[str]) -> int:
    if len(args) != 1:
        print("用法: vibe-paths.py resolve <service-id>", file=sys.stderr)
        return 1
    sid = args[0]
    local = load_local_paths()
    if sid not in local:
        print(f"ERROR: {sid} 未映射(用 `vibe-paths.py add {sid} <路径>` 登记)", file=sys.stderr)
        return 1
    # resolve 的输出给管道用,只打印纯路径
    print(local[sid])
    return 0


def main() -> int:
    # 剥离可选的 hub 目录参数(第一个非子命令参数若是目录则吃掉)
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return 0
    cmd = args[0]
    rest = args[1:]
    if cmd == "list":
        return cmd_list()
    if cmd == "add":
        return cmd_add(rest)
    if cmd == "check":
        return cmd_check()
    if cmd == "resolve":
        return cmd_resolve(rest)
    print(f"未知子命令: {cmd}(可用: list / add / check / resolve)")
    return 1


if __name__ == "__main__":
    sys.exit(main())

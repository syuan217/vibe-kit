#!/usr/bin/env python3
"""校验 registry/services.yaml 的结构与引用完整性。

用法: python3 scripts/registry-check.py
退出码: 0 通过(允许有 warning);1 存在 error。CI 与本地均可运行。
"""
import pathlib
import re
import sys

try:
    import yaml
except ImportError:
    sys.exit("缺少依赖 PyYAML,请先安装: pip install pyyaml")

ROOT = pathlib.Path(__file__).resolve().parent.parent
VALID_VIA = {"REST", "gRPC", "MQ", "DB", "其他"}
REQUIRED = ["id", "repo", "owner", "description", "docs"]

errors: list[str] = []
warnings: list[str] = []


def main() -> int:
    try:
        reg = yaml.safe_load((ROOT / "registry" / "services.yaml").read_text(encoding="utf-8"))
    except yaml.YAMLError as e:
        print(f"ERROR: yaml 解析失败: {e}")
        return 1

    reg = reg or {}  # 空文件时 safe_load 返回 None,兜底避免 AttributeError
    services = reg.get("services") or []
    ids = [s.get("id") for s in services]

    # id 唯一 & kebab-case
    for sid in ids:
        if not sid or not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", str(sid)):
            errors.append(f"{sid}: id 必须为 kebab-case")
    dup = {i for i in ids if ids.count(i) > 1}
    if dup:
        errors.append(f"id 重复: {dup}")

    known = set(ids)
    consumed: set[str] = set()
    for s in services:
        sid = s.get("id", "<无id>")
        for f in REQUIRED:
            if not s.get(f):
                errors.append(f"{sid}: 缺少必填字段 {f}")
        if "depends_on" not in s:
            errors.append(f"{sid}: 缺少 depends_on(无依赖请显式写 [])")
        for dep in s.get("depends_on") or []:
            did = dep.get("id")
            consumed.add(did)
            if did not in known:
                errors.append(f"{sid}: 依赖了未登记的服务 {did}(请先登记该服务)")
            if dep.get("via") not in VALID_VIA:
                errors.append(f"{sid} -> {did}: via 必须为 {sorted(VALID_VIA)} 之一")
            if dep.get("status", "active") not in {"active", "planned"}:
                errors.append(f"{sid} -> {did}: status 必须为 active 或 planned")
            if dep.get("status") == "planned" and not dep.get("spec"):
                warnings.append(f"{sid} -> {did}: planned 依赖建议标注 spec 编号以便溯源与关闭时转 active")
        if "consumers" in s:
            warnings.append(f"{sid}: consumers 请勿手工维护(由 depends_on 反推),建议删除该字段")

    # 孤立服务提示
    for s in services:
        sid = s.get("id", "<无id>")
        if not (s.get("depends_on") or []) and sid not in consumed:
            warnings.append(f"{sid}: 孤立服务(无依赖也无消费方),确认是否真实")

    # 依赖图新鲜度
    graph = ROOT / "docs" / "service-graph.md"
    reg_file = ROOT / "registry" / "services.yaml"
    if not graph.exists():
        warnings.append("docs/service-graph.md 不存在,运行 python3 scripts/registry-graph.py 生成")
    elif graph.stat().st_mtime < reg_file.stat().st_mtime:
        warnings.append("依赖图可能过期,运行 python3 scripts/registry-graph.py 重新生成")

    for w in warnings:
        print(f"WARN:  {w}")
    for e in errors:
        print(f"ERROR: {e}")
    print(f"\n{len(services)} 个服务, {len(errors)} 个错误, {len(warnings)} 个警告")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())

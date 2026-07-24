#!/usr/bin/env python3
"""校验 registry/services.yaml 的结构与引用完整性。

用法: python3 scripts/registry-check.py [hub目录]
退出码: 0 通过(允许有 warning);1 存在 error。CI 与本地均可运行。
"""
import os
import pathlib
import re
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
    if len(sys.argv) > 1:
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
        "用法: registry-check.py [hub目录],或设 $VIBE_HUB,或在 hub 根目录运行。"
    )


ROOT = find_hub()
VALID_VIA = {"REST", "DB"}                      # depends_on 收窄:facade/MQ 各有归处
VALID_FACADE_VIA = {"Dubbo", "SOFA", "gRPC", "Feign"}
VALID_STATUS = {"active", "planned"}
REQUIRED = ["id", "repo", "owner", "description", "docs"]
MIRROR_FIELDS = ("produces", "consumes", "calls")  # 关系单一来源:不应出现在服务条目

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
            if dep.get("status", "active") not in VALID_STATUS:
                errors.append(f"{sid} -> {did}: status 必须为 active 或 planned")
            if dep.get("status") == "planned" and not dep.get("spec"):
                warnings.append(f"{sid} -> {did}: planned 依赖建议标注 spec 编号以便溯源与关闭时转 active")
        for mf in MIRROR_FIELDS:
            if mf in s:
                warnings.append(
                    f"{sid}: {mf} 请勿写在服务条目(关系单一来源,在 topics/facades 维护),建议删除")
        if "consumers" in s:
            warnings.append(f"{sid}: consumers 请勿手工维护,建议删除该字段")

    topics = reg.get("topics") or []
    facades = reg.get("facades") or []

    # ── topics 校验 ──
    topic_names = [t.get("name") for t in topics]
    dup_t = {n for n in topic_names if topic_names.count(n) > 1}
    if dup_t:
        errors.append(f"topic name 重复: {dup_t}")
    for t in topics:
        name = t.get("name", "<无name>")
        if not t.get("name"):
            errors.append("topic 缺少 name")
        if t.get("owner") not in known:
            errors.append(f"topic {name}: owner {t.get('owner')} 未登记为服务")
        if not t.get("contract"):
            warnings.append(f"topic {name}: 建议补 contract 指针(schema 文档)")
        producers = t.get("producers") or []
        consumers = t.get("consumers") or []
        if not producers:
            errors.append(f"topic {name}: 至少需要 1 个 producer")
        for svc in producers + consumers:
            if svc not in known:
                errors.append(f"topic {name}: 引用了未登记的服务 {svc}")
        if t.get("status", "active") not in VALID_STATUS:
            errors.append(f"topic {name}: status 必须为 active 或 planned")

    # ── facades 校验 ──
    facade_ids = [f.get("id") for f in facades]
    dup_f = {i for i in facade_ids if facade_ids.count(i) > 1}
    if dup_f:
        errors.append(f"facade id 重复: {dup_f}")
    for f in facades:
        fid = f.get("id", "<无id>")
        if not f.get("id") or not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", str(fid)):
            errors.append(f"facade {fid}: id 必须为 kebab-case")
        if f.get("owner") not in known:
            errors.append(f"facade {fid}: owner {f.get('owner')} 未登记为服务")
        if f.get("via") not in VALID_FACADE_VIA:
            errors.append(f"facade {fid}: via 必须为 {sorted(VALID_FACADE_VIA)} 之一")
        if not f.get("contract"):
            warnings.append(f"facade {fid}: 建议补 contract 指针(方法签名文档)")
        for svc in f.get("called_by") or []:
            if svc not in known:
                errors.append(f"facade {fid}: called_by 引用了未登记的服务 {svc}")
        if f.get("status", "active") not in VALID_STATUS:
            errors.append(f"facade {fid}: status 必须为 active 或 planned")

    # 孤立服务提示(连接性:depends_on / 被依赖 / 参与 topic / 参与 facade)
    connected = set(consumed)
    for t in topics:
        if t.get("owner"):
            connected.add(t["owner"])
        connected.update(t.get("producers") or [])
        connected.update(t.get("consumers") or [])
    for f in facades:
        if f.get("owner"):
            connected.add(f["owner"])
        connected.update(f.get("called_by") or [])
    for s in services:
        sid = s.get("id", "<无id>")
        if not (s.get("depends_on") or []) and sid not in connected:
            warnings.append(f"{sid}: 孤立服务(无任何依赖/被依赖/收发/接口关系),确认是否真实")

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
    print(f"\n{len(services)} 个服务, {len(topics)} 个 topic, {len(facades)} 个 facade, "
          f"{len(errors)} 个错误, {len(warnings)} 个警告")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())

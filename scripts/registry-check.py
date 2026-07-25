#!/usr/bin/env python3
"""校验 registry/services.yaml 的结构与引用完整性。

用法: python3 scripts/registry-check.py [hub目录]
退出码: 0 通过(允许有 warning);1 存在 error。CI 与本地均可运行。
"""
import hashlib
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
VALID_VIA = {"REST", "DB", "Dubbo", "SOFA", "gRPC", "Feign"}  # 点对点调用;MQ 归 topics[]
VALID_STATUS = {"active", "planned"}
# boundary 自 v3 起必填:关系表只圈范围,"哪些事归谁"全靠它(facade 拿掉后更是唯一来源)
REQUIRED = ["id", "repo", "owner", "description", "docs", "boundary"]
MIRROR_FIELDS = ("produces", "consumes", "consumers", "calls")  # 关系单一来源:不应出现在服务条目

# contract 是**指针**不是内容:`<service-id>:<该仓库内相对路径>`,可带 #锚点
CONTRACT_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*:\S+$")

errors: list[str] = []
warnings: list[str] = []


def check_contract(value, label: str, provider: str, known: set) -> None:
    """校验 contract 指针。provider 是应当提供该契约的服务(依赖的对端 / topic 的 owner)。"""
    if not value:
        warnings.append(
            f"{label}: 建议补 contract 指针(格式 `<service-id>:<路径>`,如 `{provider}:docs/api.md`)")
        return
    v = str(value).strip()
    if v.startswith(("http://", "https://")):
        return  # 外部 API 门户:允许,但不随代码走,弱于入库文档
    if not CONTRACT_RE.match(v):
        warnings.append(
            f"{label}: contract `{v}` 缺少 `<service-id>:` 前缀,裸路径无法判断属于哪个仓库")
        return
    prefix = v.split(":", 1)[0]
    if prefix != provider:
        hint = "该服务未登记" if prefix not in known else "契约应由提供方维护"
        warnings.append(f"{label}: contract 前缀是 {prefix},应为 {provider}({hint})")


def main() -> int:
    try:
        reg = yaml.safe_load((ROOT / "registry" / "services.yaml").read_text(encoding="utf-8"))
    except yaml.YAMLError as e:
        print(f"ERROR: yaml 解析失败: {e}")
        return 1

    reg = reg or {}  # 空文件时 safe_load 返回 None,兜底避免 AttributeError

    # schema 版本必须显式为 3(v2 → v3 是破坏性升级,见 CHANGELOG 迁移指引)
    if reg.get("version") != 3:
        errors.append(f"schema version 必须为 3(当前: {reg.get('version', '缺失')};迁移见 CHANGELOG「迁移指引」)")

    # v2 遗留:facades[] 已折叠为服务级 depends_on(粒度改为服务级,不再记接口)
    if "facades" in reg:
        errors.append(
            "检测到 v2 的顶层 facades[]:v3 已取消接口级实体。"
            "把每个 facade 的 called_by 成员各加一条 depends_on: "
            "{id: <该 facade 的 owner>, via: <原 facade 的 via>},然后删除 facades[] 并把 version 改为 3"
        )

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
        # "不负责"那半句最容易省、也最有用:派活时 AI 靠它避免把活派给错误的服务
        if s.get("boundary") and "不负责" not in str(s["boundary"]):
            warnings.append(f"{sid}: boundary 建议补一句「不负责:…(归 <service-id>)」,划分工时最值钱的一行")
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
            check_contract(dep.get("contract"), f"{sid} -> {did}", str(did), known)
        for mf in MIRROR_FIELDS:
            if mf in s:
                warnings.append(
                    f"{sid}: {mf} 请勿写在服务条目(关系单一来源,MQ 关系在 topics[] 维护),建议删除")

    topics = reg.get("topics") or []

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
        check_contract(t.get("contract"), f"topic {name}", str(t.get("owner")), known)
        producers = t.get("producers") or []
        consumers = t.get("consumers") or []
        if not producers:
            errors.append(f"topic {name}: 至少需要 1 个 producer")
        for svc in producers + consumers:
            if svc not in known:
                errors.append(f"topic {name}: 引用了未登记的服务 {svc}")
        if t.get("status", "active") not in VALID_STATUS:
            errors.append(f"topic {name}: status 必须为 active 或 planned")

    # 孤立服务提示(连接性:depends_on / 被依赖 / 参与 topic)
    connected = set(consumed)
    for t in topics:
        if t.get("owner"):
            connected.add(t["owner"])
        connected.update(t.get("producers") or [])
        connected.update(t.get("consumers") or [])
    for s in services:
        sid = s.get("id", "<无id>")
        if not (s.get("depends_on") or []) and sid not in connected:
            warnings.append(f"{sid}: 孤立服务(无任何依赖/被依赖/收发/接口关系),确认是否真实")

    # 依赖图新鲜度:比对生成物内嵌的 services.yaml 内容 hash(mtime 不可靠,git 不保留)
    graph = ROOT / "docs" / "service-graph.md"
    reg_file = ROOT / "registry" / "services.yaml"
    if not graph.exists():
        warnings.append("docs/service-graph.md 不存在,运行 python3 scripts/registry-graph.py 生成")
    else:
        cur_hash = hashlib.sha256(reg_file.read_bytes()).hexdigest()[:16]
        m = re.search(r"<!--\s*source-hash:\s*([0-9a-f]+)\s*-->", graph.read_text(encoding="utf-8"))
        if not m:
            warnings.append("docs/service-graph.md 缺少来源 hash(旧版生成),运行 python3 scripts/registry-graph.py 重新生成")
        elif m.group(1) != cur_hash:
            warnings.append("依赖图已过期(services.yaml 内容已变化),运行 python3 scripts/registry-graph.py 重新生成")

    for w in warnings:
        print(f"WARN:  {w}")
    for e in errors:
        print(f"ERROR: {e}")
    print(f"\n{len(services)} 个服务, {len(topics)} 个 topic, "
          f"{len(errors)} 个错误, {len(warnings)} 个警告")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())

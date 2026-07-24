#!/usr/bin/env python3
"""从 registry/services.yaml 生成 mermaid 服务依赖图,写入 docs/service-graph.md。

用法: python3 registry-graph.py [hub目录]
registry 变更后重新运行即可(也可挂到 hub 仓库 CI)。
"""
import os
import pathlib
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
        "用法: registry-graph.py [hub目录],或设 $VIBE_HUB,或在 hub 根目录运行。"
    )


ROOT = find_hub()
OUT = ROOT / "docs" / "service-graph.md"


def node_id(sid: str) -> str:
    return sid.replace("-", "_").replace(".", "_")


def s_node(sid: str) -> str:  # 服务
    return "s_" + node_id(sid)


def t_node(name: str) -> str:  # topic
    return "t_" + node_id(name)


def f_node(fid: str) -> str:  # facade
    return "f_" + node_id(fid)


def main() -> None:
    reg = yaml.safe_load((ROOT / "registry" / "services.yaml").read_text(encoding="utf-8"))
    services = reg.get("services") or []
    topics = reg.get("topics") or []
    facades = reg.get("facades") or []
    known = {s["id"] for s in services}

    lines = [
        "# 服务依赖图",
        "",
        "> 由 `scripts/registry-graph.py` 从 `registry/services.yaml` 自动生成,勿手改。",
        "> 矩形=服务,六边形=MQ topic,平行四边形=facade 接口。",
        "",
        "```mermaid",
        "graph LR",
    ]
    # 服务节点(矩形)
    for s in services:
        desc = s.get("description", "")
        lines.append(f'  {s_node(s["id"])}["{s["id"]}<br/><small>{desc}</small>"]')
    # REST/DB 直连依赖
    for s in services:
        for dep in s.get("depends_on") or []:
            via = dep.get("via", "")
            if dep["id"] not in known:
                print(f'警告: {s["id"]} 依赖了未登记的服务 {dep["id"]}')
            lines.append(f'  {s_node(s["id"])} -->|{via}| {s_node(dep["id"])}')
    # topic 节点(六边形)+ 产/消边
    for t in topics:
        name = t["name"]
        lines.append(f'  {t_node(name)}{{{{"{name}"}}}}')
        for p in t.get("producers") or []:
            lines.append(f'  {s_node(p)} -->|produces| {t_node(name)}')
        for c in t.get("consumers") or []:
            lines.append(f'  {t_node(name)} -->|consumes| {s_node(c)}')
    # facade 节点(平行四边形)+ 调用/归属边
    for f in facades:
        fid = f["id"]
        via = f.get("via", "")
        lines.append(f'  {f_node(fid)}[/"{fid}"/]')
        if f.get("owner"):
            lines.append(f'  {f_node(fid)} -.owns.-> {s_node(f["owner"])}')
        for caller in f.get("called_by") or []:
            lines.append(f'  {s_node(caller)} -->|{via}| {f_node(fid)}')
    lines += ["```", ""]

    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"已生成 {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()

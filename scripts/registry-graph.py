#!/usr/bin/env python3
"""从 registry/services.yaml 生成 mermaid 服务依赖图,写入 docs/service-graph.md。

用法: python3 scripts/registry-graph.py
registry 变更后重新运行即可(也可挂到 hub 仓库 CI)。
"""
import pathlib

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "service-graph.md"


def node_id(sid: str) -> str:
    return sid.replace("-", "_")


def main() -> None:
    reg = yaml.safe_load((ROOT / "registry" / "services.yaml").read_text(encoding="utf-8"))
    services = reg.get("services") or []
    known = {s["id"] for s in services}

    lines = [
        "# 服务依赖图",
        "",
        "> 由 `scripts/registry-graph.py` 从 `registry/services.yaml` 自动生成,勿手改。",
        "",
        "```mermaid",
        "graph LR",
    ]
    for s in services:
        desc = s.get("description", "")
        lines.append(f'  {node_id(s["id"])}["{s["id"]}<br/><small>{desc}</small>"]')
    for s in services:
        for dep in s.get("depends_on") or []:
            via = dep.get("via", "")
            if dep["id"] not in known:
                print(f'警告: {s["id"]} 依赖了未登记的服务 {dep["id"]}')
            lines.append(f'  {node_id(s["id"])} -->|{via}| {node_id(dep["id"])}')
    lines += ["```", ""]

    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"已生成 {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()

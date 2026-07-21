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

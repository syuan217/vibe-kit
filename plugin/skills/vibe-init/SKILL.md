---
name: vibe-init
description: Initializes the vibe-kit spec-driven workflow in an application repository - runs spec-kit init for multiple AI agents, copies doc templates (AGENTS.md, docs/, wiki), and injects the team constitution. Use when the user says "初始化工作流", "bootstrap 这个仓库", "接入 vibe-kit", "set up vibe-kit", or wants to onboard a new/existing app repo to the team workflow.
---

# vibe-init — 应用仓库接入 vibe-kit 工作流

## 前置确认

1. 确认当前在应用仓库根目录(存在 `.git/`),否则让用户切换或指定路径。
2. 定位 hub 仓库(vibe-kit)本地路径:优先从对话获取;未知则询问用户。hub 是模板与宪法的唯一权威来源。
3. 检查 `specify` CLI:`command -v specify`。未安装则给出安装命令并等待用户确认安装:
   `uv tool install specify-cli --from git+https://github.com/github/spec-kit.git`

## 执行

优先直接运行 hub 脚本(等价于以下步骤):

```bash
<hub路径>/scripts/vibe-init.sh --integrations claude,cursor,codex
```

integrations 按团队实际使用的工具调整(询问用户或沿用默认)。脚本不可用时手动执行:

1. 对每个 agent 各跑一次 `specify init . --force --integration <agent> --ignore-agent-tools`
2. `cp -Rn <hub>/templates/app/. .`(不覆盖已有文件)
3. 若 `.specify/memory/constitution.md` 无有效内容,拷入 `<hub>/templates/constitution-base.md`
4. `cp <hub>/VERSION .vibe-kit-version`

## 收尾(必做)

1. 存量仓库:建议立即运行 vibe-init-docs skill 从代码生成真实文档;新仓库则引导用户填写 AGENTS.md 占位符。
2. 提醒用户在 hub `registry/services.yaml` 登记本服务(id、repo、owner、依赖),并重新生成依赖图:`python3 <hub>/scripts/registry-graph.py`
3. 提醒将 AGENTS.md、docs/、prompts/、`.specify/`、各 agent 命令目录全部提交入库。

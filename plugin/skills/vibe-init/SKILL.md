---
name: vibe-init
description: Initializes the vibe-kit spec-driven workflow in an application repository - runs spec-kit init for multiple AI agents, copies doc templates (AGENTS.md, docs/, wiki), and injects the team constitution. Use when the user says "初始化工作流", "bootstrap 这个仓库", "接入 vibe-kit", "set up vibe-kit", or wants to onboard a new/existing app repo to the team workflow.
---

# vibe-init — 应用仓库接入 vibe-kit 工作流

所需模板已随插件分发,位于 `${CLAUDE_PLUGIN_ROOT}/templates/`。**本 skill 不需要 clone 任何仓库;禁止为获取模板或定位 hub 而 clone 仓库。**

## 前置确认

1. 确认当前在应用仓库根目录(存在 `.git/`),否则让用户切换或指定路径。
2. 定位 hub(registry/总 spec 所在的团队协调仓库),按优先级:用户指明的路径 → 应用仓库根 `.vibe-hub` 文件 → `$VIBE_HUB` 环境变量 → 对话上下文 → **询问用户**(与其他 skill 相比多出「用户指明」最高优先档:首次接入时 `.vibe-hub` 尚不存在,本 skill 正是负责写入它的)。找不到时必须询问,不要猜、不要 clone;用户可选:
   - 提供已有 hub 的本地路径(校验其下存在 `registry/services.yaml`);
   - 暂无 hub → 本次跳过 hub 相关步骤(登记 registry 留到之后),初始化照常完成;
   - 想新建 hub → 指引用户 clone 团队已有的 hub 仓库,或用 vibe-kit 仓库的 `scripts/init-hub.sh <目录> --git` 创建。
3. 检查 `specify` CLI:`command -v specify`。未安装则询问用户,**经确认后代为执行安装**:
   `uv tool install specify-cli --from git+https://github.com/github/spec-kit.git`
   (若连 `uv` 也没有,先经确认安装 uv:`curl -LsSf https://astral.sh/uv/install.sh | sh`。未经用户确认不得安装任何软件。)

## 执行(直接按步骤操作,不依赖外部脚本)

1. spec-kit 初始化,每个 agent 各跑一次(integrations 询问用户或默认 claude,cursor,codex):
   `specify init . --force --integration <agent> --ignore-agent-tools`
2. 拷贝应用模板(不覆盖已有文件):`cp -Rn "${CLAUDE_PLUGIN_ROOT}/templates/app/." .`,然后 `rm -f ./gitignore`(该模板按第 5 步合并进 `.gitignore`,不落地为裸文件)。
3. 若 `.specify/memory/constitution.md` 不存在或无有效内容(无"工程宪法"字样),拷入 `${CLAUDE_PLUGIN_ROOT}/templates/constitution-base.md`。
4. 写本地标记文件(均已被 gitignore 忽略):
   - `.vibe-kit-version` ← 插件版本(读 `${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json` 的 version)
   - `docs/.sync-commit` ← `git rev-parse HEAD`(文档一致性基线)
   - `.vibe-hub` ← hub 绝对路径(前置第 2 步确定;跳过 hub 时不写)
5. 合并 gitignore:把 `${CLAUDE_PLUGIN_ROOT}/templates/app/gitignore` 中的条目逐行去重追加到应用仓库 `.gitignore`(已有条目不动)。

## 收尾(必做)

1. 存量仓库:建议立即运行 vibe-init-docs skill 从代码生成真实文档;新仓库则引导用户填写 AGENTS.md 占位符。
2. 若已配置 hub:提醒用户在 hub `registry/services.yaml` 登记本服务(id、repo、owner、依赖),并重新生成依赖图:`python3 <hub>/scripts/registry-graph.py`。未配置 hub 则提醒之后补办。
3. 提醒将 AGENTS.md、docs/、prompts/ 提交入库;`.specify/`、`specs/`、各 agent 命令目录、`.vibe-hub` 等已被 `.gitignore` 忽略,属本地生成物,队友各自跑 vibe-init 即可重建。

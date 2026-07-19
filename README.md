# vibe-kit

多仓库微服务团队的 spec-driven AI 开发工作流中心仓库(hub)。方案详见 **WORKFLOW.md**。

## 安装插件(Claude Code / Cowork)

本仓库同时是插件市场(`.claude-plugin/marketplace.json`),推送到 GitHub 后即可直接安装:

```
/plugin marketplace add syuan217/vibe-kit
/plugin install vibe-kit@vibe-kit
```

插件更新后执行 `/plugin marketplace update vibe-kit` 刷新。不用 Claude 的同事无需安装,使用应用仓库内 `prompts/*.md`(内容同源)。插件说明见 `plugin/USAGE.md`。

## 目录

```
WORKFLOW.md                  # 工作流方案(先读这个)
VERSION                      # kit 版本
registry/services.yaml       # 服务注册表:全系统服务清单、依赖关系、文档指针
registry/README.md           # registry 维护规范(更新时机、校验、校准)
specs/                       # 跨应用需求总 spec(_template/ 为模板)
docs/                        # 公共文档(总体架构、团队约定、doc-style 写作规范)
docs/requirement-playbook.md # 需求处理手册:一个需求下来时怎么做(团队必读)
templates/
  constitution-base.md       # 团队工程宪法基线(bootstrap 时注入应用仓库)
  app/                       # 应用仓库脚手架(AGENTS.md、README、docs、ADR、CI、PR 模板等)
prompts/
  vibe-init-docs.md          # 存量仓库从代码反向生成整套文档(初始)
  rebuild-wiki.md            # 从代码生成 wiki 定位层(code-map + 模块页)
  finalize-feature.md        # 需求完成后把 spec 结论沉淀进 docs/(收尾)
  sync-docs.md               # 增量补齐文档(日常失真修复)
  registry-sync.md           # 从代码反推服务依赖,校准 registry
scripts/
  vibe-init.sh               # 在应用仓库初始化本工作流
  registry-graph.py          # 从 registry 生成 mermaid 服务依赖图
  registry-check.py          # registry 结构与引用校验(CI/本地)
plugin/                      # Claude 插件源码(6 个 skills,打包为 vibe-kit.plugin 分发)
```

## 快速开始

1. 安装 spec-kit CLI:

   ```bash
   uv tool install specify-cli --from git+https://github.com/github/spec-kit.git
   ```

2. 在某个应用仓库根目录执行:

   ```bash
   /path/to/vibe-kit/scripts/vibe-init.sh --integrations claude,cursor,codex
   ```

3. 按脚本输出提示:填写 `AGENTS.md`、在本仓库 `registry/services.yaml` 登记该应用、提交入库。

4. 用一个真实需求走流程:`/speckit.specify → clarify → plan → tasks → implement`。

跨应用需求:先在本仓库 `specs/` 复制 `_template/` 立总 spec,再到各应用仓库走上述流程(见 `specs/README.md`)。

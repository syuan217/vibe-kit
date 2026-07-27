# vibe-kit

多仓库微服务团队的 spec-driven AI 开发工作流中心仓库(hub)。方案详见 **WORKFLOW.md**。

## 安装插件(Claude Code / zcode / Kimi Code / Cowork)

本仓库同时是插件市场(`.claude-plugin/marketplace.json`),推送到 GitHub 后即可直接安装。插件根目录携带 `.zcode-plugin/plugin.json`、`.kimi-plugin/plugin.json` 与 `.claude-plugin/plugin.json` 三份清单,**Claude Code、zcode 与 Kimi Code 都支持**,skill 内容同一份。

**Claude Code / Cowork**:

```
/plugin marketplace add syuan217/vibe-kit
/plugin install vibe-kit@vibe-kit
```

**zcode**:Settings → Plugin Management → Discover,点 `+` 添加 GitHub 地址 `syuan217/vibe-kit`,然后安装 vibe-kit。

**Kimi Code**(仓库根的 `kimi.plugin.json` 是安装入口):

```
/plugins install https://github.com/syuan217/vibe-kit
```

或**离线方式**:从 GitHub Release 下载 `vibe-kit.plugin`,Claude / zcode 直接拖入会话安装;Kimi Code 解压后执行 `/plugins install <解压目录>`。

插件更新后:Claude 执行 `/plugin marketplace update vibe-kit` 刷新;zcode 在 Discover 刷新后重装;Kimi Code 重新执行 `/plugins install` 并 `/reload`。不用 Claude / zcode / Kimi Code 的同事(如 Cursor、Codex 用户)无需安装,使用应用仓库内 `prompts/*.md`(内容同源)。插件说明见 `plugin/USAGE.md`。

## 目录

```
AGENTS.md                    # 本仓库自身的 AI 上下文入口(修改本仓库前必读)
WORKFLOW.md                  # 工作流方案(先读这个)
VERSION                      # kit 版本
CHANGELOG.md                 # 版本变更记录(发版时由 vibe-release.py 维护)
registry/services.yaml       # 服务注册表:全系统服务清单、依赖关系、文档指针
registry/README.md           # registry 维护规范(更新时机、校验、校准)
specs/                       # 跨应用需求总 spec(_template/ 为模板)
docs/                        # 公共文档(总体架构、团队约定、doc-style 写作规范)
docs/requirement-playbook.md # 需求处理手册:一个需求下来时怎么做(团队必读)
plugin/templates/
  constitution-base.md       # 团队工程宪法基线(bootstrap 时注入应用仓库)
  app/                       # 应用仓库脚手架(AGENTS.md、README、docs、ADR、CI、PR 模板等)
prompts/                     # 与 plugin/skills 同源,由 sync-prompts.py 生成(勿手改)
  cross-app-spec.md          # 跨应用需求总 spec(影响面分析 + 契约先行)
  vibe-init-docs.md          # 存量仓库从代码反向生成整套文档(初始)
  rebuild-wiki.md            # 从代码生成 wiki 定位层(code-map + 模块页)
  finalize-feature.md        # 需求完成后把 spec 结论沉淀进 docs/(收尾)
  sync-docs.md               # 增量补齐文档(日常失真修复)
  registry-sync.md           # 从代码反推服务依赖,校准 registry
scripts/
  vibe-init.sh               # 在应用仓库初始化本工作流(--hub 指定独立 hub)
  init-hub.sh                # 创建与 kit 分离的独立 hub 目录/仓库
  registry-graph.py          # 从 registry 生成 mermaid 服务依赖图
  registry-check.py          # registry 结构与引用校验(CI/本地)
  vibe-paths.py              # 服务仓库本地路径映射(list/add/check/resolve)
  vibe-release.py            # 发版校验与半自动 bump(check/bump)
  sync-prompts.py            # 从 SKILL.md 生成 prompts/ 同源副本(--write/--check)
tests/                       # pytest:registry/vibe-paths 脚本 + prompt 同源
plugin/                      # Claude/zcode/Kimi Code 插件源码(7 个 skills,打包为 vibe-kit.plugin 分发)
```

## 快速开始

1. 安装 spec-kit CLI:

   ```bash
   uv tool install specify-cli --from git+https://github.com/github/spec-kit.git
   ```

2. (可选)如需 hub 与 kit 分离:`/path/to/vibe-kit/scripts/init-hub.sh ~/team-hub --git`(三种部署形态见 WORKFLOW.md §1.1)

3. 在某个应用仓库根目录执行:

   ```bash
   /path/to/vibe-kit/scripts/vibe-init.sh --integrations claude,cursor,codex [--hub ~/team-hub]
   ```

4. 按脚本输出提示:填写 `AGENTS.md`、在 hub 的 `registry/services.yaml` 登记该应用、提交入库。

5. 用一个真实需求走流程:`/speckit.specify → clarify → plan → tasks → implement`。

跨应用需求:先在本仓库 `specs/` 复制 `_template/` 立总 spec,再到各应用仓库走上述流程(见 `specs/README.md`)。

## License

[MIT](LICENSE)

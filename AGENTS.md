# vibe-kit

> 本仓库自身的 AI 统一上下文入口。这是一个 **kit + hub 合一**仓库:kit 是分发给团队的工作流工具,hub 是团队协调数据中心。

## 仓库定位

为多仓库微服务团队提供 spec-driven AI 开发工作流。完整方案见 WORKFLOW.md,目录说明见 README.md。

- **kit 部分**(工具,随版本演进):`plugin/`(含 `plugin/templates/`)、`prompts/`、`scripts/`、`VERSION`
- **hub 部分**(团队数据,持续更新):`registry/`、`specs/`、`docs/`
- **市场清单**:`.claude-plugin/marketplace.json`(本仓库即插件市场)

## 常用命令

- 校验 registry:`python3 scripts/registry-check.py`
- 重生成依赖图:`python3 scripts/registry-graph.py`
- 打包插件:`cd plugin && zip -r ../vibe-kit.plugin . -x "*.DS_Store"`
- 应用接入:`scripts/vibe-init.sh`;独立 hub:`scripts/init-hub.sh <目录> --git`

## 修改本仓库的硬性约定(AI 必须遵守)

1. **同源必须同步改**(范围按工作流的操作对象精确划定,不要机械补齐副本):
   - **三处同源**(skill + `prompts/` + `plugin/templates/app/prompts/`):finalize-feature、rebuild-wiki、sync-docs——在应用仓库日常执行,三类用户都需要。
   - **两处同源**(skill + `prompts/`):cross-app-spec、registry-sync、vibe-init-docs——操作对象是 hub 或一次性执行,应用仓库不放副本。
   - **仅 skill**:vibe-init——由 `scripts/vibe-init.sh` 驱动,逻辑变更须同步改脚本,不出 prompt 副本。
   改任何一处,必须同步同组其余文件;skill 的 references/ 模板与 `plugin/templates/`、`specs/_template/` 中的源模板同理。
2. **改了 `plugin/` 就要发版**:`plugin/.claude-plugin/plugin.json` 与 `.claude-plugin/marketplace.json` 两处版本号同步递增,`VERSION` 跟随,重新打包 .plugin;发布 = push + 打 `v*` tag(CI 自动发 Release)。
3. **registry 变更**:改 `registry/services.yaml` 后运行 registry-check 与 registry-graph;规则见 `registry/README.md`。
4. **文档规范**:遵循 `docs/doc-style.md`;修改模板时保持与 WORKFLOW.md、README.md、`plugin/USAGE.md` 的交叉引用一致。
5. 团队宪法基线(`plugin/templates/constitution-base.md`)条款变更需团队评审,不得随手改。

## 文档地图

- WORKFLOW.md — 工作流方案(痛点→机制、hub 部署形态)
- README.md — 目录与快速开始
- docs/requirement-playbook.md — 需求处理手册(团队必读)
- docs/doc-style.md — 文档写作规范(含分支与文档规则)
- registry/README.md — registry 维护规范
- plugin/USAGE.md — 插件使用说明(人 + AI)
- specs/README.md — 跨应用总 spec 流程

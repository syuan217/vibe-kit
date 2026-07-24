# Changelog

本文件记录 vibe-kit 所有版本的变更。由 `scripts/vibe-release.py` 起草,人工校对。

格式参考 [keepachangelog.com](https://keepachangelog.com/),遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [Unreleased]

## [0.8.0] - 2026-07-24

### Added

- **zcode 平台支持**:新增 `plugin/.zcode-plugin/plugin.json` 作为 zcode 原生清单(与 `.claude-plugin/plugin.json` 同源)。zcode 与 Claude Code 共享同一份 skill 内容与 marketplace,安装方式见 `README.md` / `plugin/USAGE.md`。

### Changed

- 版本号同步点从 4 处扩展为 5 处(新增 `plugin/.zcode-plugin/plugin.json`),`scripts/vibe-release.py` 的 check/bump 与 CI `plugin-release.yml` 同步纳入校验。
- `plugin/skills/vibe-init/SKILL.md` 把 Claude 专有的 `${CLAUDE_PLUGIN_ROOT}` 改为平台无关的指令式描述(「插件根目录 = SKILL.md 向上两级」),读版本号改为兼容 `.zcode-plugin/` 或 `.claude-plugin/` 任一清单。
- `AGENTS.md` 硬性约定 #2 更新为五处版本号同步;`README.md`、`plugin/USAGE.md` 补 zcode 安装说明,FAQ 把 zcode 从「其他工具用 prompts/」移入「装插件即可」。

## [0.7.0] - 2026-07-24

### Changed

- **registry schema v1 → v2(破坏性)**:`depends_on.via` 收窄为 `REST`/`DB`;MQ 关系迁移到 `topics[]`(producers/consumers)、RPC facade 迁移到 `facades[]`(owner/called_by);服务新增 `boundary` 字段。关系单一来源,服务条目不再镜像 produces/consumes/calls。
- cross-app-spec 影响面分析升级为图遍历(沿 topics/facades/depends_on 扩散),总 spec 影响面表新增「边界」「交互方式」列。
- registry-sync 扫描按 topics/facades/depends_on 三类归位,新增对外接口时提醒复核 `boundary`;finalize-feature 同步该提醒。
- registry-check / registry-graph 支持 topics/facades(图渲染六边形 topic、平行四边形 facade);新增 `tests/` 脚本测试并接入 CI。
- `registry/README.md`、`WORKFLOW.md` §2.2、`plugin/USAGE.md` 同步 v2 三类关系模型。

### 迁移指引

- 已有 registry:`version: 1 → 2`;把 `via: gRPC/Dubbo/SOFA` 的 depends_on 改写为 `facades[]` 条目、`via: MQ` 改写为 `topics[]` 条目;给各服务补 `boundary`。跑 `python3 scripts/registry-check.py` 校验。

## [0.6.0] - 2026-07-21

> **升级指南**:按身份(Claude 插件用户 / 已接入应用仓库 / hub 维护者)见 `plugin/USAGE.md` FAQ「从 0.5.0 升级到 0.6.0?」。

### Added

- 本地代码路径映射(`.vibe-paths.local.yaml` + `scripts/vibe-paths.py` 的 `list`/`add`/`check`/`resolve` 子命令):让 AI 从 hub 的 service-id 一步跳到本机 clone 的代码目录,不再停在 GitHub URL。机制见 `docs/local-paths.md`。
- 发版自动化(`scripts/vibe-release.py` 的 `check`/`bump` 两模式):扫描版本号与 skill 名册的漂移、半自动起草 CHANGELOG 条目、重打包 .plugin。
- `CHANGELOG.md`(本文件),回填 0.4.3 / 0.4.4 / 0.5.0 历史条目。

### Changed

- `registry/README.md`、`plugin/USAGE.md`、`AGENTS.md` 增补本地路径映射机制的条目与 AI 使用规则。
- cross-app-spec / registry-sync / finalize-feature 的 skill 副本(共 7 处同源)新增跨仓库跳转引导:优先 `vibe-paths.py resolve`,禁止为定位而 clone。
- CI `plugin-release.yml` 校验从 2 处扩展为 4 处(`VERSION` + `plugin.json` + `marketplace.json` 顶层 + `plugins[0]`)版本号一致。
- `scripts/registry-check.py` 与 `scripts/registry-graph.py` 加固:`find_hub()` 多级回退(命令行参数 > `$VIBE_HUB` > 当前目录 > 脚本上级目录)+ PyYAML 缺失友好提示。脚本随插件分发到应用仓库后不再依赖自身位置。

### Fixed

- 修正 `README.md` 目录树里 skills 数量漂移(6 → 7)。

## [0.5.0] - 2026-07-20

> 追溯填写。素材取自 `v0.4.4..v0.5.0` 的 git log。

### Added

- 插件**内置模板与团队宪法**(位于 `plugin/templates/`),与 hub 解耦——安装即可用,无需 clone vibe-kit 仓库。
- 加固 wiki(code-map 路径必须真实存在、符号不写行号等)。
- 仓库自身的 `AGENTS.md`:AI 统一上下文入口,含同源同步、发版等硬性约定。

## [0.4.4] - 2026-07-19

> 追溯填写。素材取自 `v0.4.3..v0.4.4` 的 git log。

### Added

- `vibe-init` 在用户确认后自动安装 spec-kit CLI,引导 `uv tool install`。

### Changed

- CI `actions/checkout` v4 → v5(Node 20 弃用)。

## [0.4.3] - 2026-07-19

> 追溯填写。素材取自 tag commit message。

### Added

- registry 依赖新增 `status: planned` / `active`(显式表达 hub 超前于应用的中间态)+ `spec` 溯源字段。
- 受控的 hub/应用文档时间差机制:planned 依赖在契约定稿时预登记、上线时转 active。

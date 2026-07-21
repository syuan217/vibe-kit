# Changelog

本文件记录 vibe-kit 所有版本的变更。由 `scripts/vibe-release.py` 起草,人工校对。

格式参考 [keepachangelog.com](https://keepachangelog.com/),遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [Unreleased]

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

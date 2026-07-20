# vibe-kit plugin

把 vibe-kit 工作流能力封装为 7 个 skills,AI 按场景自动触发,也可直接说 skill 名调用。

**完整使用说明(人 + AI agent)见 [USAGE.md](USAGE.md)。**

## Skills

| Skill | 触发场景 | 阶段 |
|---|---|---|
| vibe-init | "初始化工作流 / 接入 vibe-kit" | 仓库接入 |
| vibe-init-docs | "这个仓库没文档 / 反向生成文档" | 初始生成 |
| rebuild-wiki | "生成 wiki / 代码地图" | 初始生成·重建 |
| cross-app-spec | "这个需求涉及多个服务" | 需求开始 |
| finalize-feature | "需求收尾 / 沉淀文档" | 需求结束 |
| sync-docs | "同步文档 / 文档过期了" | 日常修复 |
| registry-sync | "校准依赖 / 检查服务依赖关系" | 定期校准 |

## 说明

- **hub 依赖**:vibe-init 与 cross-app-spec 需要本地有 vibe-kit hub 仓库(模板、宪法、registry 的唯一权威来源);其余 skills 可独立工作。
- **跨工具策略**:本插件服务 Claude Code / Cowork 用户;Cursor、Codex 同事继续使用各应用仓库内 `prompts/*.md`(内容同源)。修改工作流时,`plugin/skills/` 与 `prompts/`、`plugin/templates/` 需同步更新。
- 前置:spec-kit CLI(`specify`),vibe-init 会检查并给出安装命令。

## 安装

从 GitHub(推荐):`/plugin marketplace add syuan217/vibe-kit`,然后 `/plugin install vibe-kit@vibe-kit`。
或将 GitHub Release 中的 `vibe-kit.plugin` 文件拖入 Cowork 会话点击安装。

# vibe-kit plugin

把 vibe-kit 工作流能力封装为 10 个 skills,AI 按场景自动触发,也可直接说 skill 名调用。

**完整使用说明(人 + AI agent)见 [USAGE.md](USAGE.md)。**

## Skills

| Skill | 触发场景 | 阶段 |
|---|---|---|
| vibe-init | "初始化工作流 / 接入 vibe-kit" | 仓库接入 |
| vibe-init-docs | "这个仓库没文档 / 反向生成文档" | 初始生成 |
| rebuild-wiki | "生成 wiki / 代码地图" | 初始生成·重建 |
| cross-app-spec | "这个需求涉及多个服务" | 需求开始(跨应用) |
| vibe-clarify | "起草需求 / 需求澄清" | 需求阶段1:澄清+定方案 |
| vibe-build | "实现需求 / 按 blueprint 实现" | 需求阶段2:实现+单测 |
| vibe-verify | "核对实现 / 检查这次的改动" | 需求阶段3:核对一致性 |
| finalize-feature | "需求收尾 / 沉淀文档" | 需求结束(评审通过、合并前) |
| sync-docs | "同步文档 / 文档过期了" | 日常修复 |
| registry-sync | "校准依赖 / 检查服务依赖关系" | 定期校准 |

## 说明

- **hub 依赖**:模板与宪法随插件分发,无需 clone hub;hub 只存 registry 与总 spec。cross-app-spec 需要 hub;vibe-init 无 hub 也可先接入(之后补登记);其余 skills 可独立工作。
- **跨工具策略**:本插件服务 Claude Code / zcode / Kimi Code / Cowork 用户;Cursor、Codex 同事继续使用各应用仓库内 `prompts/*.md`(内容同源)。修改工作流只改 `plugin/skills/`(唯一源),`prompts/` 与应用模板副本由 `scripts/sync-prompts.py --write` 生成(CI `--check` 防漂移)。
- 前置:vibe-clarify/vibe-verify 调用外部引擎(mattpocock skills:grill-with-docs、code-review、tdd),vibe-init 会提示用 `npx skills add mattpocock/skills -a <agent>` 安装(详见 USAGE.md)。

## 安装

从 GitHub(推荐):Claude 用 `/plugin marketplace add syuan217/vibe-kit` 然后 `/plugin install vibe-kit@vibe-kit`;zcode 在 Settings → Plugin Management → Discover 添加同一 GitHub 地址后安装;Kimi Code 执行 `/plugins install https://github.com/syuan217/vibe-kit`。
或将 GitHub Release 中的 `vibe-kit.plugin` 文件拖入会话安装(Claude / zcode;Kimi Code 解压后 `/plugins install <解压目录>`)。

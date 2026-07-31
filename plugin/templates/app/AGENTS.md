# <应用名>

> 所有 AI 编码工具(Claude Code / Cursor / Codex 等)的统一上下文入口。
> 保持精简(≤150 行):细节放 docs/,按需引用,不在此堆砌。

## 应用概览

- 职责:<一句话说明本服务做什么>
- 所属系统:见 hub 仓库 <vibe-kit 仓库地址> 的 registry/services.yaml(上下游依赖以它为准)

## 技术栈

<语言 / 框架 / 数据库 / 关键中间件及版本>

## 常用命令

- 构建:`<command>`
- 测试:`<command>`
- 本地运行:`<command>`
- lint:`<command>`

## 目录结构

<3~8 行,只列关键目录及职责>

## 编码约定

- 遵循 `docs/constitution.md`(团队基线 + 应用补充),其中文档更新是任务完成定义的一部分
- <应用特有约定>

## 文档地图

- docs/wiki/code-map.md — **改代码前先查这里**:功能→代码定位表
- docs/wiki/modules/ — 模块页(关键文件、流程、常见修改场景)
- docs/architecture.md — 架构、模块、数据流
- docs/api.md — 对外契约(API/消息/事件)
- docs/decisions/ — 架构决策记录(ADR,模板 0000)
- docs/constitution.md — 团队工程宪法(基线 + 应用补充)
- specs/ — 需求过程产物(requirement/blueprint/open-questions;长期真相在 docs/)
- specs/_template/ — 单应用需求文档骨架(requirement/blueprint/open-questions 模板,vibe-clarify 套用;**入库**,是 `specs/` 整体不入库的唯一例外)
- prompts/vibe-clarify.md — 阶段1:起草需求 + 澄清 + 出 blueprint
- prompts/vibe-build.md — 阶段2:按 blueprint 实现 + 单测
- prompts/vibe-verify.md — 阶段3:核对实现 vs blueprint
- prompts/finalize-feature.md — 需求完成后(评审通过、合并前)把结论沉淀进长期文档
- prompts/sync-docs.md — 发现文档与代码不一致时,按此流程补齐
- 文档写作规范:hub 仓库 docs/doc-style.md

## 前置依赖(工作流引擎)

本工作流的澄清/评审引擎来自 **mattpocock/skills**(外部依赖,英文 skill,不随 vibe-kit 插件分发):

- grill-with-docs — vibe-clarify 的逐个澄清引擎
- code-review — vibe-verify 的两轴评审引擎
- tdd — vibe-build 的单测方法指引(可选)

首次接入或换机器后安装(按你用的 AI agent 选 `-a`):

```
npx skills add mattpocock/skills -a claude-code    # 或 codex / cursor / zcode / kimi-code-cli
```

详见 hub 仓库 `WORKFLOW.md`「引擎层依赖」。

## 开发工作流(必须遵守)

1. 需求先走 `/vibe-clarify`:单应用需求直接启动;跨应用需求先在 hub 仓库立总 spec(cross-app-spec),子 spec 首行引用总 spec 链接
2. `/vibe-clarify` → `/vibe-build` → `/vibe-verify`;动手改代码前先查 docs/wiki/code-map.md 定位,查不到再全库搜索并事后补进 code-map
3. `/vibe-verify` 通过后提 PR;**评审通过、合并前**按 prompts/finalize-feature.md 把结论沉淀进 docs/;平时发现文档失真按 prompts/sync-docs.md 补齐
4. 对外契约变更:更新 docs/api.md + 同步 hub registry/services.yaml

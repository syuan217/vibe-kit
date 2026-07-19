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

- 遵循 `.specify/memory/constitution.md`(团队基线 + 应用补充),其中文档更新是任务完成定义的一部分
- <应用特有约定>

## 文档地图

- docs/wiki/code-map.md — **改代码前先查这里**:功能→代码定位表
- docs/wiki/modules/ — 模块页(关键文件、流程、常见修改场景)
- docs/architecture.md — 架构、模块、数据流
- docs/api.md — 对外契约(API/消息/事件)
- docs/decisions/ — 架构决策记录(ADR,模板 0000)
- specs/ — 需求规格(spec-kit 过程产物;长期真相在 docs/)
- prompts/finalize-feature.md — 需求完成后把 spec 结论沉淀进长期文档
- prompts/sync-docs.md — 发现文档与代码不一致时,按此流程补齐
- 文档写作规范:hub 仓库 docs/doc-style.md

## 开发工作流(必须遵守)

1. 需求先有 spec:单应用需求直接 `/speckit.specify`;跨应用需求先在 hub 仓库立总 spec,子 spec 首行引用总 spec 链接
2. `/speckit.clarify` → `/speckit.plan` → `/speckit.tasks` → `/speckit.implement`;动手改代码前先查 docs/wiki/code-map.md 定位,查不到再全库搜索并事后补进 code-map
3. 需求完成、合 PR 前按 prompts/finalize-feature.md 把结论沉淀进 docs/;平时发现文档失真按 prompts/sync-docs.md 补齐
4. 对外契约变更:更新 docs/api.md + 同步 hub registry/services.yaml

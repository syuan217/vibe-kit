---
name: finalize-feature
description: Finalizes a completed feature by distilling vibe-clarify/build artifacts (specs/NNN-xxx: requirement.md, blueprint.md, open-questions.md) into long-lived docs - wiki code-map, architecture, API contract, and ADRs - after PR review passes and before the merge. Use when the user says "需求收尾", "收尾 specs/NNN", "finalize feature", "沉淀文档", or right after /vibe-verify passes (actual best timing: PR reviewed & approved, before merge).
---

# finalize-feature — 需求完成后的文档收尾

定位:requirement/blueprint/open-questions 是**过程产物**,docs/ 才是**长期真相**。此步把本次需求的结论沉淀进长期文档,否则文档会随需求数量增加而失真。**最佳时机是 PR 评审通过、合并前**——代码定稿后再沉淀,避免评审返工让文档失真(`/vibe-verify` 通过只代表"可以提 PR",不是"可以沉淀文档")。

## 步骤

1. 读取本次 `specs/NNN-xxx/`(requirement.md、blueprint.md、open-questions.md、spec.md)与实际代码变更(`git diff`)。
2. 以**代码实际实现**为准(实现可能偏离 plan),沉淀到长期文档:
   - docs/wiki/(**逐项核对,不可整体略过**):先从本次 diff 列出新增/变更的入口清单(controller/路由、RPC 接口、消息收发、定时任务),逐项检查 code-map 是否有对应条目——没有则补行,有则校对路径;受影响模块页更新关键文件与常见修改场景;新模块则复制 `_module-template.md` 建页并登记索引;最后汇报"入口 N 项,新增条目 M 行"
   - docs/architecture.md:新增/变更的模块、依赖、数据流、数据模型
   - docs/api.md:契约变化,并在变更记录表补一行
   - AGENTS.md:命令、目录结构、约定如有变化
   - 重大技术决策 → docs/decisions/ 新增 ADR(复制 `0000-adr-template.md`)
3. 核对 spec.md「实现偏差」一节(vibe-build/vibe-verify 已记录实现与 blueprint 的偏离);若仍有未记的明显偏离,补一句话/条。
4. 跨应用需求:提醒用户回填 hub 总 spec 的影响面表格与状态;依赖变化则更新 hub `registry/services.yaml`。hub 定位:`.vibe-hub` 文件 → `$VIBE_HUB` 环境变量 → 对话上下文 → **询问用户**;不要猜,**禁止为定位 hub 而 clone 任何仓库**。若需核对其它涉及服务的实现进度,先在 hub 跑 `python3 scripts/vibe-paths.py resolve <对端 service-id>` 取本地路径(见 `docs/local-paths.md`,未映射则询问用户)。若本次为本服务**新增**了对外 RPC 接口或 MQ topic(producer),提示用户其 registry `boundary` 描述是否需要更新——registry 是服务级粒度、不记具体接口,`boundary` 是唯一还能表达"这个服务对外负责什么"的字段(人工维护,不自动改)。
5. 遵循 hub `docs/doc-style.md` 写作规范;输出变更摘要,经用户确认后提交文档改动:`docs: finalize NNN-xxx`,并更新本地基线 `git rev-parse HEAD > docs/.sync-commit`(该文件已被 .gitignore 忽略,不入库)。

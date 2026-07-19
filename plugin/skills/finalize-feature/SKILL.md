---
name: finalize-feature
description: Finalizes a completed feature by distilling spec-kit artifacts (specs/NNN-xxx) into long-lived docs - wiki code-map, architecture, API contract, and ADRs - before the PR is merged. Use when the user says "需求收尾", "收尾 specs/NNN", "finalize feature", "沉淀文档", or right after /speckit.implement completes.
---

# finalize-feature — 需求完成后的文档收尾

定位:spec/plan/tasks 是**过程产物**,docs/ 才是**长期真相**。此步把本次需求的结论沉淀进长期文档,否则文档会随需求数量增加而失真。在 `/speckit.implement` 完成、合 PR 前执行。

## 步骤

1. 读取本次 `specs/NNN-xxx/`(spec.md、plan.md、data-model.md、contracts/ 等)与实际代码变更(`git diff`)。
2. 以**代码实际实现**为准(实现可能偏离 plan),沉淀到长期文档:
   - docs/wiki/:code-map 补/改功能条目,受影响模块页更新关键文件与常见修改场景;新模块建页并登记索引
   - docs/architecture.md:新增/变更的模块、依赖、数据流、数据模型
   - docs/api.md:契约变化,并在变更记录表补一行
   - AGENTS.md:命令、目录结构、约定如有变化
   - 重大技术决策 → docs/decisions/ 新增 ADR(模板 `references/adr-template.md`)
3. 实现与 plan 的偏离处,在 spec.md 末尾补「实现偏差」一节(一句话/条即可)。
4. 跨应用需求:提醒用户回填 hub 总 spec 的影响面表格与状态;依赖变化则更新 hub `registry/services.yaml`。
5. 输出变更摘要,经用户确认后提交:`docs: finalize NNN-xxx`。

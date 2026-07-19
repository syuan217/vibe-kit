# finalize-feature — 需求完成后的文档收尾

> 用法:`/speckit.implement` 完成、合 PR 前,对任意 AI 工具说"按 prompts/finalize-feature.md 收尾 specs/NNN-xxx"。
> 定位:spec/plan/tasks 是**过程产物**,docs/ 才是**长期真相**。此步把本次需求的结论沉淀进长期文档,否则文档会随需求数量增加而失真。

## 步骤

1. 读取本次 `specs/NNN-xxx/`(spec.md、plan.md、data-model.md、contracts/ 等)与实际代码变更(`git diff`)。
2. 以**代码实际实现**为准(实现可能偏离 plan),沉淀到长期文档:
   - docs/wiki/:code-map 补/改功能条目,受影响模块页更新关键文件与常见修改场景(新模块则复制 _module-template.md 建页并登记索引)
   - docs/architecture.md:新增/变更的模块、依赖、数据流、数据模型
   - docs/api.md:契约变化,并在变更记录表补一行
   - AGENTS.md:命令、目录结构、约定如有变化
   - 重大技术决策 → docs/decisions/ 新增 ADR(复制 0000-adr-template.md)
3. 实现与 plan 的偏离处,在 spec.md 末尾补「实现偏差」一节(一句话/条即可)。
4. 跨应用需求:提醒用户回填 hub 总 spec 的影响面表格与状态;依赖关系变化则更新 hub registry/services.yaml。
5. 遵循 hub `docs/doc-style.md` 写作规范;输出变更摘要,确认后将当前 HEAD 写入基线(`git rev-parse HEAD > docs/.sync-commit`)并一起提交:`docs: finalize NNN-xxx`。

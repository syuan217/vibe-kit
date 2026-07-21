# finalize-feature — 需求完成后的文档收尾

> 用法:`/speckit.implement` 完成、合 PR 前,对任意 AI 工具说"按 prompts/finalize-feature.md 收尾 specs/NNN-xxx"。
> 定位:spec/plan/tasks 是**过程产物**,docs/ 才是**长期真相**。此步把本次需求的结论沉淀进长期文档,否则文档会随需求数量增加而失真。

## 步骤

1. 读取本次 `specs/NNN-xxx/`(spec.md、plan.md、data-model.md、contracts/ 等)与实际代码变更(`git diff`)。
2. 以**代码实际实现**为准(实现可能偏离 plan),沉淀到长期文档:
   - docs/wiki/(**逐项核对,不可整体略过**):先从本次 diff 列出新增/变更的入口清单(controller/路由、RPC 接口、消息收发、定时任务),逐项检查 code-map 是否有对应条目——没有则补行,有则校对路径;受影响模块页更新关键文件与常见修改场景(新模块则复制 _module-template.md 建页并登记索引);最后汇报"入口 N 项,新增条目 M 行"
   - docs/architecture.md:新增/变更的模块、依赖、数据流、数据模型
   - docs/api.md:契约变化,并在变更记录表补一行
   - AGENTS.md:命令、目录结构、约定如有变化
   - 重大技术决策 → docs/decisions/ 新增 ADR(复制 0000-adr-template.md)
3. 实现与 plan 的偏离处,在 spec.md 末尾补「实现偏差」一节(一句话/条即可)。
4. 跨应用需求:提醒用户回填 hub 总 spec 的影响面表格与状态;依赖关系变化则更新 hub registry/services.yaml。hub 定位:`.vibe-hub` 文件 → `$VIBE_HUB` 环境变量 → 对话上下文 → **询问用户**;不要猜,**禁止为定位 hub 而 clone 任何仓库**。若需核对其它涉及服务的实现进度,先在 hub 跑 `python3 scripts/vibe-paths.py resolve <对端 service-id>` 取本地路径(见 `docs/local-paths.md`,未映射则询问用户)。
5. 遵循 hub `docs/doc-style.md` 写作规范;输出变更摘要,确认后提交文档改动:`docs: finalize NNN-xxx`,并更新本地基线 `git rev-parse HEAD > docs/.sync-commit`(该文件已被 .gitignore 忽略,不入库)。

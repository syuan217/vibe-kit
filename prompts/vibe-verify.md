# vibe-verify — 实现与方案一致性核对

> 用法:`/vibe-build` 完成后、提交 PR 前,对任意 AI 工具说"按 prompts/vibe-verify.md 核对实现"。
> (本文件由 `scripts/sync-prompts.py` 从 `plugin/skills/vibe-verify/SKILL.md` 生成,勿手改)

需求工作流的**阶段 3**:vibe-build 完成后、提交 PR 前,核对实现是否忠实于 blueprint,以及代码是否符合规范。这是传统「实现完即收尾」流程里缺失的校验环——在提交 PR 前先自检,而不是把问题留给评审者。

## 前置:确认评审引擎可用

本阶段调用 **code-review**(mattpocock/skills,英文 skill,外部依赖)做两轴并行评审。它跑两个互不污染上下文的 sub-agent:

- **Spec 轴**:实现是否忠实原始 spec/PRD——找缺失需求、范围蔓延、错误实现。本流程里,Spec 轴的输入固定为 `specs/NNN-需求名/blueprint.md`。
- **Standards 轴**:代码是否符合仓库编码规范——找 CODING_STANDARDS/CONTRIBUTING 或 constitution,加 Fowler 代码异味基线(每个异味是启发式而非硬违规,仓库规范优先)。

若 code-review 不可用:提示用户运行 `npx skills add mattpocock/skills -a <当前 agent>`。不要在缺引擎时跳过核对直接放行——这一步正是为了在提交 PR 前发现问题。

## 步骤

1. **定固定点**:与用户确认本次评审的基线(commit / branch / tag / merge-base)。code-review 会用 `git diff <固定点>...HEAD` 三点语法取 diff,先校验引用有效、diff 非空。
2. **指明 spec 来源**:把 `specs/NNN-需求名/blueprint.md` 作为 Spec 轴的原始方案交给 code-review。若 blueprint 里有「实现偏差」记录(vibe-build 留的),一并告知评审,让它判断偏差是否可接受。
3. **指明规范来源**:Standards 轴会找仓库的 CODING_STANDARDS/CONTRIBUTING 与 `docs/constitution.md`(团队宪法基线)。若本仓库有额外规范文档,告知评审。
4. **运行 code-review 两轴并行**:让两个 sub-agent 分别跑,结果**分开汇报、不合并**——一个改动可能通过一轴、失败另一轴(符合规范但偏离需求,或实现需求但代码烂),合并会互相掩盖。
5. **处理结果**:
   - **Spec 轴问题**(缺失/蔓延/错误):原则上要修;若属合理偏离,在 `spec.md`「实现偏差」节补记理由。修完重跑该轴。
   - **Standards 轴问题**(异味/违规):逐条评估,该重构重构;启发式异味不是硬违规,结合仓库实际判断。
6. **收尾提醒**(必做):核对通过后,**提醒用户时序**——现在可以提交 PR;**finalize-feature 的正确时机是 PR 评审通过、合并前**(不是现在)。理由:finalize 把过程产物蒸馏成长期文档,代码没经评审定稿就沉淀,评审返工会让文档失真。verify 通过是"可以提 PR"的信号,不是"可以沉淀文档"的信号。

## 不做什么

- 不替用户跳过两轴中的任何一个(它们故意分离,互相校验)。
- 不在本次直接跑 finalize-feature(时序不对,见步骤 6)。
- 不把异味当硬违规强制全部修(启发式,按实际判断)。

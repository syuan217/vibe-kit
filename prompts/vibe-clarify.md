# vibe-clarify — 需求澄清与方案(blueprint)

> 用法:对任意 AI 工具说"按 prompts/vibe-clarify.md 起草需求 <需求描述>"(单应用直接启动;跨应用由 cross-app-spec 启动指令带入)。
> (本文件由 `scripts/sync-prompts.py` 从 `plugin/skills/vibe-clarify/SKILL.md` 生成,勿手改)

需求工作流的**阶段 1**:把一个模糊需求变成「人能读懂的需求说明 + AI 能执行的方案」。在一个阶段内完成需求起草、逐个澄清、方案定稿——三件事一气呵成,且澄清可读性远高于「一次性甩一堆结构化问题」。

**产物分两类,各居其位**:
- `requirement.md` —— 给**人**读:意图、背景、用户故事、验收场景。团队评审对象。
- `blueprint.md` —— 给 **AI** 执行:技术方案、数据模型、契约、任务清单、检查点。结构化但措辞向"可读"妥协,不要写成可直接粘贴的代码。
- `open-questions.md` —— 澄清留痕:已决决策 + 仍待定项。

## 前置:确认澄清引擎可用

本阶段调用 **grill-with-docs**(mattpocock/skills,英文 skill)做逐个澄清。它是一次性把问题甩一堆、人读不懂的反面——**一次只问一个问题,每个都给推荐答案,能查到的事实去查、决策才问人**。

若当前 agent 未安装 mattpocock skills(grill-with-docs 不可用):提示用户运行 `npx skills add mattpocock/skills -a <当前 agent>`(常见 agent:claude-code / codex / cursor / zcode / kimi-code-cli),装好后再继续;不要在缺引擎的情况下硬走澄清(会退回"一次甩一堆问题"的旧毛病)。grill-with-docs 不在 vibe-kit 插件包内,是外部依赖,详见 hub `WORKFLOW.md`「引擎层依赖」。

## 步骤

1. **建需求骨架**:在当前仓库 `specs/` 下建 `NNN-需求名/`(NNN 取现有最大编号 +1,三位数),从 `specs/_template/` 复制三个骨架(`requirement.md`、`blueprint.md`、`open-questions.md`)到该目录;再建 `spec.md`,只填头部元数据(状态 `draft`、发起人、日期、需求来源)与「需求概述」一节占位。**跨应用需求**:启动指令会带总 spec 链接,本服务的子 `spec.md` **首行必须引用总 spec 链接**;单应用需求无此引用。
2. **起草 `requirement.md`(给人读)**:按骨架章节填写——要解决什么问题(what/why,不谈技术)、谁是用户、典型场景、验收场景(用户视角)、范围边界。这是团队评审的对象,优先让人看懂,不堆术语。
3. **承接上级下放的问题(跨应用专属)**:检查启动指令是否带「需在本服务 clarify 阶段定的问题」清单。
   - **若有**:这份清单是 grill-with-docs 的**强制输入**——这些是上级 cross-app-spec 明确下放、必须在本服务有结论的问题。把它们作为拷问的**第一批必答项**,逐个拷问到有结论(参照下方第 4 步的拷问方式),结论写进 `open-questions.md` 并标注来源「上级下放」。
   - grill-with-docs 本身的决策树拷问在此基础上**补充**发现新问题,标注来源「拷问发现」。
   - **不要**只把 requirement.md 丢给 grill-with-docs 就不管——它不会自动感知这份预定义清单,下放问题会被漏掉。
4. **逐个澄清(调 grill-with-docs)**:以 requirement.md(及第 3 步的下放清单)为拷问对象,运行 grill-with-docs。它的四条铁律正是可读性的保障,严格遵守不要绕过:
   - **一次只问一个问题**,等用户回答再问下一个(严禁一次甩一堆)。
   - **每个问题给出你的推荐答案**,用户只需确认或修正,不必从零思考。
   - **能查到的事实去查**(读代码、读 docs/、读 registry、跑命令),不要问;**决策才问人**。
   - **遍历决策树**,系统化覆盖,不要漏分支。
   每个已解决的决策写进 `open-questions.md`(问题 / 结论 / 理由);仍答不了的也写进去,注明「由谁定 / 何时定」——**不要替用户拍板**,留待定比写错答案更安全。
5. **产出 `blueprint.md`(给 AI 执行)**:基于澄清结果写技术方案。结构化但不堆代码:技术选型与理由、数据模型、对外契约(变更标注兼容/破坏性)、**任务清单**(垂直切片,每片可独立实现+验证)、每任务的验收检查点。措辞目标是"AI 读完能动手",不是"可直接粘贴"。
6. **收尾**:把 `spec.md` 状态保持 `draft`(待 vibe-build/vibe-verify 完成后才推进)。提醒用户:blueprint 定稿后即可进入 `/vibe-build`(阶段 2)。对外契约有变更的,提示同步 hub `registry/services.yaml`(若跨应用,契约评审已在总 spec 完成)。

## 不做什么

- 不写代码、不创建分支以外的工作树改动(分支可在此步建:默认 `NNN-需求名`)。
- 不替用户回答决策性问题——给推荐答案,等确认。
- 不把 blueprint 写成代码块堆砌——它是方案说明,实现留给 vibe-build。

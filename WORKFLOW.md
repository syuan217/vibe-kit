# vibe-kit 工作流方案

> 面向多仓库(polyrepo)微服务团队的 spec-driven vibe coding 工作流。
> 团队成员可使用不同 AI 编码工具(Claude Code / Cursor / Codex 等),文档与流程保持统一。

## 0. TL;DR

- **vibe-kit 本仓库是 hub(中心仓库)**:存放服务注册表、跨应用 spec、公共文档、团队宪法基线、应用仓库模板。
- **每个应用仓库通过 `scripts/vibe-init.sh` 初始化**:获得 spec-kit 工作流 + 统一的 `AGENTS.md` 文档结构。
- **AGENTS.md 是所有 AI 工具的统一上下文入口**(跨工具开放标准,30+ 工具原生支持),一份文件服务所有工具。
- **跨应用需求先在 hub 立总 spec,拆分后各仓库走 spec-kit 流程**,契约先于实现。
- **文档失职有三道防线**:宪法约束(流程内建)→ PR/CI 卡点 → `prompts/sync-docs.md` 一键补齐。

## 1. 总体架构

```
┌─────────────────────  vibe-kit (hub 仓库)  ─────────────────────┐
│  registry/services.yaml   服务清单 + 依赖关系 + 文档指针          │
│  specs/                   跨应用需求总 spec                      │
│  docs/                    公共文档(总体架构、团队约定)           │
│  templates/               应用仓库脚手架(AGENTS.md、CI、宪法基线)│
│  prompts/                 sync-docs / vibe-init-docs 等文档 prompt│
│  scripts/vibe-init.sh     应用仓库初始化脚本                     │
└──────────────┬──────────────────┬──────────────────┬───────────┘
               │ bootstrap        │ bootstrap        │ bootstrap
        ┌──────▼──────┐    ┌──────▼──────┐    ┌──────▼──────┐
        │ app-a 仓库   │    │ app-b 仓库   │    │ app-c 仓库   │
        │ AGENTS.md   │    │ AGENTS.md   │    │ AGENTS.md   │
        │ docs/       │    │ docs/       │    │ docs/       │
        │ specs/      │    │ specs/      │    │ specs/      │
        │ .specify/   │    │ .specify/   │    │ .specify/   │
        └─────────────┘    └─────────────┘    └─────────────┘
```

每个应用的文档随代码入库(你选择的方案),hub 只存公共部分与"指针"(registry),避免两处维护同一信息。

## 2. 痛点 → 解决机制

### 2.1 痛点一:不同 AI 工具下文档统一

**机制:AGENTS.md 单一入口 + 固定文档结构。**

- `AGENTS.md` 是跨工具开放标准(Linux 基金会 Agentic AI Foundation 托管),Cursor、Codex、Copilot、Windsurf 等 30+ 工具原生读取,Claude Code 现在也直接读取。**只维护这一份**,模板中保留一行式 `CLAUDE.md`(`@AGENTS.md`)仅为兼容旧版 Claude Code。
- AGENTS.md 保持精简(≤150 行):概览、技术栈、命令、约定、文档地图。深度内容放 `docs/`,AI 按需读取——这比一个巨型文件对所有工具都更有效。
- 文档分三层:**AGENTS.md**(入口层)→ **docs/**(结构层:architecture/api/decisions)→ **docs/wiki/**(定位层:code-map 功能→代码定位表 + 模块页含"常见修改场景")。定位层让 AI 改代码前查表即达,免去每次全库搜索;首次用 `prompts/rebuild-wiki.md` 从代码生成,之后随需求收尾增量维护。
- spec-kit 初始化时对每个团队用到的 agent 各执行一次 `specify init . --force --integration <agent>`,`.specify/`(模板、脚本、constitution)是共享核心,各 agent 的命令目录(`.claude/commands/`、`.cursor/` 等)**全部提交入库**——任何同事克隆仓库即获得同一套 `/speckit.*` 命令。

### 2.2 痛点二:多应用关联需求

**机制:hub 总 spec + 服务注册表 + 契约优先。**

- `registry/services.yaml` 是全系统唯一权威的服务清单:每个服务的仓库地址、负责人、上下游依赖、契约文档指针。AI 工具处理跨应用需求时先读它,即可知道"改 A 会影响谁"。
- **registry 维护机制**(详见 `registry/README.md`):只声明 `depends_on`,消费方由脚本反推;三个声明式更新时机(vibe-init 接入登记、finalize-feature 依赖变化时更新、cross-app-spec 立项时校对)+ CI 自动校验(`scripts/registry-check.py`:引用完整性、字段合法性,合入后自动重生成依赖图)+ 定期用 `registry-sync` 从代码反推真实依赖校准声明。
- 跨应用需求流程:先在 hub `specs/NNN-需求名/spec.md` 立**总 spec**(需求概述、影响面、契约变更、各服务职责拆分、上线顺序),再到各应用仓库 `/speckit.specify` 建**子 spec** 并回链总 spec。总 spec 的"影响面"表格反向链接所有子 spec,双向可追溯。
- **契约先于实现**:跨服务接口(API/消息/事件)在总 spec 的契约章节先定稿,提供方与消费方并行开发;上线顺序在总 spec 中明确(通常先发提供方)。

### 2.3 痛点三:文档未及时维护 / 文档在本地

**机制:三道防线,前两道防止、第三道兜底修复。**

1. **流程内建**(宪法约束):`templates/constitution-base.md` 规定"任务完成定义包含文档更新"、"文档唯一权威来源是 git 仓库"。spec-kit 各阶段都读 constitution,AI 在 implement 阶段会自动把文档更新纳入任务。
2. **PR/CI 卡点**:PR 模板含文档 checklist;CI(`doc-freshness.yml`)检测"源码变了但 docs/、AGENTS.md、specs/ 都没动"并发出警告(试用期用 warning,推广稳定后可改为 fail)。
3. **兜底修复**:`prompts/sync-docs.md`——任何人用任何 AI 工具说"按 prompts/sync-docs.md 执行",即可扫描上次文档更新以来的代码变更,反推补齐文档。即使有人漏了,下一个人一条命令修复,文档债不会滚雪球。对完全没有文档的存量仓库,用 `prompts/vibe-init-docs.md` 从代码反向生成整套文档。

文档生成覆盖完整生命周期,四个 prompt/规范各管一段:`vibe-init-docs`(存量仓库初始生成)→ `finalize-feature`(每个需求完成后把 spec 结论沉淀进 docs/,spec 是过程产物、docs 才是长期真相)→ `sync-docs`(日常失真修复);`docs/doc-style.md` 是统一写作规范,保证不同人、不同 AI 工具生成的文档质量一致。

因为文档全部在 git 里随 PR 走,"文档在某人本地"这一情况从结构上被消除。

### 2.4 痛点四:团队工作流统一

**机制:spec-kit 标准流程 + 分层 constitution。**

- 统一流程:`/speckit.specify → /speckit.clarify → /speckit.plan → /speckit.tasks → /speckit.implement`(clarify 强烈建议不跳过,可显著减少返工;需要时加 `/speckit.analyze` 做一致性检查)。
- constitution 分层:**团队基线**(hub 维护,bootstrap 时注入,条款不得删改)+ **应用级补充**(各仓库 `/speckit.constitution` 追加)。团队规范改一处,新应用自动继承。
- 后续团队定制(统一 spec 模板措辞、强制安全评审门禁等)可打包为 spec-kit **preset** 分发,应用仓库 `specify preset add` 即可套用——这是官方支持的组织级定制机制。

## 3. 端到端开发流程

> 给团队成员的详细操作手册(每步做什么、说什么、谁负责、常见情况处理)见 **`docs/requirement-playbook.md`**,以下为流程概要。

**单应用需求:**

1. 在应用仓库:`/speckit.specify <需求描述>`(自动建分支与 `specs/NNN-xxx/spec.md`)
2. `/speckit.clarify` 澄清 → `/speckit.plan <技术选型>` → `/speckit.tasks` → `/speckit.implement`
3. 合 PR 前按 `prompts/finalize-feature.md` 收尾:把本次 spec 的结论(架构/契约/决策变化)沉淀进 docs/,重大决策落 ADR
4. 提 PR → CI doc-freshness 检查 → 评审合入

**跨应用需求:**

1. 在 hub 仓库:复制 `specs/_template/` 建总 spec,写清需求、影响面、契约变更、职责拆分、上线顺序(可让 AI 读 `registry/services.yaml` 辅助分析影响面)
2. 契约章节评审定稿(涉及服务的 owner 确认)
3. 各应用仓库分别走"单应用需求"流程,子 spec 首行引用总 spec 链接
4. 各仓库完成后回填总 spec 状态表;按总 spec 的上线顺序发布
5. 若依赖关系变化,更新 `registry/services.yaml`

## 4. 目录结构

**hub(本仓库):** 见 README.md。

**应用仓库 bootstrap 后新增:**

```
AGENTS.md                    # AI 统一上下文入口(唯一需要维护的工具文档)
CLAUDE.md                    # 一行引用,仅兼容旧版 Claude Code
README.md                    # 给人看的入口(指向 AGENTS.md 与 docs/)
docs/architecture.md         # 架构与模块
docs/api.md                  # 对外契约
docs/decisions/              # 架构决策记录(ADR)
docs/wiki/                   # 代码定位层:code-map.md + modules/ 模块页
prompts/rebuild-wiki.md      # 从代码生成/重建 wiki
prompts/finalize-feature.md  # 需求完成后沉淀文档(含 wiki 增量)
prompts/sync-docs.md         # 文档补齐流程
.specify/                    # spec-kit 核心(模板/脚本/constitution)
.claude/ .cursor/ .codex/    # 各 agent 命令目录(全部入库)
specs/                       # 本应用需求 spec(spec-kit 产物)
.github/PULL_REQUEST_TEMPLATE.md
.github/workflows/doc-freshness.yml
```

## 5. 试用与推广路径

1. **本周(个人)**:挑一个你自己的应用仓库跑 `vibe-init.sh`,用一个真实小需求走完整流程;在 registry 登记 2-3 个真实服务。
2. **验证跨应用**:挑一个涉及 2 个服务的真实需求,在 hub 走一次总 spec → 子 spec 流程,检验模板是否顺手,随手修模板。
3. **推广前**:把 hub 推到团队 git;写一页 onboarding(可直接用 README);找 1-2 个同事(最好用不同 AI 工具)试点一个迭代。
4. **推广后**:CI 检查由 warning 改为 fail;考虑把团队定制打包为 spec-kit preset;registry 增加 CI 校验(yaml 合法性、依赖引用存在性)。

## 6. 补充建议(超出你提出的四点)

- **契约优先**是跨应用协作的核心,建议逐步把对外接口沉淀为 OpenAPI/proto 文件放各仓库 `docs/`,registry 指向它——机器可读的契约对 AI 的价值远高于散文描述。
- **kit 版本化**:应用 bootstrap 时写入 `.vibe-kit-version`,将来 kit 升级可知道哪些仓库落后。
- **AI 文档写作原则**:给 AI 的文档要短、结构化、指针化;"一个入口 + 按需深入"胜过"一个大而全"。
- **非开发同事看文档**的需求出现时,再考虑从 git 单向同步到飞书/Confluence(脚本或 CI 完成),始终保持 git 为唯一权威、平台只读。

## 附:方案依据

- spec-kit 官方(v0.10,`/speckit.*` 命令、多 agent init、extensions/presets):https://github.com/github/spec-kit
- AGENTS.md 标准与各工具支持现状:https://benjamincrozat.com/agents-md 、https://www.morphllm.com/agents-md-guide
- spec-kit 工作流实践:https://developer.microsoft.com/blog/spec-driven-development-spec-kit/

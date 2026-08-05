# Changelog

本文件记录 vibe-kit 所有版本的变更。由 `scripts/vibe-release.py` 起草,人工校对。

格式参考 [keepachangelog.com](https://keepachangelog.com/),遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [Unreleased]

## [1.2.1] - 2026-08-05

补丁版,修复 finalize-feature skill 在严格 YAML 解析器下加载缺失的问题,并加固 frontmatter 校验。无工作流逻辑变更。

### Fixed

- **finalize-feature skill 加载缺失**:`plugin/skills/finalize-feature/SKILL.md` 的 `description` 是未加引号的 plain scalar,值体里含两处 `: `(`specs/NNN-xxx: requirement.md`、`actual best timing: PR reviewed & approved`)。严格 YAML 解析器(如 Kimi Code)把第二处冒号当作新的 mapping key,抛 `mapping values are not allowed here`,整行被丢 → 该 skill 在这些工具里加载后缺席(v1.2.0 声明 10 个,实际只见 9 个)。宽松解析器(如 zcode)能整行当字符串吃下去,所以并非所有工具都复现,掩盖了问题。修复:给 `description` 加单引号包裹,值体原样保留。
- **frontmatter 校验加固**:`scripts/vibe-release.py check` 此前用正则 `^(name|description):\s*(.+)$` 提取 frontmatter 字段,对非法 YAML 照样匹配成功,无法兜住本次 bug。改为 `yaml.safe_load` 真解析:解析失败时报「SKILL.md frontmatter 不是合法 YAML」并指明行号。`tests/test_vibe_release.py` 补回归测试 `test_skill_frontmatter_invalid_yaml_detected`。

## [1.2.0] - 2026-07-31

移除 spec-kit,自建 3 阶段需求工作流。设计与逐文件核对基准见 `docs/v1.2.0-plan-spec-kit-removal.md`。

动因是试用后的两个痛点:spec-kit 的 plan/tasks 高度结构化、接近代码,优化的是"AI 可执行性"而非"人可读性",团队评审困难;`/speckit.clarify` 一次性甩一堆结构化问题,人读不懂问题意图。澄清与评审这两件事本身是有成熟做法的,只是 spec-kit 的实现不合用——所以流程层自建、引擎层外挂。

### Removed

- **spec-kit 整体移除**:`specify` CLI 的检测/安装/多 agent init 循环、`.specify/` 目录、`/speckit.*` 命令链、`--integrations` 参数、preset 相关叙述全部退出。`scripts/vibe-init.sh` 因此从"装 CLI + 跑 N 次 init + 拷模板"简化为"拷模板 + 注入宪法 + 记标记"。

### Added

- **需求工作流三阶段 skill**(`vibe-clarify` / `vibe-build` / `vibe-verify`,skill 数 7 → 10)。三者接住 spec-kit 原来的 specify/clarify/plan/tasks/implement,并补上一个它没有的环节:
  - `vibe-clarify`(阶段1)—— 自建 `specs/NNN-需求名/` 骨架,起草 `requirement.md`(给人读)、调 grill-with-docs 逐个澄清、产出 `blueprint.md`(给 AI 执行)与 `open-questions.md`(留痕)。**两类产物分居**是可读性的关键:评审看 requirement,执行读 blueprint,不再用一份文档同时讨好两种读者。
  - `vibe-build`(阶段2)—— 按 blueprint 任务清单垂直切片逐个实现,有单测能力的变更走 tdd(红→绿),偏离 blueprint 处记进 `spec.md`「实现偏差」。
  - `vibe-verify`(阶段3)—— 传统「实现完即收尾」流程缺失的校验环。调 code-review 两轴**并行且不合并**评审:Spec 轴核对实现是否忠实 blueprint,Standards 轴核对编码规范。不合并是有意的——一个改动可能符合规范但偏离需求,或实现了需求但代码烂,合并会互相掩盖。
- **需求文档骨架** `specs/_template/`(`requirement.md` / `blueprint.md` / `open-questions.md`),随 vibe-init 拷入应用仓库并**入库**,是 `specs/` 整体不入库的唯一例外——它是工具不是过程产物,入库让队友克隆即可用。gitignore 写法必须是 `specs/*` + `!specs/_template/`:git 不下降进被整体排除的目录,写成 `specs/` 会让负规则静默失效。
- `WORKFLOW.md` §1.2「引擎层依赖」、`plugin/templates/app/AGENTS.md`「前置依赖」段:说明引擎装什么、怎么装、不装会怎样。
- `scripts/vibe-release.py check` 新增 **AGENTS.md skill 名册校验**(名册与 `plugin/skills/` 实际目录按集合比对)。数字类漂移只报 warning(bump 能自动修),名册报 error——bump 修不了名册,warning 会被无视,而名单错比数字错有害:AI 读 AGENTS.md 会以为某个 skill 不存在。`fix_skill_count_in_docs` 的扫描范围同步加上 `AGENTS.md`(此前只扫 README/plugin-README/USAGE,这正是本轮 review 发现「7 个 skills」漏改的原因)。

### Changed

- **澄清/评审引擎改为外部依赖**:grill-with-docs(及同源的 grilling/grill-me)、code-review、tdd 来自 [mattpocock/skills](https://github.com/mattpocock/skills),各应用仓库经 vercel-labs/skills 生态 `npx skills add mattpocock/skills -a <agent>` 安装。**不拷贝、不 submodule**——保持上游同步,英文原装不本地化。流程层 skill 正文只**调用**引擎名,不打包它们;引擎缺失时 vibe-clarify/vibe-verify 会提示安装而非静默降级回"一次甩一堆问题"。
- **动词链全仓库替换**:`/speckit.specify → clarify → plan → tasks → implement` 改为 `/vibe-clarify → /vibe-build → /vibe-verify`。涉及 `cross-app-spec` 生成的启动指令、`plugin/templates/app/AGENTS.md`、`WORKFLOW.md`、`docs/requirement-playbook.md`、`specs/README.md`、`specs/_template/spec.md`、`plugin/USAGE.md`。
- **跨应用下放问题成为 grill-with-docs 的强制输入**:grill-with-docs 是主动发现问题的拷问引擎,不会自动感知 cross-app-spec 下放的预定义清单。`vibe-clarify` 步骤 3 显式处理——检查启动指令是否带清单、有则作为第一批必答项逐个拷问到结论、决策树拷问在此基础上补充发现,两类问题都进 `open-questions.md` 并标注来源(上级下放 / 拷问发现)。不这样做,下放的问题会被静默漏掉。
- **finalize-feature 时序修正**:从「`/speckit.implement` 完成后」改为「**PR 评审通过、合并前**」。`/vibe-verify` 通过只代表"可以提 PR",不是"可以沉淀文档"——代码没经评审定稿就沉淀,评审返工会让文档失真。skill 触发语、`docs/doc-style.md`、`docs/requirement-playbook.md`、`plugin/USAGE.md` 同步。
- **团队宪法落地路径**:`.specify/memory/constitution.md` → **`docs/constitution.md`**(入库、团队可见、随 PR 走)。应用级补充原则从 `/speckit.constitution` 改为直接编辑该文件。`plugin/templates/constitution-base.md` 第 5、6 条改写为 vibe-clarify 流程措辞。
- **同源范围扩容**:三处同源(skill + `prompts/` + `plugin/templates/app/prompts/`)从 3 个增至 6 个,新增 vibe-clarify/vibe-build/vibe-verify——它们在应用仓库日常执行,三类用户都需要。`scripts/sync-prompts.py` 的 `SYNCED` 与 `APP_COPIES` 同步。
- 四份清单的 keywords `spec-kit` → `agent-skills`(`kimi.plugin.json`、`plugin/.claude-plugin/plugin.json`、`plugin/.kimi-plugin/plugin.json`、`.claude-plugin/marketplace.json`);marketplace 名册与三处「N 个 skills」更新为 10。
- `plugin/templates/app/gitignore`:移除 `.specify/`;agent 命令目录的注释从"各自由 vibe-init 重新生成"改为"各工具自己管理"(vibe-init 不再生成它们)。
- `plugin/templates/app/.github/workflows/doc-freshness.yml`:排除列表移除 `\.specify/`。

## [1.1.0] - 2026-07-27

### Added

- **Kimi Code 平台支持**:新增 `plugin/.kimi-plugin/plugin.json`(随 `.plugin` 包分发)与仓库根 `kimi.plugin.json`(`/plugins install https://github.com/syuan217/vibe-kit` 的入口清单,指向 `./plugin/skills/`)两份 Kimi 原生清单,与 `.claude-plugin/`、`.zcode-plugin/` 同源,skill 内容三平台同一份。安装后 `/reload` 生效,`/skill:<name>` 可显式调用。
- `tests/test_vibe_release.py` 新增 kimi 清单用例(name 与 claude 清单一致性、两处 `skills` 路径声明缺失),`make_kit` fixture 同步造两份 kimi 清单。

### Changed

- 版本号同步点从 5 处扩展为 **7 处**(新增 `plugin/.kimi-plugin/plugin.json` 与根 `kimi.plugin.json`),`scripts/vibe-release.py` 的 check/bump 同步纳入;check 另校验 kimi 清单 name 一致性与 `"skills"` 声明(plugin 内须为 `./skills/`、根清单须为 `./plugin/skills/`)。
- `vibe-init` skill 读插件版本号的清单候选加入 `.kimi-plugin/plugin.json`(Kimi Code 安装时前两份 claude/zcode 清单同样存在,行为不变)。
- `README.md`、`plugin/USAGE.md`、`plugin/README.md` 补 Kimi Code 安装/升级说明(离线方式为解压后 `/plugins install <目录>`,与拖入式不同);`AGENTS.md` 硬性约定 #2 更新为七处版本号同步。

## [1.0.0] - 2026-07-25

### Added

- `LICENSE`(MIT),README 增加 License 小节。
- `plugin/USAGE.md` 补三块内容:§三 开头的 **skill 速查表**(在哪执行 / 要不要 hub / 频率,不用翻 7 张表);§四「**登记本服务**」——接入后第一件事,给可直接抄的 registry 条目与四个最容易做错的点(附校验通过的真实 YAML);§七「**报错怎么办**」——PyYAML 缺失、hub 找不到、schema v3 迁移、boundary 必填、依赖图过期、副本漂移、doc-freshness 告警等 9 条症状→处置。历史版本升级步骤收进 §八,不再混在 FAQ 里。
- `scripts/sync-prompts.py`:prompt 同源副本从"手工同步"升级为生成机制——`plugin/skills/<name>/SKILL.md` 是唯一源,`--write` 生成 6 个 `prompts/` 副本与 3 个应用模板副本,`--check` 接入 CI 防漂移(副本带"勿手改"标注)。skill 正文统一为渠道中立写法(执行时路径)。
- 测试 9 → 38:新增 `tests/test_vibe_paths.py`(hub 参数剥离、remote 归一化、拼错子命令)、`tests/test_sync_prompts.py`(副本同源)与 `tests/test_vibe_release.py`(版本漂移、清单合法性、skill 名册与 frontmatter),`conftest.py` 增 `make_kit` fixture 与 `run_paths`/`run_release` 辅助函数;registry 测试覆盖 v3 迁移守卫、via 值域、boundary 必填、contract 指针四类写法。

### Changed

- **registry schema v2 → v3(破坏性):facade 从接口级折叠为服务级**。取消顶层 `facades[]`,RPC 调用并入 `services[].depends_on`,`via` 值域放开为 `REST`/`DB`/`Dubbo`/`SOFA`/`gRPC`/`Feign`(MQ 仍归 `topics[]`,关系单一来源不变)。理由:需求澄清阶段只需知道"哪些服务被牵涉、各自负责什么",接口留到实施阶段读代码发现;`order → user-facade → user-service` 与 `order → user-service` 圈出的服务集合完全一样,而一个服务常暴露多个 facade,维护量是数倍。附带收益:`facades[].called_by` 是接口 owner 不自知的**反向边**,折叠后变成调用方自知、且能被构建坐标硬验证的出边。`topics[]` 保留(topic 名承载业务语义,且是 producer/consumer 的天然 join key)。
- **`contract` 指针有了明确规范并接入校验**:此前格式只在示例里出现过、从未写进规范,且 `depends_on[].contract` **完全没有校验**(v2 的 `facades[].contract` 本有 WARN,折叠时漏补)。现在明确:contract 记的是「去哪儿看契约」而非契约本身,格式 `<service-id>:<该仓库内相对路径>`(可带 `#锚点`,也允许 http(s) URL 指向外部 API 门户);前缀必须是**契约提供方**(`depends_on` 指对端、`topics[]` 指 owner)。缺失 / 裸路径无前缀 / 前缀指错服务,三种情况各报 WARN。`registry/README.md` 新增「contract 指针写什么」一节说明格式、三条规则、目标文档该有什么内容、以及 AI 如何顺着它跨仓库取文件。
- **`boundary` 升为必填并接入校验**:关系表只圈范围,"哪些事归 A、哪些归 B"全靠它——facade 拿掉后它是唯一还能表达"这个服务对外负责什么"的字段。`registry-check.py` 缺失报 ERROR;只写"负责什么"、漏了"不负责:……(归 <service-id>)"那半句时报 WARN(派活时 AI 就是靠后半句避免把活派错服务)。
- `registry-check.py`:schema `version` 强制为 3,并对 v2 遗留的顶层 `facades[]` 给出**明确的折叠办法**而非难懂的字段错误;依赖图新鲜度从 mtime 改为比对 `service-graph.md` 内嵌的 services.yaml 内容 hash(修复 git 不保留 mtime 导致的"过期"假阳性)。
- `registry-graph.py`:不再渲染 facade 节点,RPC 成为服务间一条以 `via` 为标签的边(`order -->|Dubbo| user`);生成物写入 `source-hash`;空 yaml 兜底;description 双引号转义(防 mermaid 渲染失败)。
- `cross-app-spec`:影响面分析**先问用户"最核心、关系最紧密的是哪个服务"**定种子(需求方通常清楚,比语义猜测准),说不上来才退回语义命中;扩散改为两类关系;明确"具体改哪个接口本阶段不必确定"。
- **`cross-app-spec` 新增「跨端澄清」步骤**(影响面确认后、建 spec 前)。此前 hub 阶段只做影响面推断与契约评审,没有澄清环节——而契约评审看的是"写下来的东西对不对",挖不出"没人想到要写的东西"。结果是跨服务的语义模糊(幂等归哪端、兼容怎么过渡、允许多久不一致)漏到各服务分别去问,而单个服务的 `/speckit.clarify` **结构上问不出来**:它只看得到自己那一半,两边可能给出不一致的答案,到联调才发现。新步骤的判据只有一条:**答案不同会改变一个以上服务的做法**才在 hub 问,只影响一家的下放到该服务 clarify(并在启动指令里点名)。关键约束是**允许答"不知道"**——发起人常常不是所有受影响服务的领域负责人,猜错的答案一旦写进契约,下游会当既定前提照做,比留一个开放问题更难纠正;答不了就记进新增的「待定问题」表(问题 / 影响哪些服务 / 由谁定 / 何时定 / 结论),标「契约评审前定」的必须在转 `contracts-approved` 前清掉。`specs/_template/spec.md` 加该节,启动指令模板增加"需在本服务 clarify 阶段定的问题"一栏。
- `registry-sync`:扫描结果按 `depends_on`/`topics` 两类归位,同一对端的多个接口**合并为一条依赖**;明确只扫本服务的**出边**("谁调我"由对方仓库补上)。
- **总 spec 影响面表改记「负责人 / 分支 / 状态」**:子 spec 是各仓库过程产物、`specs/` 不入库,原先填 `<repo>/specs/NNN-xxx/spec.md` 对别人是死链(`specs/_template/spec.md`、cross-app-spec skill 同步)。
- `doc-freshness.yml`(应用模板):"文档已更新"的判定去掉 `specs/`,只认 `docs/` 与 `AGENTS.md`。`specs/` 不入库时它是死条件;一旦某团队 opt-in 把 `specs/` 入库,spec-driven 分支必然带 `specs/NNN-xxx/spec.md`,判定会**恒真**、这道卡点直接失效。改后语义也更贴原意:写了 spec 不算数,把结论沉淀进长期文档才算数。
- `vibe-paths.py`:remote URL 归一化比较(`git@`/`ssh://`/`https://`/`.git` 后缀/大小写/**端口**),ssh clone 对 https registry 不再误报"不匹配";自建 GitLab 的 `ssh://git@host:2222/...` 同样识别;删除冗余条件。
- **skill 目录只留 SKILL.md**:删除 3 个 skill 下共 5 个 `references/` 模板——渠道中立化后 SKILL.md 正文已不引用它们(与 `plugin/templates/`、`specs/_template/` 逐字节重复的死文件),同时解除 AGENTS.md 里"references/ 模板需手动同步"这条负担;`vibe-release.py check` 新增 WARN 防其回潮。
- CI 收敛:`plugin-release.yml` 不再内联任何校验逻辑——版本、插件/zcode 清单、skill frontmatter 全部并入 `scripts/vibe-release.py check`(并新增「frontmatter name 须与目录名一致」),workflow 只剩 `vibe-release.py check` + `sync-prompts.py --check` 两步,与 AGENTS.md 的本地校验命令真正等价;两个 workflow 触发路径补齐 `scripts/vibe-*.py`、`scripts/sync-prompts.py`、`prompts/**`、`VERSION`、`CHANGELOG.md`、`README.md`。
- `vibe-init.sh` 的 .gitignore 合并:重跑时不再重复追加注释行(此前注释按行去重会脱离所描述的条目、糊在文件末尾,重跑一次就乱一次)。
- AGENTS.md「测试与 CI」不再复述 workflow 触发路径与测试文件清单(改为规则式描述),消除必然漂移的副本。
- `init-hub.sh`:独立 hub 补拷 `vibe-paths.py` 与 `docs/local-paths.md`(修复 hub 内 registry/README 的断链),生成的 hub README 同步补充。
- 同源副本修复 3 处语义漂移(finalize-feature 的 doc-style 要求、registry-sync 的 hub 定位优先级、cross-app-spec 的 hub 内执行说明);README 目录树补 `vibe-paths.py`、`vibe-release.py`、`cross-app-spec.md`。

### Fixed

- `vibe-release.py` 与 `vibe-paths.py` 的 `[hub目录]` 参数:此前 `find_hub()` 已识别但 `main()` 未剥离,docstring 宣称的用法实际报"未知子命令",现已可用并补测试。
- **拼错的子命令不再被静默吞掉**:两个脚本此前把"任何非子命令的首参"都当 hub 目录剥离,`vibe-paths.py lst` 会打印帮助并退出 0(看着像成功),`vibe-paths.py resolv <sid>` 则把错误指向后面的参数。现在只有**已存在的目录**才当 hub 参数,判定收敛到共用的 `hub_arg()`,子命令名册提为模块常量(此前在 vibe-paths.py 里硬编码 3 处)。
- `vibe-release.py` 版本不一致报错文案"应四处相同"→"应五处相同"。

### 迁移指引

- **hub 仓库:registry v2 → v3**。逐条把 `facades[]` 折叠进调用方的 `depends_on`,然后删掉整个 `facades[]` 段、把 `version` 改为 3:

  ```yaml
  # 改之前(v2)
  facades:
    - id: user-facade
      owner: user-service
      via: Dubbo
      contract: user-service:docs/api.md
      called_by: [order-service, report-service]

  # 改之后(v3):called_by 的每个成员各加一条 depends_on,指向该 facade 的 owner
  services:
    - id: order-service
      depends_on:
        - { id: user-service, via: Dubbo, contract: user-service:docs/api.md }
    - id: report-service
      depends_on:
        - { id: user-service, via: Dubbo, contract: user-service:docs/api.md }
  ```

  同一对端有多个 facade 时**合并成一条**(服务级粒度,`via` 相同即可合并)。改完跑:

  ```bash
  python3 scripts/registry-check.py && python3 scripts/registry-graph.py
  ```

  忘了改的话 registry-check 会直接报出折叠办法,不会让你对着字段错误猜。顺带把各服务的 `boundary` 补全——它现在是必填,也是 facade 拿掉后唯一还能表达"这个服务对外负责什么"的字段。
- **应用仓库**:无需操作。`specs/` 维持忽略、`.gitignore` 不用动;重跑 `vibe-init.sh` 只会补齐缺失的忽略条目。

## [0.8.0] - 2026-07-24

### Added

- **zcode 平台支持**:新增 `plugin/.zcode-plugin/plugin.json` 作为 zcode 原生清单(与 `.claude-plugin/plugin.json` 同源)。zcode 与 Claude Code 共享同一份 skill 内容与 marketplace,安装方式见 `README.md` / `plugin/USAGE.md`。

### Changed

- 版本号同步点从 4 处扩展为 5 处(新增 `plugin/.zcode-plugin/plugin.json`),`scripts/vibe-release.py` 的 check/bump 与 CI `plugin-release.yml` 同步纳入校验。
- `plugin/skills/vibe-init/SKILL.md` 把 Claude 专有的 `${CLAUDE_PLUGIN_ROOT}` 改为平台无关的指令式描述(「插件根目录 = SKILL.md 向上两级」),读版本号改为兼容 `.zcode-plugin/` 或 `.claude-plugin/` 任一清单。
- `AGENTS.md` 硬性约定 #2 更新为五处版本号同步;`README.md`、`plugin/USAGE.md` 补 zcode 安装说明,FAQ 把 zcode 从「其他工具用 prompts/」移入「装插件即可」。

## [0.7.0] - 2026-07-24

### Changed

- **registry schema v1 → v2(破坏性)**:`depends_on.via` 收窄为 `REST`/`DB`;MQ 关系迁移到 `topics[]`(producers/consumers)、RPC facade 迁移到 `facades[]`(owner/called_by);服务新增 `boundary` 字段。关系单一来源,服务条目不再镜像 produces/consumes/calls。
- cross-app-spec 影响面分析升级为图遍历(沿 topics/facades/depends_on 扩散),总 spec 影响面表新增「边界」「交互方式」列。
- registry-sync 扫描按 topics/facades/depends_on 三类归位,新增对外接口时提醒复核 `boundary`;finalize-feature 同步该提醒。
- registry-check / registry-graph 支持 topics/facades(图渲染六边形 topic、平行四边形 facade);新增 `tests/` 脚本测试并接入 CI。
- `registry/README.md`、`WORKFLOW.md` §2.2、`plugin/USAGE.md` 同步 v2 三类关系模型。

### 迁移指引

- 已有 registry:`version: 1 → 2`;把 `via: gRPC/Dubbo/SOFA` 的 depends_on 改写为 `facades[]` 条目、`via: MQ` 改写为 `topics[]` 条目;给各服务补 `boundary`。跑 `python3 scripts/registry-check.py` 校验。

## [0.6.0] - 2026-07-21

> **升级指南**:按身份(Claude 插件用户 / 已接入应用仓库 / hub 维护者)见 `plugin/USAGE.md` FAQ「从 0.5.0 升级到 0.6.0?」。

### Added

- 本地代码路径映射(`.vibe-paths.local.yaml` + `scripts/vibe-paths.py` 的 `list`/`add`/`check`/`resolve` 子命令):让 AI 从 hub 的 service-id 一步跳到本机 clone 的代码目录,不再停在 GitHub URL。机制见 `docs/local-paths.md`。
- 发版自动化(`scripts/vibe-release.py` 的 `check`/`bump` 两模式):扫描版本号与 skill 名册的漂移、半自动起草 CHANGELOG 条目、重打包 .plugin。
- `CHANGELOG.md`(本文件),回填 0.4.3 / 0.4.4 / 0.5.0 历史条目。

### Changed

- `registry/README.md`、`plugin/USAGE.md`、`AGENTS.md` 增补本地路径映射机制的条目与 AI 使用规则。
- cross-app-spec / registry-sync / finalize-feature 的 skill 副本(共 7 处同源)新增跨仓库跳转引导:优先 `vibe-paths.py resolve`,禁止为定位而 clone。
- CI `plugin-release.yml` 校验从 2 处扩展为 4 处(`VERSION` + `plugin.json` + `marketplace.json` 顶层 + `plugins[0]`)版本号一致。
- `scripts/registry-check.py` 与 `scripts/registry-graph.py` 加固:`find_hub()` 多级回退(命令行参数 > `$VIBE_HUB` > 当前目录 > 脚本上级目录)+ PyYAML 缺失友好提示。脚本随插件分发到应用仓库后不再依赖自身位置。

### Fixed

- 修正 `README.md` 目录树里 skills 数量漂移(6 → 7)。

## [0.5.0] - 2026-07-20

> 追溯填写。素材取自 `v0.4.4..v0.5.0` 的 git log。

### Added

- 插件**内置模板与团队宪法**(位于 `plugin/templates/`),与 hub 解耦——安装即可用,无需 clone vibe-kit 仓库。
- 加固 wiki(code-map 路径必须真实存在、符号不写行号等)。
- 仓库自身的 `AGENTS.md`:AI 统一上下文入口,含同源同步、发版等硬性约定。

## [0.4.4] - 2026-07-19

> 追溯填写。素材取自 `v0.4.3..v0.4.4` 的 git log。

### Added

- `vibe-init` 在用户确认后自动安装 spec-kit CLI,引导 `uv tool install`。

### Changed

- CI `actions/checkout` v4 → v5(Node 20 弃用)。

## [0.4.3] - 2026-07-19

> 追溯填写。素材取自 tag commit message。

### Added

- registry 依赖新增 `status: planned` / `active`(显式表达 hub 超前于应用的中间态)+ `spec` 溯源字段。
- 受控的 hub/应用文档时间差机制:planned 依赖在契约定稿时预登记、上线时转 active。

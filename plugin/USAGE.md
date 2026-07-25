# vibe-kit 插件使用说明

> 面向两类读者:**人**(如何安装、什么时候说什么)与 **AI agent**(何时自动触发、执行边界)。

## 一、这个插件是什么

vibe-kit 插件把团队 spec-driven 工作流中"文档生成与维护、跨应用协调"的能力封装为 7 个 skills。安装后,AI 会在对应场景**自动触发**相应能力,你不需要记命令、不需要粘贴 prompt。

模板与团队宪法**随插件分发**(位于插件内 `templates/`),安装即可用,无需 clone vibe-kit 仓库。插件同时支持 **Claude Code** 与 **zcode**(两平台 skill 格式兼容,同一份 `plugin/` 分发)。插件与两方协作:

```
vibe-kit 插件(装在 Claude / zcode 里,自带模板/宪法)
    │ 读 registry/总 spec         │ 生成/维护文档
    ▼                            ▼
hub 仓库(团队协调,可选)      应用仓库(你的服务)
  registry、总spec             AGENTS.md、docs/、wiki
```

## 二、安装与前置条件

**Claude Code / Cowork**(从 GitHub 安装):

```
/plugin marketplace add syuan217/vibe-kit
/plugin install vibe-kit@vibe-kit
```

**zcode**(Settings → Plugin Management → Discover,点 `+` 添加本仓库 GitHub 地址 `syuan217/vibe-kit` 作为 marketplace,然后安装 vibe-kit 插件)。

或**离线方式**(两平台通用):将 `vibe-kit.plugin` 文件拖入会话点击安装(文件可在 GitHub Release 下载)。

前置条件:

1. **spec-kit CLI**(bootstrap 时需要):`uv tool install specify-cli --from git+https://github.com/github/spec-kit.git`(vibe-init skill 会自动检查并提示)
2. **hub 目录**(可选,跨应用协调时需要):团队共享的 registry/总 spec 仓库,可用 vibe-kit 仓库的 `init-hub.sh` 创建(三种形态见 WORKFLOW.md §1.1;团队协作必须是共享 git 仓库)。应用仓库根的 `.vibe-hub` 文件记录其位置,AI 据此定位;**定位不到时 AI 会询问你,不会自行 clone 仓库**。暂无 hub 也可先接入,之后补登记
3. 应用仓库是 git 仓库

## 三、七个 Skill 详解

速查(**在哪执行**决定你要先 `cd` 到哪;**要 hub 吗**决定没配 hub 时能不能用):

| Skill | 一句话 | 在哪执行 | 要 hub 吗 | 频率 |
|---|---|---|---|---|
| vibe-init | 仓库接入工作流 | 应用仓库 | 可选(之后补登记) | 一次性 |
| vibe-init-docs | 从代码反向生成整套文档 | 应用仓库 | 否 | 一次性 |
| rebuild-wiki | 生成/重建代码定位 wiki | 应用仓库 | 否 | 首次 + 大重构后 |
| cross-app-spec | 立跨应用总 spec、定契约 | **hub** | **必须** | 每个跨应用需求 |
| finalize-feature | 需求收尾、结论沉淀进 docs/ | 应用仓库 | 否(跨应用需求时要) | **每个需求** |
| sync-docs | 文档失真时增量补齐 | 应用仓库 | 否 | 按需 |
| registry-sync | 从代码校准依赖声明 | 应用仓库 | **必须** | 每月 / 大需求后 |

日常只有 **finalize-feature** 是每个需求都要做的;其余按需触发。

### 1. vibe-init — 仓库接入

| | |
|---|---|
| 用途 | 把一个应用仓库接入 vibe-kit 工作流 |
| 什么时候用 | 新建仓库后,或存量仓库首次接入 |
| 你可以说 | "把这个仓库接入 vibe-kit" / "初始化工作流" |
| 需要提供 | hub 仓库路径(可选,没有则跳过);团队用哪些 AI 工具(默认 claude,cursor,codex) |
| 做什么 | 对每个 AI 工具跑 spec-kit init;从插件内拷贝 AGENTS.md/docs/wiki/prompts 模板;注入团队宪法;合并 .gitignore(忽略 .specify/、specs/、agent 命令目录等本地生成物);记录 kit 版本 |
| 之后 | 存量仓库紧接着跑 vibe-init-docs;去 hub registry 登记本服务;提交 AGENTS.md、docs/、prompts/ |

### 2. vibe-init-docs — 存量仓库反向生成文档

| | |
|---|---|
| 用途 | 没文档/文档严重过期的仓库,从代码反推整套文档 |
| 什么时候用 | bootstrap 之后立即,或接手一个文档烂掉的老仓库 |
| 你可以说 | "这个仓库没有文档,帮我生成" / "反向生成文档" |
| 做什么 | 通读代码,生成 AGENTS.md、architecture、api(真实契约)、wiki;推测处标 TODO(待确认) 汇总给你确认 |
| 注意 | 只写代码可证实的内容;生成后需要你抽查确认 TODO 项 |

### 3. rebuild-wiki — 生成代码定位 wiki

| | |
|---|---|
| 用途 | 生成/重建 `docs/wiki/`:code-map 功能定位表 + 模块页,让 AI 改代码前"查表即达" |
| 什么时候用 | 首次生成,或大规模重构后重建(日常增量不用它,由 finalize-feature 维护) |
| 你可以说 | "生成 wiki" / "生成代码地图" / "重建 code-map" |
| 做什么 | 按业务域划分 5~15 个模块;生成 code-map(功能→路径→符号)与模块页(关键文件、调用链、常见修改场景);逐一核对路径真实存在 |

### 4. cross-app-spec — 跨应用需求总 spec

| | |
|---|---|
| 用途 | 涉及 ≥2 个服务的需求,在 hub 立总 spec、分析影响面、先定契约 |
| 什么时候用 | 跨应用需求的**最开始**,动任何代码之前 |
| 你可以说 | "这个需求涉及订单和用户两个服务" / "建个跨应用 spec" / "帮我分析影响面" |
| 需要提供 | hub 路径;需求描述 |
| 做什么 | 先问你"最核心的是哪个服务"定种子 → 读 registry(v3:services+topics)图遍历推断影响面给你确认 → **就跨端问题澄清**(职责归属、兼容策略、失败/幂等语义、一致性、上线顺序硬约束)→ 建 spec(概述、影响面表、待定问题、契约变更、职责拆分、上线顺序)→ 为每个涉及服务生成拷贝即用的 /speckit.specify 启动指令 |
| 澄清的边界 | 只问"**答案不同会改变一个以上服务做法**"的问题——这类问题单服务的 `/speckit.clarify` 结构上问不出来。只影响一家的会被下放到该服务自己 clarify。**答不上来就留「待定问题」,别硬答**:猜错的答案写进契约后,下游会当既定前提照做 |
| 之后 | 契约经相关 owner 评审(人工闸口,不自动跳过;评审前先清掉标了"契约评审前定"的待定项)后,到各应用仓库粘贴启动指令即进入标准 spec-kit 流程 |

### 5. finalize-feature — 需求收尾沉淀

| | |
|---|---|
| 用途 | 需求做完后,把 specs/NNN 的结论沉淀进长期文档(spec 是过程产物,docs 才是长期真相) |
| 什么时候用 | `/speckit.implement` 完成后、**合 PR 前**,每个需求都要做 |
| 你可以说 | "收尾 specs/003" / "需求做完了,沉淀一下文档" |
| 做什么 | 对照 spec 与实际 diff,更新 wiki code-map/模块页、architecture、api(含变更记录)、AGENTS.md;重大决策落 ADR;偏离 plan 处在 spec 补「实现偏差」;跨应用需求提醒回填总 spec |

### 6. sync-docs — 日常文档修复

| | |
|---|---|
| 用途 | 代码变了文档没跟上(别人漏了收尾、或紧急改动没走流程)时增量补齐 |
| 什么时候用 | 发现文档失真;CI doc-freshness 告警;接手仓库前先校准一遍 |
| 你可以说 | "同步一下文档" / "文档好像过期了" / "补文档" |
| 做什么 | 找到上次文档更新点,扫描其后的代码变更,逐项修正 AGENTS.md/wiki/architecture/api;只改文档不改代码 |

### 7. registry-sync — 校准服务依赖关系

| | |
|---|---|
| 用途 | 从代码反推本服务的真实依赖(HTTP/gRPC/MQ/跨库),对比 hub registry 声明,修正失真 |
| 什么时候用 | 大需求收尾后、或每月对全部服务跑一轮;怀疑 registry 不准时 |
| 你可以说 | "校准一下依赖" / "检查这个服务的依赖关系对不对" |
| 需要提供 | hub 路径 |
| 做什么 | 扫描代码 → 按 depends_on/topics 两类报告缺失/多余/方式不符(服务级粒度,同一对端多个接口合并为一条;存疑项列证据不静默写入)→ 新增对外接口时提醒复核 boundary → 确认后更新 registry、跑校验、重生成依赖图 |

## 四、典型场景(人视角)

> 完整的需求处理手册(判断类型、每步操作、角色分工、异常情况)见 hub 仓库 `docs/requirement-playbook.md`。

**接入一个存量服务**:打开仓库 → "接入 vibe-kit"(vibe-init)→ "反向生成文档"(vibe-init-docs,含 wiki)→ 按提示去 hub 登记 registry → 提交。

**做一个单应用需求**:`/speckit.specify` → `clarify` → `plan` → `tasks` → `implement`(AI 动手前会自动查 wiki code-map 定位代码)→ "收尾一下"(finalize-feature)→ 提 PR。

**做一个跨应用需求**:"这个需求涉及 A 和 B 服务"(cross-app-spec 在 hub 立总 spec、定契约)→ owner 评审契约 → 各仓库走单应用流程 → 各自 finalize-feature → 按总 spec 顺序上线 → 回填总 spec 状态。

**发现文档不对**:"同步文档"(sync-docs)。不用追究是谁漏的,一条命令修复。

**维护服务关系(registry)**:平时不用管——vibe-init 登记、finalize-feature 随需求更新、hub CI 自动校验和重生成依赖图;每月或大需求后对各服务说"校准依赖"(registry-sync)防止声明与代码脱节。

### 登记本服务(接入后的第一件事)

在 hub 的 `registry/services.yaml` 加一条。**只记服务级关系,不记接口**——具体调哪个方法留给实施时读代码:

```yaml
  - id: order-service                 # kebab-case,与仓库名一致
    repo: https://github.com/your-org/order-service
    owner: yinn
    description: 订单核心服务
    boundary: |                       # 必填,registry 里最值钱的字段
      负责订单生命周期(创建、支付回调、状态流转)。
      不负责:库存扣减(inventory-service)、履约(fulfillment-service)。
    docs: { agents: AGENTS.md, architecture: docs/architecture.md, api: docs/api.md }
    depends_on:                       # 无依赖也要显式写 []
      - { id: user-service, via: Dubbo, contract: user-service:docs/api.md }
```

四件最容易做错的事(都会被 registry-check 警告):

1. **`boundary` 的"不负责"那半句别省** —— 跨应用需求派活时,AI 就是靠它避免把活派给错误的服务。
2. **MQ 不写 `depends_on`** —— 发布订阅关系归 `topics[]`(`producers`/`consumers`),`depends_on` 只放点对点调用(`via` 取 `REST`/`DB`/`Dubbo`/`SOFA`/`gRPC`/`Feign`)。
3. **同一个对端只写一条** —— 对方暴露 5 个 Dubbo 接口也只写一条 `via: Dubbo`。
4. **`contract` 是指针不是内容,且要指对端** —— 格式 `<service-id>:<对方仓库内路径>`(如 `user-service:docs/api.md`,可带 `#锚点`)。裸写 `docs/api.md` 说不清是哪个仓库;写成自己的 service-id 也不对——契约由**提供方**维护。registry 里永远不抄接口签名。

改完在 hub 跑:

```bash
python3 scripts/registry-check.py && python3 scripts/registry-graph.py
```

字段全集与维护规范见 hub `registry/README.md`(权威来源)。

## 五、AI Agent 使用规则

安装本插件后,agent 应遵守:

1. **自动触发,不等用户点名**:用户说出各 skill 描述中的触发语义时直接调用对应 skill;`/speckit.implement` 完成时主动建议 finalize-feature;发现文档与代码不一致时主动建议 sync-docs。
2. **定位代码先查表**:在已接入 vibe-kit 的仓库改代码前,先读 `docs/wiki/code-map.md` 与相关模块页;查不到再全库搜索,并在任务结束时把新发现补进 code-map。**跨仓库定位**(需要读对端服务代码)时,先在 hub 跑 `python3 scripts/vibe-paths.py resolve <service-id>` 取本地 clone 路径;未映射则询问用户去 `add`,**禁止为定位代码而 clone 任何仓库**;拿到本地路径后仍按本条规则读该仓库的 `docs/wiki/code-map.md` 再定位具体文件(机制见 `docs/local-paths.md`)。
3. **skill 链**:vibe-init(存量仓库)→ 建议 vibe-init-docs;vibe-init-docs → 内部调用 rebuild-wiki;cross-app-spec 完成 → 引导用户到各应用仓库走 spec-kit 流程;任何 skill 发现契约/依赖变化 → 提醒更新 hub registry 并重跑 `scripts/registry-graph.py`。
4. **hub 定位**:按优先级——应用仓库根 `.vibe-hub` 文件 → `$VIBE_HUB` 环境变量 → 对话上下文 → 问用户;不要猜。
5. **registry 是服务级粒度**:写入 registry 的关系只到"哪个服务、什么方式",**不得记接口名/方法名**;同一对端的多个接口合并为一条 `depends_on`。要表达"这个服务负责什么"用 `boundary`,不要靠罗列接口。
6. **事实边界**:文档中的路径、符号、接口必须在代码中真实存在,生成后用搜索工具核对;不确定标 `TODO(待确认)`,禁止臆造;行号永远不写入文档。
7. **确认后提交**:所有 skill 的产出先给用户变更摘要,确认后再 commit(各 skill 内规定了 commit message 格式)。
8. **只在职责内动手**:文档类 skills 只改文档不改代码;宪法基线条款不得修改。

## 六、FAQ

- **skill 没有自动触发?** 直接说 skill 名即可,如"用 sync-docs 检查一下"。
- **zcode / Claude 都支持吗?** 支持。插件根目录同时携带 `.zcode-plugin/plugin.json` 与 `.claude-plugin/plugin.json` 两份清单,skill 内容同一份。zcode 用户按 §二安装即可,与 Claude 用户体验一致。
- **Cursor / Codex 同事怎么办?** 这两个工具暂无插件市场;其用户使用应用仓库内 `prompts/*.md`(内容与插件同源),效果一致。
- **插件和 hub 里的 prompts 改了一边怎么办?** 不会只改一边:`plugin/skills/<name>/SKILL.md` 是唯一源,`prompts/` 与应用模板里的副本由 `python3 scripts/sync-prompts.py --write` 生成(CI 用 `--check` 防漂移,勿手改副本);改完重新打包分发 `.plugin`。
- **升级插件?** hub 仓库 `plugin/` 目录改完、`plugin.json`(Claude `.claude-plugin/` + zcode `.zcode-plugin/` 两处)与 `.claude-plugin/marketplace.json` 版本号同步递增、推送 GitHub 并打 tag(CI 自动发 Release);团队执行 `/plugin marketplace update vibe-kit`(Claude)或在 zcode Discover 刷新后重装即可。
- **跨版本升级要做什么?** 每个版本的手工步骤写在 `CHANGELOG.md` 对应版本的「迁移指引」一节(权威来源,不在此复述)。0.7.0 起一律查 CHANGELOG;更早的两个版本见文末「历史版本升级步骤」。

## 七、报错怎么办

| 你看到 | 原因与处理 |
|---|---|
| `缺少依赖 PyYAML,请先安装` | hub 脚本(registry-check / registry-graph / vibe-paths)只依赖这一个第三方库:`pip install pyyaml` |
| `未找到 hub(缺少 registry/services.yaml)` | 脚本按「命令行参数 → `$VIBE_HUB` → 当前目录 → 脚本上级目录」找 hub。在应用仓库里跑要传路径,或先 `export VIBE_HUB=<hub 路径>` |
| AI 反复问你 hub 在哪 | 应用仓库根缺 `.vibe-hub` 文件(个人本地配置,不入库)。重跑 `vibe-init.sh` 会写入,或手动 `echo <hub绝对路径> > .vibe-hub` |
| `schema version 必须为 3` | hub 的 registry 还是旧 schema,按 `CHANGELOG.md`「迁移指引」转换;检测到遗留 `facades[]` 时报错里直接给了折叠办法 |
| `<service>: 缺少必填字段 boundary` | v3 起 `boundary` 必填,补上"负责……/不负责……(归 <service-id>)"两句 |
| `contract 缺少 <service-id>: 前缀` / `contract 前缀是 X,应为 Y` | contract 是跨仓库指针,格式 `<对端 service-id>:<对端仓库内路径>`;契约由提供方维护,所以前缀是对端(topic 则是 owner) |
| `依赖图已过期` | `services.yaml` 改了但没重生成:`python3 scripts/registry-graph.py`(合入 main 后 CI 也会自动做) |
| `未检测到 specify CLI` | `uv tool install specify-cli --from git+https://github.com/github/spec-kit.git`;没有 uv 先 `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| CI 报 `prompt 副本与 skill 不同源` | 有人手改了 `prompts/` 下的副本。副本是生成物——改 `plugin/skills/<name>/SKILL.md`,再跑 `python3 scripts/sync-prompts.py --write` |
| doc-freshness 警告"源码变了但文档没动" | 说"需求收尾"(finalize-feature)或"同步文档"(sync-docs)。注意它只认 `docs/` 与 `AGENTS.md`——**写了 spec 不算数** |

## 八、历史版本升级步骤

- **从 0.4.x 升级到 0.5.0?** 0.5.0 起 `docs/.sync-commit`、`.vibe-hub`、`.vibe-kit-version` 改为本地文件不入库。已接入的应用仓库升级后执行一次:

  ```bash
  git rm --cached docs/.sync-commit .vibe-hub .vibe-kit-version 2>/dev/null || true
  ```

  然后重跑 vibe-init(合并新 `.gitignore` 条目,已有文件不会被覆盖),提交 `.gitignore` 与上述删除。

- **从 0.5.0 升级到 0.6.0?** 本次新增本地代码路径映射(`vibe-paths.py`)+ 发版自动化(`vibe-release.py`),以及 cross-app-spec / registry-sync / finalize-feature 的跨仓库跳转引导。按你的身份选对应步骤:

  - **Claude 插件用户**:`/plugin marketplace update vibe-kit` 后重装——所有 skill 更新自动生效(覆盖本次大部分改动)。
  - **已接入的应用仓库**:只有一个文件需要手动同步——`prompts/finalize-feature.md`(0.6.0 在步骤 4 末尾加了「跨仓库进度核对」引导)。`vibe-init.sh` 用 `cp -Rn` 不覆盖已有文件,重跑脚本**不会**刷新它,必须手动:

    ```bash
    # 在应用仓库根执行,从 vibe-kit 拷贝新版本覆盖
    cp <vibe-kit-path>/plugin/templates/app/prompts/finalize-feature.md prompts/finalize-feature.md
    git add prompts/finalize-feature.md
    git commit -m "chore: sync finalize-feature.md to vibe-kit v0.6.0"
    ```

    其余 0.6.0 改动不影响应用仓库副本:`vibe-paths.py` 与 `docs/local-paths.md` 只在 hub 跑,应用仓库不放;cross-app-spec / registry-sync 的 prompt 副本按同源规则也不进应用仓库。
  - **hub 维护者**:hub 本身已是 0.6.0,无需额外升级。可选:在 hub 根目录用 `python3 scripts/vibe-paths.py add <sid> <路径>` 登记自己机器上的服务 clone 路径,让 AI 跨仓库跳转生效(个人配置,不入库)。

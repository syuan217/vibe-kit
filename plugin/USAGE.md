# vibe-kit 插件使用说明

> 面向两类读者:**人**(如何安装、什么时候说什么)与 **AI agent**(何时自动触发、执行边界)。

## 一、这个插件是什么

vibe-kit 插件把团队 spec-driven 工作流中"文档生成与维护、跨应用协调"的能力封装为 6 个 skills。安装后,AI 会在对应场景**自动触发**相应能力,你不需要记命令、不需要粘贴 prompt。

它与两个仓库协作:

```
vibe-kit 插件(装在 Claude 里)
    │ 读模板/宪法/registry        │ 生成/维护文档
    ▼                            ▼
hub 仓库(vibe-kit)          应用仓库(你的服务)
  registry、总spec、模板        AGENTS.md、docs/、wiki、specs/
```

## 二、安装与前置条件

安装(推荐,从 GitHub):

```
/plugin marketplace add gentBai/vibe-kit
/plugin install vibe-kit@vibe-kit
```

或离线方式:将 `vibe-kit.plugin` 文件拖入 Cowork 会话点击安装(文件可在 GitHub Release 下载)。

前置条件:

1. **spec-kit CLI**(bootstrap 时需要):`uv tool install specify-cli --from git+https://github.com/github/spec-kit.git`(vibe-init skill 会自动检查并提示)
2. **hub 仓库本地 clone**:vibe-init 和 cross-app-spec 需要;首次使用时 AI 会询问 hub 路径,告诉它即可
3. 应用仓库是 git 仓库

## 三、六个 Skill 详解

### 1. vibe-init — 仓库接入

| | |
|---|---|
| 用途 | 把一个应用仓库接入 vibe-kit 工作流 |
| 什么时候用 | 新建仓库后,或存量仓库首次接入 |
| 你可以说 | "把这个仓库接入 vibe-kit" / "初始化工作流" |
| 需要提供 | hub 仓库路径;团队用哪些 AI 工具(默认 claude,cursor,codex) |
| 做什么 | 对每个 AI 工具跑 spec-kit init;拷贝 AGENTS.md/docs/wiki/prompts 模板;注入团队宪法;记录 kit 版本 |
| 之后 | 存量仓库紧接着跑 vibe-init-docs;去 hub registry 登记本服务;全部提交入库 |

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
| 做什么 | 读 registry 推断影响面给你确认;建 `specs/NNN-xxx/spec.md`(概述、影响面表、契约变更、职责拆分、上线顺序) |
| 之后 | 契约经相关 owner 评审后,各应用仓库分别走 /speckit.specify(子 spec 引用总 spec) |

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

## 四、典型场景(人视角)

**接入一个存量服务**:打开仓库 → "接入 vibe-kit"(vibe-init)→ "反向生成文档"(vibe-init-docs,含 wiki)→ 按提示去 hub 登记 registry → 提交。

**做一个单应用需求**:`/speckit.specify` → `clarify` → `plan` → `tasks` → `implement`(AI 动手前会自动查 wiki code-map 定位代码)→ "收尾一下"(finalize-feature)→ 提 PR。

**做一个跨应用需求**:"这个需求涉及 A 和 B 服务"(cross-app-spec 在 hub 立总 spec、定契约)→ owner 评审契约 → 各仓库走单应用流程 → 各自 finalize-feature → 按总 spec 顺序上线 → 回填总 spec 状态。

**发现文档不对**:"同步文档"(sync-docs)。不用追究是谁漏的,一条命令修复。

## 五、AI Agent 使用规则

安装本插件后,agent 应遵守:

1. **自动触发,不等用户点名**:用户说出各 skill 描述中的触发语义时直接调用对应 skill;`/speckit.implement` 完成时主动建议 finalize-feature;发现文档与代码不一致时主动建议 sync-docs。
2. **定位代码先查表**:在已接入 vibe-kit 的仓库改代码前,先读 `docs/wiki/code-map.md` 与相关模块页;查不到再全库搜索,并在任务结束时把新发现补进 code-map。
3. **skill 链**:vibe-init(存量仓库)→ 建议 vibe-init-docs;vibe-init-docs → 内部调用 rebuild-wiki;cross-app-spec 完成 → 引导用户到各应用仓库走 spec-kit 流程;任何 skill 发现契约/依赖变化 → 提醒更新 hub registry 并重跑 `scripts/registry-graph.py`。
4. **hub 定位**:需要 hub 时先从对话上下文找路径,找不到问用户;不要猜。
5. **事实边界**:文档中的路径、符号、接口必须在代码中真实存在,生成后用搜索工具核对;不确定标 `TODO(待确认)`,禁止臆造;行号永远不写入文档。
6. **确认后提交**:所有 skill 的产出先给用户变更摘要,确认后再 commit(各 skill 内规定了 commit message 格式)。
7. **只在职责内动手**:文档类 skills 只改文档不改代码;宪法基线条款不得修改。

## 六、FAQ

- **skill 没有自动触发?** 直接说 skill 名即可,如"用 sync-docs 检查一下"。
- **Cursor / Codex 同事怎么办?** 插件仅服务 Claude 用户;其他工具用户使用应用仓库内 `prompts/*.md`(内容与插件同源),效果一致。
- **插件和 hub 里的 prompts 改了一边怎么办?** 二者同源,修改工作流时须同步更新 `plugin/skills/` 与 hub `prompts/`、`templates/`,然后重新打包分发 `.plugin`。
- **升级插件?** hub 仓库 `plugin/` 目录改完、`plugin.json` 与 `.claude-plugin/marketplace.json` 版本号同步递增、推送 GitHub 并打 tag(CI 自动发 Release);团队执行 `/plugin marketplace update vibe-kit` 后重装即可。

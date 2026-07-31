---
name: cross-app-spec
description: Creates a cross-application master spec in the vibe-kit hub repo for requirements spanning multiple services - analyzes impact via the service registry, defines contract changes first, and splits work per service. Use when the user says "跨应用需求", "这个需求涉及多个服务", "建总 spec", "cross-app spec", or "影响面分析".
---

# cross-app-spec — 跨应用需求总 spec

适用:涉及 **2 个及以上应用**的需求(单应用需求直接在其仓库走 `/vibe-clarify`)。

## 步骤

1. 定位 hub,按优先级:当前应用仓库根 `.vibe-hub` 文件内容 → `$VIBE_HUB` 环境变量 → 对话上下文 → **询问用户**;不要猜,**禁止为定位 hub 而 clone 任何仓库**(已在 hub 仓库中执行时即当前目录)。
2. **影响面分析(图遍历)**:读 hub `registry/services.yaml`(schema v3:services + topics,关系为**服务级**,不含接口)。
   - **先定种子**:问用户「本需求最核心、关系最紧密的是哪个服务?」——需求方通常清楚,人指定比语义猜测准。用户说不上来时,才退回从需求 NL 语义命中(service / topic)。
   - **再沿两类关系扩散**:
     - 种子作为某 topic 的 **producer** → 拉该 topic 全部 `consumers`(下游影响面)
     - 种子作为某 topic 的 **consumer** → 标注该 topic 的 `producer`(可能需协调)
     - 沿 `depends_on` 双向扩散:种子调了谁(上游契约可能要改)、谁调了种子(下游会被影响)
     - 种子本身是 topic → 直接拉其 producers + consumers
   - 把推断结果给用户确认,不确定的标存疑。涉及服务若 hub `.vibe-paths.local.yaml` 有映射(见 `docs/local-paths.md`),标注「本地可直达」。**每个受影响服务据其 `boundary` 与交互角色,给一句「本需求中它要改什么」**——registry 只圈范围,分工靠 boundary。
   - 具体要改哪个接口/方法,**本阶段不必确定**,留给各服务实施时读代码发现。
3. **跨端澄清**(影响面确认后、建 spec 前):判据只有一条——**答案不同会改变一个以上服务的做法**才在此处问;只影响一家的留给该服务 `/vibe-clarify` 的 grill-with-docs 拷问(下放方式见步骤 6)。按下列几类挑真正存疑的问,不要凑数:
   - **职责归属**:这件事归 A 还是 B(两边 `boundary` 重叠、或都没覆盖时)
   - **兼容策略**:破坏性变更怎么过渡——双写/双读期、灰度、旧字段何时下线
   - **失败语义**:超时、重试、幂等、补偿由哪一端负责
   - **一致性要求**:强一致还是最终一致,允许多久不一致
   - **上线顺序硬约束**:有没有"必须先发谁"的技术性依赖

   每个问题三种归宿,**不要逼用户当场拍板**:①有答案 → 写进「契约变更」或「各服务职责拆分」;②答不了 → 记进「待定问题」表,注明**由谁、在什么阶段定**;③判断出只影响一家 → 明确下放,并在启动指令里点名让该服务 clarify。
   发起人常常不是所有受影响服务的领域负责人——**猜错的答案一旦写进契约,下游会当既定前提照做,比留一个开放问题更难纠正**。宁可留待定。
4. 在 hub `specs/` 下建 `NNN-需求名/spec.md`(NNN 取现有最大编号 +1,三位数;模板 `specs/_template/spec.md`),重点填写:
   - 需求概述(what/why,不谈实现)
   - 影响面表(服务、**边界**、**交互方式**、变更类型、负责人、分支、状态)。子 spec 是各仓库的过程产物、`specs/` 不入库,**不要填子 spec 文件路径**(对别人是死链),只记落到谁头上、哪条分支、进展如何
   - **待定问题**表(第 3 步答不了的,连同"由谁定、何时定"一起落表;没有未决项就删掉该节)
   - **契约变更**(先于实现定稿,标注兼容/破坏性)
   - 各服务职责拆分与验收标准
   - 上线顺序(通常先提供方后消费方)
5. 提醒流程:契约章节须经涉及服务的 owner 评审(状态改 `contracts-approved`)后,各应用仓库才开始实现;**评审前先过一遍「待定问题」表,标注了"契约评审前定"的必须已有结论**。子 spec 首行引用本 spec 链接,各服务开工/完成时回填影响面表的分支与状态列。**此评审是人工闸口,不要替用户跳过。**
6. **生成各服务启动指令**(拷贝即用):为每个涉及服务输出一条预填好的命令。先在 hub 跑 `python3 scripts/vibe-paths.py resolve <service-id>` 取本地 clone 路径——已映射则指令注释写成 `# 在 <绝对路径> 执行:` 并附 `cd <路径>`;未映射则保持 `# 在 <service-id> 仓库执行:` 占位,并提示用户可用 `vibe-paths.py add` 登记(机制见 `docs/local-paths.md`,禁止为定位而 clone)。指令格式:

   ```
   # 在 <本地路径或 service-id 仓库> 执行:
   /vibe-clarify 实现跨应用需求「NNN-需求名」中本服务的部分。总 spec:<hub spec 链接或路径>。本服务职责:<职责拆分章节内容摘要>。契约约束:<该服务相关的契约变更摘要>。需在本服务 clarify 阶段定的问题:<第 3 步下放给本服务的问题,没有则省略此句>。完成后回填总 spec 影响面表。
   ```

   用户在对应仓库粘贴即进入 vibe-clarify 流程(vibe-clarify → vibe-build → vibe-verify → finalize-feature);跨端问题已在总 spec 定完,vibe-clarify 会把下放问题作为 grill-with-docs 的强制输入逐个拷问到结论(见 vibe-clarify 步骤 3),本服务只需处理自己那一半。
7. 若本需求会新增/改变服务依赖:契约定稿(contracts-approved)时即在 `registry/services.yaml` 以 `status: planned` + `spec: NNN` 预登记新依赖(上线关闭需求时转 `active`),并重新生成依赖图:`python3 scripts/registry-graph.py`。

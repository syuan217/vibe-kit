# registry 拓扑模型升级 — 设计

> 日期:2026-07-24 · 状态:draft · 作者:yinn(+ AI)
> 目标读者:vibe-kit 维护者。本文是实现前的设计基线,经确认后进入 writing-plans。

## 1. 背景与问题

vibe-kit 现有 `registry/services.yaml` 只有一种关系:`A depends_on B via REST|gRPC|MQ|DB`——**有向、点对点**的边。这撑不起一个真实诉求:

> 一个需求下来,我要知道它涉及哪几个服务、每个服务的边界是什么、服务间通过 facade 还是 MQ 交互、每个服务在本需求里各自要改什么;然后再进各服务做细节澄清·分析·开发·检查。

三个结构性缺陷:

1. **MQ 无法建模**。生产者发到 topic,多个消费者订阅,彼此通过 topic 解耦。硬写成 `producer depends_on consumer`(或反向)会丢信息,且无法表达"多个服务消费同一 topic"。生产者/消费者常常都是团队自有服务,当前模型里没有能装它的字段。
2. **服务边界缺失**。`services[]` 只有一行 `description`,没有"负责什么/不负责什么",需求分析输出不了"每个服务的边界"。
3. **facade 交互不可见**。`via: gRPC` 只说了"用 gRPC 连",没说连哪个 facade 接口、被谁调用;需求分析落不到"这个改动碰哪个接口"。

根因:契约实体(topic、facade 接口)没有独立身份,只能挂在服务→服务的边上。

## 2. 目标与非目标

### 目标
- registry 能表达三类交互:MQ 发布/订阅(topic)、RPC facade 接口调用、REST 直连/跨库依赖。
- 每个服务有明确的 `boundary`(边界/职责)声明。
- 需求分析(cross-app-spec)从"查一层边"升级为"图遍历",产出影响面 + 各服务边界 + 交互方式 + 各服务改造点。
- registry-sync 从代码校准新模型的 topics/facades/depends_on。
- 采用**混合来源**:registry 存丰富声明作缓存,registry-sync 定期从代码校准。

### 非目标(YAGNI)
- **不**从代码自动反推 `boundary`(边界是设计意图,代码推不出);仅在检测到服务新增对外接口时**软提醒**人工复核边界。
- facade **不**做到方法级(方法签名留在契约文档,registry 只到接口级)。
- **不**在 registry 重复契约内容(topic schema、facade 方法签名),只存指向契约文档的指针(遵守 doc-style「权威来源唯一」)。

## 3. 数据模型

三类关系各用各的形状:

```yaml
version: 2                                # schema 版本从 1 升到 2

services:
  - id: order-service
    repo: https://github.com/your-org/order-service
    owner: yinn
    description: 订单核心服务
    boundary: |                           # 新增:边界(负责什么/不负责什么)
      负责订单生命周期(创建、支付回调、状态流转)。
      不负责:库存扣减(inventory-service)、履约(fulfillment-service)。
    docs:
      agents: AGENTS.md
      architecture: docs/architecture.md
      api: docs/api.md
    depends_on:                               # 收窄:仅 REST 直连 / 跨库
      - id: user-service
        via: REST                             # 合法值收窄为 REST | DB
        contract: user-service:docs/api.md
        status: active
        spec: "001"

topics:                                    # 新增一等实体:MQ topic
  - name: order.created
    owner: order-service                   # schema 归属(契约定义方)
    contract: order-service:docs/events/order-created.md
    producers: [order-service]
    consumers: [inventory-service, notification-service, points-service]
    status: active                         # active | planned
    spec: "003"                            # 可选:引入该 topic 的总 spec 编号

facades:                                   # 新增一等实体:RPC facade 接口(接口级)
  - id: user-facade
    owner: user-service
    via: Dubbo                             # Dubbo | SOFA | gRPC | Feign
    contract: user-service:docs/api.md     # 方法签名在契约文档,registry 不重复
    called_by: [order-service, cart-service]
    status: active
    spec: "001"
```

设计要点:
- `depends_on.via` 合法值从 `REST|gRPC|MQ|DB` **收窄为 `REST|DB`**——gRPC/Dubbo/SOFA 归 `facades`,MQ 归 `topics`。这是破坏性 schema 变更,故 `version: 2`。
- topic 用 `name`(如 `order.created`)作主键;facade 用 `id`(如 `user-facade`)作主键。
- **关系单一来源(重要)**:MQ/facade 关系**只**存在 `topics[]/facades[]` 实体里,服务条目**不**镜像 `produces/consumes/calls` 字段。理由:同一关系存两处必然漂移,这正是 doc-style「权威来源唯一」要防的,也是"registry 会失真"的病根。要看"order-service 产哪些 topic",遍历 `topics` 里 producers 含它的条目即可(工具/AI 读整份文件时零成本;`registry-graph.py` 也会渲染出来)。代价:人肉眼看 services.yaml 时,某服务的发布/订阅不内联可见——用图弥补。服务条目只保留 `depends_on`(REST/DB)这类真正点对点、无独立契约实体的关系。

### 需求诉求 → 模型落点对照

| 诉求 | 模型落点 |
|---|---|
| MQ 生产/消费都是自有服务、要建关系 | `topics[].producers/consumers`,一产多消一目了然 |
| 每个服务的边界是什么 | `services[].boundary` |
| 服务间 facade 还是 MQ 交互 | facade→`facades[]`,MQ→`topics[]`,REST 直连→`depends_on` |

## 4. 需求分析升级(cross-app-spec)

影响面分析步骤从"查一层 depends_on"改为**图遍历**:

1. 解析需求 NL,定位种子:直接点名或语义命中的 service / topic / facade。
2. 沿三类边扩散(关系从 topics/facades 实体读取):
   - 种子服务作为某 topic 的 producer → 拉该 topic 全部 `consumers`(下游影响面)
   - 种子服务作为某 topic 的 consumer → 标注该 topic 的 `producer`(可能需协调)
   - 种子服务作为某 facade 的 `called_by` → 拉 facade `owner`(上游接口可能要改);作为 owner → 拉全部 `called_by`
   - 反向:若种子本身是某 topic/facade,直接拉其全部关联服务
3. 产出**影响面表**,每行:服务 | 边界(取 `boundary`) | 交互方式(facade / topic / REST——它如何卷入本需求) | 进/出范围。
4. 每个受影响服务,据 boundary + 交互角色,给一句"本需求中它要改什么"。
5. 契约变更章节:哪些 topic 加字段/新建、哪些 facade 加方法,标兼容/破坏性。
6. 上线顺序:由 producer→consumer、facade 提供方→调用方的依赖自动推导。
7. (不变)为每个服务生成拷贝即用的 `/speckit.specify` 启动指令;现在指令里的"本服务职责/契约约束"摘要有真实材料可填。

## 5. 代码校准升级(registry-sync)

扫描规则扩展,结果映射到新模型:

- **MQ 生产**:`rocketMQTemplate.send/syncSend/asyncSend`、`kafkaTemplate.send`、topic 常量定义 → `topics[].producers`
- **MQ 消费**:`@RocketMQMessageListener(topic=…)`、`@KafkaListener(topics=…)`、`@RabbitListener` → `topics[].consumers`
- **facade 提供**:`@DubboService`/`@SofaService`/gRPC service impl → `facades[].owner`
- **facade 调用**:`@DubboReference`/`@SofaReference`/`@FeignClient` → `facades[].called_by`
- **REST/DB**:沿用现有规则,写入收窄后的 `depends_on`

差异报告按 **topics / facades / depends_on** 三类分别列出缺失/多余/不符;由注解/坐标推测出的关系一律列入待确认清单(附证据:文件 + 注解),人工逐项确认后写入,**不静默写入**(沿用现有原则)。

**边界软提醒**:当校准发现某服务**新增**了它 owner 的 facade 或 topic(即对外契约面扩大),提示"<service> 新增对外接口/事件,其 boundary 描述可能需要更新",不自动改。finalize-feature 收尾时同样触发此提醒。

## 6. 校验与图

### registry-check.py(引用完整性扩到新实体)
- topic 的 `producers/consumers`、facade 的 `owner/called_by` 引用的服务必须在 `services[]` 存在
- 每个 topic 至少 1 个 producer;每个 facade 有 owner
- topic name、facade id 全局唯一
- `depends_on.via` 只允许 `REST|DB`;topic/facade 的 `status` 只允许 `active|planned`
- (关系单一来源后**无双向一致性问题**——服务侧不再镜像关系字段,故不需要 check 两侧一致)

### registry-graph.py(渲染新拓扑)
- 服务为普通节点
- topic 为菱形节点,`producer → topic → consumer` 二部图(天然显示一产多消)
- facade 为接口节点,`called_by → facade → owner`
- depends_on 仍为服务间直连边

## 7. 存量数据迁移

`registry/services.yaml` 现为示例数据(order-service/user-service)。迁移动作:
- `version: 1 → 2`
- 重写示例:补 `boundary`,把原 `order-service depends_on user-service via REST` 保留为 REST 依赖,并新增一个 topic 示例(体现一产多消)和一个 facade 示例(体现一接口多调用),让示例本身教会读者三类关系。
- `registry/README.md` 更新维护规范:三类关系的声明规则、更新时机、校准方式。

> 注:真实团队数据尚未录入(当前全是示例)。本次连同示例一起改,首次录入真实服务时即用新模型。

## 8. 同步义务与发版(AGENTS.md 硬约定)

本次改动涉及 `plugin/` + 脚本 + registry,按仓库规矩:
- **两处同源** × 2:cross-app-spec、registry-sync 各改 skill(`plugin/skills/*/SKILL.md`)+ `prompts/` 副本。
- registry-check.py / registry-graph.py 是纯脚本,无 prompt 副本。
- **发版**:动了 `plugin/`,四处版本号(`VERSION` + `plugin.json` + marketplace 顶层 + `plugins[0]`)递增 + `CHANGELOG.md` 新条目 + 重打包 `.plugin`。先 `python3 scripts/vibe-release.py check`,再 `bump <新版本>`。schema 破坏性变更(v1→v2)建议 minor 版本(如 0.7.0)并在 CHANGELOG 标注迁移指引。
- 文档同步:`registry/README.md`、`registry/services.yaml` 示例、`WORKFLOW.md` §2.2、`plugin/USAGE.md`(registry-sync/cross-app-spec 条目)。
- `docs/doc-style.md` 的"权威来源唯一"不变,新模型仍遵守(契约指针不重复)。

## 9. 验收标准

- [ ] `registry/services.yaml` 用新模型描述示例,含至少 1 个 topic(一产多消)、1 个 facade(一接口多调用)、1 个 REST 依赖。
- [ ] `registry-check.py` 通过,且能对故意植入的坏引用(不存在的 topic/facade/service、无 producer 的 topic、via:gRPC 违规)报错。
- [ ] `registry-graph.py` 生成的图区分服务/topic/facade 三类节点。
- [ ] cross-app-spec skill 与 prompt 副本内容一致,影响面分析描述为图遍历,输出含边界与交互方式列。
- [ ] registry-sync skill 与 prompt 副本内容一致,扫描规则覆盖 MQ 生产/消费与 facade 提供/调用,含边界软提醒。
- [ ] 版本号四处一致、CHANGELOG 有条目、`.plugin` 重打包。
- [ ] 用一个虚构跨应用需求走查 cross-app-spec,产出的影响面表确实包含"哪些服务 + 各自边界 + 交互方式 + 各自改造点"。

## 10. 未定/后续

- boundary 的更强校准方案(目前仅软提醒)留待以后。
- topic schema / facade 方法契约是否逐步沉淀为机器可读文件(OpenAPI/proto/AsyncAPI)供 AI 直接读,超出本次范围。

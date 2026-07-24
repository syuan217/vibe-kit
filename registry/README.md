# registry 维护规范

`services.yaml` 是全系统服务关系的唯一权威来源。它的准确性决定了跨应用影响面分析的质量,按以下机制维护。

> 前置依赖:校验与依赖图脚本需要 PyYAML——`pip install pyyaml`。

## schema v2:三类关系

registry 用三类关系描述系统,**各有归处、关系单一来源**(同一关系不存两处):

| 关系 | 归处 | 形状 |
|---|---|---|
| REST 直连 / 跨库访问 | `services[].depends_on` | 有向点对点,`via: REST` 或 `DB` |
| MQ 发布/订阅 | `topics[]` | `producers[]` → topic → `consumers[]`,天然一产多消 |
| RPC facade 接口调用 | `facades[]` | `called_by[]` → facade → `owner`,天然一接口多调用 |

**服务条目不镜像 `produces/consumes/calls`**——要看某服务收发什么,遍历 topics/facades 即可(`registry-graph.py` 会渲染)。RPC/MQ 一律不进 `depends_on`。

### services[] 字段

| 字段 | 必填 | 说明 |
|---|---|---|
| id | ✅ | 服务唯一标识,kebab-case,与仓库名一致 |
| repo | ✅ | 仓库地址 |
| owner | ✅ | 负责人(registry 变更需其评审) |
| description | ✅ | 一句话职责 |
| boundary | 建议 | 服务边界:负责什么 / **不**负责什么。需求分析据此输出各服务边界。人工维护,代码推不出 |
| docs | ✅ | 文档指针(agents/architecture/api,相对仓库根) |
| depends_on | ✅(可为 []) | **仅** REST 直连 / 跨库:id + via(`REST`\|`DB`)+ contract + 可选 status/spec |

### topics[] 字段

| 字段 | 必填 | 说明 |
|---|---|---|
| name | ✅ | topic 名(如 `order.created`),全局唯一 |
| owner | ✅ | schema 归属服务(契约定义方) |
| contract | 建议 | 事件 schema 文档指针 |
| producers | ✅(≥1) | 生产该 topic 的服务(可多个) |
| consumers | ✅(可为 []) | 消费该 topic 的服务(可多个) |
| status / spec | 可选 | `active`\|`planned`;引入该 topic 的总 spec 编号 |

### facades[] 字段

| 字段 | 必填 | 说明 |
|---|---|---|
| id | ✅ | facade 接口标识,kebab-case,全局唯一 |
| owner | ✅ | 提供该接口的服务 |
| via | ✅ | `Dubbo`\|`SOFA`\|`gRPC`\|`Feign` |
| contract | 建议 | 方法签名文档指针(registry 不抄方法) |
| called_by | ✅(可为 []) | 调用该接口的服务(可多个) |
| status / spec | 可选 | 同上 |

## 三个维护时机(声明式更新)

1. **服务接入时**(vibe-init):新服务必须登记后才算接入完成。
2. **需求收尾时**(finalize-feature):本次需求新增/移除了对外调用、或契约变化 → 更新对应条目,同一 PR 提交。
3. **跨应用立项时**(cross-app-spec):做影响面分析时顺手校对涉及服务的条目,发现失真当场修。

## 自动校验(CI)

`scripts/registry-check.py` 在每次 PR 时由 CI 运行(也可本地跑):

- 结构:yaml 合法、必填字段齐全、id 唯一且 kebab-case、depends_on via 仅 REST/DB、facade via 合法、status 合法
- 引用:depends_on / topic producers·consumers / facade owner·called_by 指向的服务必须已登记(未登记 → 报错)
- 完整性:每个 topic ≥1 producer、每个 facade 有 owner;topic name / facade id 全局唯一
- 提示:服务条目误写 produces/consumes/calls、孤立服务、依赖图 service-graph.md 是否过期

## 定期校准(从代码反推)

声明可能撒谎,代码不会。用 **registry-sync** 在应用仓库扫描真实调用——RPC facade(Feign/Dubbo/SOFA 提供方与消费方注解及 XML)映射到 `facades[]`、MQ 生产/消费(`@RocketMQMessageListener`/`@KafkaListener`/`rocketMQTemplate`/`kafkaTemplate`)映射到 `topics[]`、REST/跨库映射到 `depends_on`——与 registry 声明对比,报告缺失/多余/方式不符。**注解与坐标得出的关系是推测,必须经人逐项确认(附证据)后才写入 registry**,注意"仅引用 DTO 未实际调用"的假阳性。建议:每次大需求后、或每月对全部服务跑一轮。

## 与应用文档的对应关系

hub 与应用文档存在受控时间差,规则是让它**可见、可控**,而非假装不存在:

1. **职责边界压缩不对应面积**:hub 只存关系与指针,契约细节在应用仓库 `docs/api.md` 随代码分支走。永远不要把接口定义抄进 hub——抄一份就多一份漂移源。
2. **变更时序(互链规则)**:应用 PR(含文档)与 hub registry 变更同时提出,PR 描述互相引用链接,前后脚合并。两边 git 历史留下对齐记录,审计时可互相追溯。
3. **中间态显式化**:跨应用需求契约定稿(contracts-approved)时,新依赖可先以 `status: planned` 预登记;全部上线、需求关闭时转 `active`(发起人在关闭总 spec 时顺手完成)。AI 做影响面分析时能同时看到"已生效"与"在途"的关系。
4. **兜底**:registry-sync 从代码(main)反推校准,修正一切声明漂移。

## 本地代码路径映射(local paths)

registry 只存服务的远程身份(repo URL)与关系;**不记任何服务的本地 clone 路径**——后者是个人视角(每人 clone 位置不同),不入 registry schema。AI 跨仓库操作时,用 hub 根目录的 `.vibe-paths.local.yaml`(个人配置,不进版本控制)把 service-id 映射到本机路径:

```yaml
paths:
  order-service: /Users/yinn/workspace/order-service
```

身份校验靠本地仓库的 `git remote URL` 必须匹配 registry 的 `repo` 字段。用 `scripts/vibe-paths.py` 维护(list / add / check / resolve 四个子命令),完整机制与 AI 使用规则见 `docs/local-paths.md`。粒度分工:

- **本地仓库路径**(稳)→ `.vibe-paths.local.yaml`(本节)
- **具体代码文件**(易变)→ 应用仓库自己的 `docs/wiki/code-map.md`,不由 hub 记录

## 变更流程

registry 只通过 PR 修改;涉及某服务条目的变更,该服务 owner 为必要评审人。合并后 CI 自动重新生成 `docs/service-graph.md` 依赖图(或本地 `python3 scripts/registry-graph.py`)。

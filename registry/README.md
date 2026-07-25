# registry 维护规范

`services.yaml` 是全系统服务关系的唯一权威来源。它的准确性决定了跨应用影响面分析的质量,按以下机制维护。

> 前置依赖:校验与依赖图脚本需要 PyYAML——`pip install pyyaml`。

## schema v3:两类关系

registry 用两类关系描述系统,**各有归处、关系单一来源**(同一关系不存两处):

| 关系 | 归处 | 形状 |
|---|---|---|
| 点对点调用(REST / RPC / 跨库) | `services[].depends_on` | 有向点对点,`via` 记具体方式 |
| MQ 发布/订阅 | `topics[]` | `producers[]` → topic → `consumers[]`,天然一产多消 |

**服务条目不镜像 `produces/consumes`**——要看某服务收发什么,遍历 topics 即可(`registry-graph.py` 会渲染)。MQ 关系不进 `depends_on`。

### 粒度是服务级,不是接口级

registry 只回答"**哪些服务被牵涉、用什么方式**",不回答"调的是哪个接口"。需求澄清阶段需要的是前者;接口在实施阶段读代码即可发现,记进 registry 只会带来数倍维护量和必然的漂移。

因此一个服务对之间**只有一条边**:user-service 暴露多少个 Dubbo 接口都不影响 `order-service → user-service (Dubbo)` 这一行。要查接口签名,顺着对端的 `docs.api` 指针去它自己的仓库看。

### services[] 字段

| 字段 | 必填 | 说明 |
|---|---|---|
| id | ✅ | 服务唯一标识,kebab-case,与仓库名一致 |
| repo | ✅ | 仓库地址 |
| owner | ✅ | 负责人(registry 变更需其评审) |
| description | ✅ | 一句话职责 |
| boundary | ✅ | 服务边界:负责什么 / **不**负责什么。**registry 里最值钱的字段**——关系表只圈范围,"哪些事归 A、哪些归 B"全靠它。人工维护,代码推不出 |
| docs | ✅ | 文档指针(agents/architecture/api,相对仓库根) |
| depends_on | ✅(可为 []) | 点对点调用:`id` + `via` 必填,`contract` 建议(缺了 WARN,格式见下),`status`/`spec` 可选。**MQ 不写这里** |

> `boundary` 写法:一句"负责……",再一句"**不负责:……(归 <service-id>)**"。后半句最容易省、也最有用——跨应用需求派活时,AI 就是靠它避免把活派给错误的服务。

### topics[] 字段

| 字段 | 必填 | 说明 |
|---|---|---|
| name | ✅ | topic 名(如 `order.created`),全局唯一 |
| owner | ✅ | schema 归属服务(契约定义方) |
| contract | 建议 | 事件 schema 文档指针,格式见下;前缀须为本 topic 的 `owner` |
| producers | ✅(≥1) | 生产该 topic 的服务(可多个) |
| consumers | ✅(可为 []) | 消费该 topic 的服务(可多个) |
| status / spec | 可选 | `active`\|`planned`;引入该 topic 的总 spec 编号 |

### contract 指针写什么

`contract` 记的是**去哪儿看契约**,不是契约本身。registry 里**永远不抄接口签名、字段、方法名**——抄一份就多一份漂移源,而且真正的定义随代码分支走。

**格式**:`<service-id>:<该服务仓库内的相对路径>`,可带 `#锚点`。

```yaml
contract: user-service:docs/api.md                    # 指到对端的契约文档
contract: order-service:docs/events/order-created.md  # 事件 schema 单独成文时
contract: user-service:docs/api.md#查询用户            # 一份 api.md 覆盖多个接口时指到章节
contract: https://api-portal.corp/user-service        # 外部 API 门户,允许但不随代码走(弱)
```

**三条规则**(registry-check 会 WARN):

1. **必须带 `<service-id>:` 前缀**。裸写 `docs/api.md` 无法判断是哪个仓库的——registry 在 hub,所有路径都是跨仓库的。
2. **前缀必须是契约的提供方**:`depends_on` 的 contract 指**对端**(你调谁就指谁),`topics[]` 的 contract 指该 topic 的 `owner`。契约由提供方维护,消费方只引用。
3. **不填会被提醒**。它是消费方(和 AI)找到接口定义的唯一入口,不填就只能去对端仓库全库翻。

**指向的文档里该有什么**:接口/事件的定义或对 OpenAPI、proto、AsyncAPI 文件的索引 + 兼容性变更记录。应用仓库的 `docs/api.md` 模板已给出结构(HTTP API / 消息·事件 / 变更记录三节)。事件 schema 可以留在 `docs/api.md` 的"消息 / 事件"一节,也可以像上面第二个例子那样单独成文——量大时单独成文,registry 直接指到那一份。

**AI 怎么用它**:先 `python3 scripts/vibe-paths.py resolve <service-id>` 拿到本机路径,再拼上后半段打开文件;没有本地映射就询问用户,**不 clone**。

### depends_on[].via 取值

| 值 | 用于 |
|---|---|
| `REST` | HTTP 直连(RestTemplate/WebClient/axios 等) |
| `Feign` | 声明式 HTTP 客户端(`@FeignClient`),带服务发现名 |
| `Dubbo` / `SOFA` / `gRPC` | 对应框架的 RPC 调用 |
| `DB` | 跨库读写(重依赖,也是坏味道,值得单独盯) |

MQ 没有对应取值——它归 `topics[]`。

## 三个维护时机(声明式更新)

1. **服务接入时**(vibe-init):新服务必须登记后才算接入完成。
2. **需求收尾时**(finalize-feature):本次需求新增/移除了对外调用、或契约变化 → 更新对应条目,同一 PR 提交。
3. **跨应用立项时**(cross-app-spec):做影响面分析时顺手校对涉及服务的条目,发现失真当场修。

## 自动校验(CI)

`scripts/registry-check.py` 在每次 PR 时由 CI 运行(也可本地跑):

- 结构:yaml 合法、schema `version` 为 3、必填字段齐全、id 唯一且 kebab-case、depends_on via 合法、status 合法
- 迁移守卫:检测到 v2 遗留的顶层 `facades[]` 直接报错并给出折叠办法
- 引用:depends_on / topic producers·consumers 指向的服务必须已登记(未登记 → 报错)
- 完整性:每个 topic ≥1 producer、topic name 全局唯一
- contract 指针:缺失、裸路径(无 `<service-id>:` 前缀)、前缀不是契约提供方 → 三种情况各 WARN
- 提示:服务条目误写 produces/consumes/consumers/calls、孤立服务、依赖图 service-graph.md 是否过期

## 定期校准(从代码反推)

声明可能撒谎,代码不会。用 **registry-sync** 在应用仓库扫描真实调用——RPC 消费方注解与构建坐标(`@FeignClient`/`@DubboReference`/`@SofaReference`/`xxx-api` artifact)、REST/跨库一并映射到 `depends_on`(via 记具体方式),MQ 生产/消费(`@RocketMQMessageListener`/`@KafkaListener`/`rocketMQTemplate`/`kafkaTemplate`)映射到 `topics[]`——与 registry 声明对比,报告缺失/多余/方式不符。**只扫本服务的出边**(我调谁、我发收什么);"谁调我"是别人仓库的事,由对方的 registry-sync 补上。**注解与坐标得出的关系是推测,必须经人逐项确认(附证据)后才写入 registry**,注意"仅引用 DTO 未实际调用"的假阳性。建议:每次大需求后、或每月对全部服务跑一轮。

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

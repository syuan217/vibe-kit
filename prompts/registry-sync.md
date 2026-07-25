# registry-sync — 从代码校准服务依赖关系

> 用法:在**应用仓库**中对任意 AI 工具说"按 hub 的 prompts/registry-sync.md 校准依赖"。
> (本文件由 `scripts/sync-prompts.py` 从 `plugin/skills/registry-sync/SKILL.md` 生成,勿手改)

定位:registry 的声明可能失真,代码不会撒谎。在**应用仓库**中执行,反推真实依赖并修正 hub registry。若当前 cwd 不在本应用仓库,先在 hub 跑 `python3 scripts/vibe-paths.py resolve <本服务 id>` 取本地路径再 `cd` 过去;未映射则询问用户(见 `docs/local-paths.md`,禁止为扫代码而 clone)。
建议频率:每次大需求收尾后,或每月对全部服务跑一轮。

## 步骤

1. 定位 hub(优先级:应用仓库根 `.vibe-hub` 文件 → `$VIBE_HUB` 环境变量 → 对话上下文 → **询问用户**;不要猜,**禁止为定位 hub 而 clone 任何仓库**),读 `registry/services.yaml` 中本服务条目(未登记则视为全新登记)。
2. 扫描代码找出**真实**对外关系,按 v3 两类归位(注解与构建配置是重要证据源)。registry 是**服务级**粒度:只认"调了哪个服务、用什么方式",**不要记接口名/方法名**——那些留给实施阶段读代码。只扫本服务的**出边**("谁调我"是对方仓库的事)。
   - **RPC 调用**(→ `depends_on`,via 记 `Dubbo`/`SOFA`/`gRPC`/`Feign`):`@FeignClient(name=...)`、`@DubboReference`/`@Reference`、`@SofaReference` 及 XML(`<dubbo:reference>`/`<sofa:reference>`);按注解里的服务名/接口所属包归到**对端 service-id**,同一对端多个接口**合并为一条依赖**
   - **构建坐标**:pom.xml / build.gradle 引用其他服务的 `xxx-api`/`xxx-client`/`xxx-facade` artifact → 推测对该服务的 RPC 依赖(证据力最强,编译期强制)。核对时先 `python3 scripts/vibe-paths.py resolve <对端 service-id>` 取本地路径;未登记则列待确认,不要 clone
   - **REST/跨库**(→ `depends_on`,via 记 `REST`/`DB`):RestTemplate/WebClient/axios/fetch 封装的 base URL 与服务发现名;读写其他服务拥有的库/表(跨库是重依赖也是坏味道,单独标注)
   - **MQ 生产**(→ `topics[].producers`):`rocketMQTemplate.send`/`syncSend`/`asyncSend`、`kafkaTemplate.send`、topic 常量定义
   - **MQ 消费**(→ `topics[].consumers`):`@RocketMQMessageListener(topic=...)`、`@KafkaListener(topics=...)`、`@RabbitListener`
   - **本服务提供的对外接口**(`@DubboService`/`@SofaService`/gRPC impl):v3 不单独登记(谁调它由调用方声明),但要统计数量供第 6 步的边界提醒判断
3. 对比"代码实际" vs "registry 声明",**按 depends_on / topics 两类分别**输出:
   - **缺失**:代码中存在、registry 未声明(最危险,影响面分析会漏)
   - **多余**:registry 声明、代码中已不存在(历史残留)
   - **不符**:producers/consumers 名单、`via` 方式或 contract 指针与实际不一致
4. **凡由注解、构建坐标推测出的关系一律属于"推测",连同动态 URL、透传调用一起列入待确认清单**:每项附证据(文件路径 + 注解/坐标内容),经用户逐项确认后才写入,**不要静默写入**。注意假阳性:仅引用了 api 包中 DTO 而未实际调用的坐标依赖,重点核对。
5. 经用户确认后更新 hub `registry/services.yaml`,运行 `python3 scripts/registry-check.py` 校验、`python3 scripts/registry-graph.py` 重新生成依赖图,在 hub 提交:`chore(registry): sync <service-id> deps from code`。
6. **边界软提醒**:若本次校准发现本服务**新增**了对外接口(`@DubboService`/`@SofaService`/gRPC impl)或 owner 的 topic(对外契约面扩大),提示「<service> 新增对外接口/事件,其 registry `boundary` 描述可能需要更新」——v3 把接口从 registry 拿掉后,`boundary` 是唯一还能表达"这个服务对外负责什么"的字段,更值得盯。不自动改,交用户决定。

---
name: registry-sync
description: Calibrates the service registry (registry/services.yaml in the vibe-kit hub) by scanning an app's code for real dependencies - HTTP clients, gRPC stubs, MQ topics, cross-service DB access - and reporting drift against the declared relations. Use when the user says "校准依赖", "registry 同步", "检查服务依赖关系", "registry-sync", or periodically after major features ship.
---

# registry-sync — 从代码校准服务依赖关系

定位:registry 的声明可能失真,代码不会撒谎。在**应用仓库**中执行,反推真实依赖并修正 hub registry。若当前 cwd 不在本应用仓库,先在 hub 跑 `python3 scripts/vibe-paths.py resolve <本服务 id>` 取本地路径再 `cd` 过去;未映射则询问用户(见 `docs/local-paths.md`,禁止为扫代码而 clone)。

## 步骤

1. 定位 hub(优先级:应用仓库根 `.vibe-hub` 文件 → `$VIBE_HUB` 环境变量 → 对话上下文 → **询问用户**;不要猜,**禁止为定位 hub 而 clone 任何仓库**),读 `registry/services.yaml` 中本服务条目(未登记则视为全新登记)。
2. 扫描代码找出**真实**对外关系,按 v2 三类归位(注解与构建配置是重要证据源):
   - **facade 提供**(→ `facades[].owner`):`@DubboService`/`@Service`(Dubbo)、`@SofaService`、gRPC service impl
   - **facade 调用**(→ `facades[].called_by`):`@FeignClient(name=...)`、`@DubboReference`/`@Reference`、`@SofaReference` 及 XML(`<dubbo:reference>`/`<sofa:reference>`);按注解服务名/接口归属映射对端 facade。核对对端接口真实存在时,先 `python3 scripts/vibe-paths.py resolve <对端 service-id>` 取本地路径;未登记则列待确认,不要 clone
   - **构建坐标**:pom.xml / build.gradle 引用其他服务的 `xxx-api`/`xxx-client`/`xxx-facade` artifact → 推测对端 facade
   - **MQ 生产**(→ `topics[].producers`):`rocketMQTemplate.send`/`syncSend`/`asyncSend`、`kafkaTemplate.send`、topic 常量定义
   - **MQ 消费**(→ `topics[].consumers`):`@RocketMQMessageListener(topic=...)`、`@KafkaListener(topics=...)`、`@RabbitListener`
   - **REST/跨库**(→ `depends_on`,via 仅 REST/DB):RestTemplate/WebClient/axios/fetch 封装的 base URL 与服务发现名;读写其他服务拥有的库/表(跨库是重依赖也是坏味道,单独标注)
3. 对比"代码实际" vs "registry 声明",**按 topics / facades / depends_on 三类分别**输出:
   - **缺失**:代码中存在、registry 未声明(最危险,影响面分析会漏)
   - **多余**:registry 声明、代码中已不存在(历史残留)
   - **不符**:producers/consumers/called_by 名单、via 方式或 contract 指针与实际不一致
4. **凡由注解、构建坐标推测出的关系一律属于"推测",连同动态 URL、透传调用一起列入待确认清单**:每项附证据(文件路径 + 注解/坐标内容),经用户逐项确认后才写入,**不要静默写入**。注意假阳性:仅引用了 api 包中 DTO 而未实际调用的坐标依赖,重点核对。
5. 经用户确认后更新 hub `registry/services.yaml`,运行 `python3 scripts/registry-check.py` 校验、`python3 scripts/registry-graph.py` 重新生成依赖图,在 hub 提交:`chore(registry): sync <service-id> deps from code`。
6. **边界软提醒**:若本次校准发现某服务**新增**了它 owner 的 facade 或 topic(对外契约面扩大),提示「<service> 新增对外接口/事件,其 registry `boundary` 描述可能需要更新」——不自动改,交用户决定。

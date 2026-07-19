---
name: registry-sync
description: Calibrates the service registry (registry/services.yaml in the vibe-kit hub) by scanning an app's code for real dependencies - HTTP clients, gRPC stubs, MQ topics, cross-service DB access - and reporting drift against the declared relations. Use when the user says "校准依赖", "registry 同步", "检查服务依赖关系", "registry-sync", or periodically after major features ship.
---

# registry-sync — 从代码校准服务依赖关系

定位:registry 的声明可能失真,代码不会撒谎。在**应用仓库**中执行,反推真实依赖并修正 hub registry。

## 步骤

1. 定位 hub 仓库(从对话上下文找,找不到问用户),读 `registry/services.yaml` 中本服务条目(未登记则视为全新登记)。
2. 扫描代码找出**真实**对外依赖:
   - HTTP/REST:client 配置、base URL、服务发现名称(Feign/RestTemplate/axios/fetch 封装等)
   - gRPC:proto import 与 stub 调用
   - MQ:生产与消费的 topic/queue 及对端服务
   - DB:是否读写其他服务拥有的库/表(跨库访问是重要依赖,也是坏味道,单独标注)
3. 对比"代码实际" vs "registry 声明",输出三类差异:
   - **缺失**:代码中存在、registry 未声明(最危险,影响面分析会漏)
   - **多余**:registry 声明、代码中已不存在(历史残留)
   - **不符**:via 方式或 contract 指针与实际不一致
4. 不确定的依赖(动态 URL、透传调用)标注"存疑"并列出证据位置,由用户判断,**不要静默写入**。
5. 经用户确认后更新 hub `registry/services.yaml`,运行 `python3 scripts/registry-check.py` 校验、`python3 scripts/registry-graph.py` 重新生成依赖图,在 hub 提交:`chore(registry): sync <service-id> deps from code`。

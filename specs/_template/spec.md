# NNN-需求名(跨应用总 spec)

- 状态: draft | contracts-approved | in-progress | done
- 发起人 / 日期:
- 需求来源: <链接>

## 1. 需求概述

<what 与 why,不谈技术实现>

## 2. 影响面

> 子 spec 是各仓库的过程产物(`specs/` 不入库),此处不填文件路径——只记落到谁头上、在哪条分支、进展如何。

| 服务 | 边界 | 交互方式 | 变更类型 | 负责人 | 分支 | 状态 |
|---|---|---|---|---|---|---|
| order-service | 订单生命周期(不含库存) | produces order.created | 事件加字段 | @someone | NNN-xxx | todo / doing / done |
| inventory-service | SKU 库存扣减 | consumes order.created | 新增消费逻辑 | @someone | NNN-xxx | todo / doing / done |

## 3. 待定问题(跨端未决)

> 只记「**答案不同会改变一个以上服务的做法**」的问题——只影响单个服务的,留给该服务自己的 `/speckit.clarify`。
> 发起人不确定时**留待定,不要替 owner 拍板**:猜错的答案一旦写进契约,下游会当既定前提照做,比开放问题更难纠正。
> 没有未决项是好事,直接删掉本节。

| 问题 | 影响哪些服务 | 由谁定 | 何时定 | 结论 |
|---|---|---|---|---|
| 订单取消后库存立即回补还是延迟对账 | order-service / inventory-service | @inventory-owner | 契约评审前 | |
| 重复消费的幂等由生产方还是消费方保证 | order-service / inventory-service | 双方 | 契约评审前 | |

标「契约评审前」的必须在状态转 `contracts-approved` 之前有结论。

## 4. 契约变更(先于实现定稿)

<新增/修改的 API、消息、事件的定义或文件链接;标注兼容性(兼容/破坏性)>

## 5. 各服务职责拆分

### <service-id>

- 要做什么:
- 验收标准:

## 6. 上线顺序与依赖

<部署顺序(通常先提供方后消费方)、灰度策略、回滚预案>

## 7. 端到端验收

<跨服务验收场景>

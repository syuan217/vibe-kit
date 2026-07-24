# NNN-需求名(跨应用总 spec)

- 状态: draft | contracts-approved | in-progress | done
- 发起人 / 日期:
- 需求来源: <链接>

## 1. 需求概述

<what 与 why,不谈技术实现>

## 2. 影响面

| 服务 | 边界 | 交互方式 | 变更类型 | 子 spec |
|---|---|---|---|---|
| order-service | 订单生命周期(不含库存) | produces order.created | 事件加字段 | <repo>/specs/NNN-xxx/spec.md |
| inventory-service | SKU 库存扣减 | consumes order.created | 新增消费逻辑 | <repo>/specs/NNN-xxx/spec.md |

## 3. 契约变更(先于实现定稿)

<新增/修改的 API、消息、事件的定义或文件链接;标注兼容性(兼容/破坏性)>

## 4. 各服务职责拆分

### <service-id>

- 要做什么:
- 验收标准:

## 5. 上线顺序与依赖

<部署顺序(通常先提供方后消费方)、灰度策略、回滚预案>

## 6. 端到端验收

<跨服务验收场景>

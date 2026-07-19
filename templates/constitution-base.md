<!--
团队工程宪法基线 — 由 vibe-kit 维护,bootstrap 时写入应用仓库 .specify/memory/constitution.md
应用可用 /speckit.constitution 在此基础上追加应用级原则;基线条款不得删改。
-->

# 工程宪法

## 一、文档即交付物

1. 任务的完成定义包含文档更新:凡改变行为、接口、目录结构的变更,必须同步更新 AGENTS.md 与 docs/ 相关内容后才算完成。
2. 文档的唯一权威来源是 git 仓库,随 PR 评审合入;关键决策不得只存在于本地文件、聊天记录或外部平台。
3. 对外契约(API/消息/事件)变更必须更新 docs/api.md,并同步 hub 仓库 registry/services.yaml 及通知消费方。
4. AI 生成的文档与代码一样需经人工评审。

## 二、规格先行

5. 非琐碎变更先有 spec(spec-kit 流程);跨应用需求先在 hub 仓库立总 spec,契约定稿后再实现。
6. spec 关注 what 与 why,plan 才引入技术选型;/speckit.clarify 默认不跳过。

## 三、质量

7. 行为变更必须有测试覆盖,不合并无测试的行为变更。
8. 简单优先:不引入未经论证的依赖、抽象与组件。

## 治理

- 基线由团队在 vibe-kit 仓库以 PR 方式修订。
- 应用级补充原则不得与基线冲突;冲突时以基线为准。

---
<!-- 以下为应用级补充,由 /speckit.constitution 维护 -->

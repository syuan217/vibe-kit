---
name: sync-docs
description: Incrementally syncs project docs (AGENTS.md, docs/, wiki code-map) with actual code state by scanning git changes since the last doc update. Use when the user says "同步文档", "补文档", "文档过期了", "sync docs", or when docs are found inconsistent with code during other work.
---

# sync-docs — 增量补齐项目文档

目标:让 AGENTS.md 与 docs/ 反映代码当前真实状态。**只改文档,不改代码。**

## 步骤

1. 确定检查范围:
   - 默认:自上次文档更新以来的变更。上次文档更新 commit:`git log -1 --format=%H -- docs/ AGENTS.md`,据此 `git diff <commit>...HEAD --stat` + `git log --oneline <commit>..HEAD`
   - 用户指定了区间/PR 时以指定范围为准
2. 逐项核对文档与代码,不一致则修改文档:
   - AGENTS.md:技术栈、常用命令、目录结构、约定
   - docs/wiki/code-map.md 与模块页:路径、符号是否仍真实存在(重点检查代码搬移导致的失效指针)
   - docs/architecture.md:模块、依赖、数据流、数据模型
   - docs/api.md:对外接口、消息/事件及变更记录表
3. 保持既有文档格式;不确定标 `TODO(待确认)`,禁止臆造。
4. 若对外契约有变化:docs/api.md 变更记录表补一行,提醒用户同步 hub `registry/services.yaml` 并通知消费方。
5. 输出变更摘要,经用户确认后提交:`docs: sync docs with code`。

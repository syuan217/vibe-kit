---
name: sync-docs
description: Incrementally syncs project docs (AGENTS.md, docs/, wiki code-map) with actual code state by scanning git changes since the last doc update. Use when the user says "同步文档", "补文档", "文档过期了", "sync docs", after branch merges or rebases cause doc conflicts or drift ("合并后文档冲突"), or when docs are found inconsistent with code during other work.
---

# sync-docs — 增量补齐项目文档

目标:让 AGENTS.md 与 docs/ 反映代码当前真实状态。**只改文档,不改代码。**
适用场景包括分支合并/rebase 之后:文档冲突不逐行手解——先解代码冲突完成合并,再跑本流程以合并后的代码为准重建文档条目(文档是代码的投影,冲突服从实体)。

## 步骤

1. 确定检查范围(基线优先级):
   - 首选 `docs/.sync-commit` 文件内容(记录"文档与代码最后确认一致"的 commit id)
   - 该文件不存在时回退推导:`git log -1 --format=%H -- docs/ AGENTS.md`
   - 用户指定了区间/PR 时以指定范围为准
   - 据基线执行 `git diff <基线>...HEAD --stat` + `git log --oneline <基线>..HEAD`
2. 逐项核对文档与代码,不一致则修改文档:
   - AGENTS.md:技术栈、常用命令、目录结构、约定
   - docs/wiki/code-map.md 与模块页:路径、符号是否仍真实存在(重点检查代码搬移导致的失效指针)
   - docs/architecture.md:模块、依赖、数据流、数据模型
   - docs/api.md:对外接口、消息/事件及变更记录表
3. 保持既有文档格式;不确定标 `TODO(待确认)`,禁止臆造。
4. 若对外契约有变化:docs/api.md 变更记录表补一行,提醒用户同步 hub `registry/services.yaml` 并通知消费方。
5. 收尾更新基线:`git rev-parse HEAD > docs/.sync-commit`,随文档改动一起提交:`docs: sync docs with code`。(该文件合并冲突时任取一边即可——合并后重跑本流程会重置它。)

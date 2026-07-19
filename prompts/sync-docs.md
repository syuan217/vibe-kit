# sync-docs — 增量补齐项目文档

> 用法:对任意 AI 编码工具说"按 prompts/sync-docs.md 执行"(可附 commit 区间或 PR 号限定范围)。
> 适用:日常发现文档失真;**分支合并/rebase 后文档冲突或漂移**(先解代码冲突完成合并,再跑本流程,以合并后的代码为准重建文档)。
> 目标:让 AGENTS.md 与 docs/ 反映代码当前真实状态。**只改文档,不改代码。**

## 步骤

1. 确定检查范围(基线优先级):
   - 首选 `docs/.sync-commit` 文件内容(记录"文档与代码最后确认一致"的 commit id)
   - 该文件不存在时回退推导:`git log -1 --format=%H -- docs/ AGENTS.md`
   - 用户指定了区间/PR 时,以指定范围为准
   - 据基线执行 `git diff <基线>...HEAD --stat` + `git log --oneline <基线>..HEAD`
2. 逐项核对文档与代码是否一致,不一致则修改文档:
   - AGENTS.md:技术栈、常用命令、目录结构、约定
   - docs/wiki/code-map.md 与模块页:路径、符号是否仍真实存在(重点检查代码搬移导致的失效指针)
   - docs/architecture.md:模块、依赖、数据流、数据模型
   - docs/api.md:对外接口、消息/事件及变更记录表
3. 保持既有文档格式;信息不确定时标注 `TODO(待确认)`,禁止臆造。
4. 若对外契约有变化:在 docs/api.md 变更记录表补一行,并提醒用户同步 hub 仓库 registry/services.yaml、通知消费方。
5. 收尾更新基线:`git rev-parse HEAD > docs/.sync-commit`,随文档改动一起提交,commit message:`docs: sync docs with code`。(该文件合并冲突时任取一边即可——合并后重跑本流程会重置它。)

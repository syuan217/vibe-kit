# vibe-init-docs — 存量仓库从代码反向生成文档

> 用法:对任意 AI 编码工具说"按 prompts/vibe-init-docs.md 执行"。
> 适用:没有文档或文档严重过期的存量仓库(通常在 bootstrap 之后立即执行一次)。

## 步骤

1. 通读仓库:构建配置、入口、目录结构、路由/接口定义、消息生产与消费、数据库 schema、部署配置。
2. 按 vibe-kit 模板生成或重写:
   - AGENTS.md(≤150 行,按模板章节)
   - docs/architecture.md
   - docs/api.md(扫描路由/controller/proto/consumer 得出真实对外契约)
   - docs/wiki/(按 prompts/rebuild-wiki.md 生成 code-map 与模块页)
3. 原则:
   - 只写从代码可证实的内容;推测处标注 `TODO(待确认)` 并在最后汇总列出,由维护者确认
   - 发现的问题(如未使用的模块、疑似废弃接口)单独列出,不写入文档正文
4. 提醒用户:在 hub 仓库 registry/services.yaml 登记本服务及其依赖。
5. 输出摘要与 TODO 清单,经用户确认后提交,commit message:`docs: bootstrap docs from codebase audit`。

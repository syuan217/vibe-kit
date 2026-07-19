---
name: vibe-init-docs
description: Reverse-engineers a full documentation set (AGENTS.md, docs/architecture.md, docs/api.md, docs/wiki/) from an existing codebase with no or badly outdated docs. Use when the user says "反向生成文档", "这个仓库没有文档", "audit docs", "从代码生成文档", or right after bootstrapping a legacy repo.
---

# vibe-init-docs — 存量仓库从代码反向生成文档

适用:没有文档或文档严重过期的存量仓库(通常在 vibe-init 之后立即执行)。

## 步骤

1. 通读仓库:构建配置(pom.xml/build.gradle,注意引用的其他服务 `xxx-api`/`xxx-client` 坐标)、入口、目录结构、路由/接口定义、RPC 注解(Feign `@FeignClient`、Dubbo `@DubboReference`/`@DubboService`、SOFA `@SofaReference`/`@SofaService` 及 XML 配置,区分提供方与消费方)、消息生产与消费、数据库 schema、部署配置。
2. 按 vibe-kit 模板(bootstrap 后仓库内已有骨架)生成或重写:
   - AGENTS.md(≤150 行,保留模板章节结构)
   - docs/architecture.md(模块、依赖、数据流、数据模型)
   - docs/api.md(扫描路由/controller/proto/consumer 得出**真实**对外契约)
   - docs/wiki/(调用 rebuild-wiki skill 生成 code-map 与模块页)
3. 原则:
   - 只写从代码可证实的内容;推测处标 `TODO(待确认)` 并在最后汇总,由维护者确认
   - 发现的问题(未使用模块、疑似废弃接口)单独列出,不写入文档正文
4. 依赖推测清单:把从注解与构建坐标推测出的上游依赖整理成**待确认清单**(每项附证据:文件 + 注解/坐标),供用户逐项确认后登记 hub `registry/services.yaml`;推测不经确认不得直接写入 registry。
5. 输出摘要与 TODO 清单,经用户确认后提交:`docs: bootstrap docs from codebase audit`。

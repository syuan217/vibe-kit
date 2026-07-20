---
name: rebuild-wiki
description: Generates or rebuilds a code-locating wiki (docs/wiki/ with code-map.md and per-module pages) by scanning the codebase, so AI can quickly find where to change code. Use when the user says "生成 wiki", "生成代码地图", "generate wiki", "重建 code map", or after large structural refactors.
---

# rebuild-wiki — 从代码生成/重建代码定位 wiki

目标:`docs/wiki/` 是 AI 快速定位代码的导航层,回答"改 X 要看哪些文件"。模板见本 skill `references/`。

## 步骤

1. **先建入口清单**(后续覆盖率以此为准,不可跳过):用 Grep/Glob 系统性枚举并列成清单——路由/controller(REST 端点)、RPC 提供方注解(Dubbo `@DubboService`/SOFA `@SofaService`/Feign 服务端)、RPC 消费方、消息生产与消费(topic/queue + 处理类)、定时任务、main/启动类。清单每项含:类型、符号、文件路径。同时扫描目录结构、服务层、数据访问、配置与横切组件(鉴权、错误处理、迁移)。
2. **按业务域划分模块**(不是按技术分层;5~15 个为宜),生成:
   - `docs/wiki/README.md` — 模块索引(模板 `references/wiki-readme.md`)
   - `docs/wiki/code-map.md` — 功能定位表 + 横切关注点表(模板 `references/code-map.md`)
   - `docs/wiki/modules/<模块名>.md` — 每模块一页(模板 `references/module-template.md`)
3. 模块页最低内容要求(达不到视为未完成,不要交薄页):
   - 职责一段话 + 关键文件表,且覆盖完整调用链:入口 → 服务/领域逻辑 → 数据访问/外部调用
   - 「常见修改场景」3~5 个典型改动及对应文件(此章节最重要)
   - 与其他模块/外部服务的交互关系
4. **覆盖率检查**:逐项核对第 1 步入口清单,每个入口必须能在 code-map 或某模块页中找到;有遗漏则补齐。汇报"入口 N 项,已覆盖 N 项"后才算通过。
5. **逐条验证**(强制,不可抽查):对生成文档中每个路径用 Glob 确认文件存在、每个符号用 Grep 确认真实存在;失效即修正或标 `TODO(待确认)`。汇报验证统计:"共 X 条引用,修正 Y 条,存疑 Z 条"。
   - 路径写仓库相对路径;符号写类名/函数名,**不写行号**(行号会漂移)
   - 禁止臆造;遵循 hub `docs/doc-style.md`(如可访问)
6. 检查 AGENTS.md 文档地图含 wiki 入口与"改代码前先查 code-map"规则,缺失则补上。
7. 输出模块清单、覆盖率与验证统计、TODO 汇总,经用户确认后提交:`docs: rebuild wiki`。

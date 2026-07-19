---
name: rebuild-wiki
description: Generates or rebuilds a code-locating wiki (docs/wiki/ with code-map.md and per-module pages) by scanning the codebase, so AI can quickly find where to change code. Use when the user says "生成 wiki", "生成代码地图", "generate wiki", "重建 code map", or after large structural refactors.
---

# rebuild-wiki — 从代码生成/重建代码定位 wiki

目标:`docs/wiki/` 是 AI 快速定位代码的导航层,回答"改 X 要看哪些文件"。模板见本 skill `references/`。

## 步骤

1. 扫描代码:目录结构、入口(main/启动类)、路由/controller、RPC 提供方注解(Dubbo `@DubboService`/SOFA `@SofaService`/Feign 服务端)、服务层、数据访问、消息生产与消费、定时任务、配置与横切组件(鉴权、错误处理、迁移)。
2. **按业务域划分模块**(不是按技术分层;5~15 个为宜),生成:
   - `docs/wiki/README.md` — 模块索引(模板 `references/wiki-readme.md`)
   - `docs/wiki/code-map.md` — 功能定位表 + 横切关注点表(模板 `references/code-map.md`)
   - `docs/wiki/modules/<模块名>.md` — 每模块一页(模板 `references/module-template.md`);「常见修改场景」章节最重要:列 3~5 个典型改动及对应文件
3. 硬性要求:
   - 所有路径与符号必须真实存在,生成后用 Grep/Glob 逐一核对
   - 路径写仓库相对路径;符号写类名/函数名,**不写行号**(行号会漂移)
   - 不确定标 `TODO(待确认)`,禁止臆造;遵循 hub `docs/doc-style.md`(如可访问)
4. 检查 AGENTS.md 文档地图含 wiki 入口与"改代码前先查 code-map"规则,缺失则补上。
5. 输出模块清单与 TODO 汇总,经用户确认后提交:`docs: rebuild wiki`。

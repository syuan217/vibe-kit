# rebuild-wiki — 从代码生成/重建项目 wiki

> 用法:对任意 AI 工具说"按 prompts/rebuild-wiki.md 执行"。首次生成或目录结构大改后重建;日常增量维护走 finalize-feature / sync-docs。
> 目标:`docs/wiki/` 是 AI 在 vibe coding 中快速定位代码的导航层,回答"改 X 要看哪些文件"。

## 步骤

1. 扫描代码:目录结构、入口(main/启动类)、路由/controller、服务层、数据访问、消息生产与消费、定时任务、配置与横切组件(鉴权、错误处理、迁移)。
2. **按业务域划分模块**(不是按技术分层;5~15 个为宜),按模板生成:
   - `docs/wiki/README.md` — 模块索引
   - `docs/wiki/code-map.md` — 功能定位表 + 横切关注点表
   - `docs/wiki/modules/<模块名>.md` — 每模块一页(复制 `_module-template.md`),其中「常见修改场景」最重要:列 3~5 个该模块典型改动及对应文件
3. 硬性要求:
   - 所有路径与符号必须真实存在,生成后逐一核对(可用 grep/glob 验证)
   - 路径写仓库相对路径;符号写类名/函数名,不写行号
   - 遵循 hub `docs/doc-style.md`;不确定标 `TODO(待确认)`,禁止臆造
4. 检查 AGENTS.md 文档地图含 wiki 入口,缺失则补上。
5. 输出模块清单与 TODO 汇总,确认后提交:`docs: rebuild wiki`。

# vibe-kit

> 本仓库自身的 AI 统一上下文入口。这是一个 **kit + hub 合一**仓库:kit 是分发给团队的工作流工具,hub 是团队协调数据中心。

## 项目概览

为多仓库(polyrepo)微服务团队提供 spec-driven AI 开发工作流:以 AGENTS.md 为跨 AI 工具的统一文档入口,以 spec-kit 为需求开发流程,以服务注册表协调跨应用需求。完整方案见 WORKFLOW.md(先读这个),目录与安装见 README.md。

- **kit 部分**(工具,随版本演进):`plugin/`(Claude/zcode/Kimi Code 插件,含 7 个 skills 与 `plugin/templates/` 应用仓库脚手架)、`prompts/`(与 skills 同源的 prompt 副本)、`scripts/`(初始化/校验/发版脚本)、`VERSION`
- **hub 部分**(团队数据,持续更新):`registry/`(服务注册表)、`specs/`(跨应用总 spec)、`docs/`(公共文档)
- **插件入口清单**:`.claude-plugin/marketplace.json`(Claude 插件市场,推送 GitHub 后可直接安装)、`kimi.plugin.json`(仓库根,Kimi Code 从 GitHub 安装的入口)

## 技术栈与运行时

- **无构建系统、无 pyproject/package.json**:仓库内容 = Markdown 文档/prompt/skill + Python 3 脚本 + Bash 脚本 + JSON/YAML 清单。
- Python 脚本(`scripts/registry-*.py`、`vibe-paths.py`、`vibe-release.py`)仅依赖 **PyYAML** 一个第三方库(`pip install pyyaml`),其余用标准库;测试用 **pytest**。
- 脚本可随插件分发到应用仓库,`find_hub()` 多级回退定位 hub:命令行参数 > `$VIBE_HUB` > 当前目录 > 脚本上级目录;PyYAML 缺失时给友好提示。
- 应用仓库通过根目录 `.vibe-hub` 文件定位 hub(个人本地配置,不入库)。

## 常用命令

- 校验 registry:`python3 scripts/registry-check.py`
- 重生成依赖图(`docs/service-graph.md`):`python3 scripts/registry-graph.py`
- 查询/维护服务本地路径:`python3 scripts/vibe-paths.py <list|add|check|resolve>`(详见 `docs/local-paths.md`)
- 发版校验:`python3 scripts/vibe-release.py check`;发版 bump:`python3 scripts/vibe-release.py bump <版本>`(详见 `CHANGELOG.md`)
- 重新生成 prompt 副本:`python3 scripts/sync-prompts.py --write`(校验用 `--check`;改了 SKILL.md 必跑)
- 跑测试:`python3 -m pytest tests/ -v`(需 `pip install pyyaml pytest`)
- 打包插件:`cd plugin && zip -r ../vibe-kit.plugin . -x "*.DS_Store"`
- 应用接入:`scripts/vibe-init.sh`;独立 hub:`scripts/init-hub.sh <目录> --git`

## 代码组织

- `plugin/skills/<name>/SKILL.md` — 7 个 skills:cross-app-spec、finalize-feature、rebuild-wiki、registry-sync、sync-docs、vibe-init、vibe-init-docs;每个 skill 就是一个 SKILL.md,**不带任何随附文件**;YAML frontmatter 必填 `name`/`description`,且 `name` 须等于目录名(CI 校验)
- `plugin/templates/` — 应用仓库脚手架(`app/` 下 AGENTS.md、docs、prompts 等)+ `constitution-base.md` 团队宪法基线
- `prompts/` — 与 skills 同源的 prompt 副本,供不用 Claude/zcode/Kimi Code 的工具(Cursor、Codex 等)直接使用
- `registry/services.yaml` — 全系统服务清单唯一权威来源,schema v3 两类关系:`depends_on`(点对点调用,via 记 REST/DB/Dubbo/SOFA/gRPC/Feign)、`topics[]`(MQ);粒度是**服务级不是接口级**,分工靠 `boundary`;规则见 `registry/README.md`
- `tests/` — pytest,以子进程方式对临时目录跑真实脚本(`tests/conftest.py` 提供 `make_hub`/`make_kit` fixture 与 `run_*` 辅助函数)
- `docs/` — 公共文档;`docs/service-graph.md` 由 registry-graph.py 生成,**不手改**

## 修改本仓库的硬性约定(AI 必须遵守)

1. **同源以 SKILL.md 为唯一源,副本靠生成不靠手改**(范围按工作流的操作对象精确划定,不要机械补齐副本):
   - **三处同源**(skill + `prompts/` + `plugin/templates/app/prompts/`):finalize-feature、rebuild-wiki、sync-docs——在应用仓库日常执行,三类用户都需要。
   - **两处同源**(skill + `prompts/`):cross-app-spec、registry-sync、vibe-init-docs——操作对象是 hub 或一次性执行,应用仓库不放副本。
   - **仅 skill**:vibe-init——由 `scripts/vibe-init.sh` 驱动,逻辑变更须同步改脚本,不出 prompt 副本。
   改流程只改 `plugin/skills/<name>/SKILL.md`(正文保持**渠道中立**:只写执行时看得到的路径,不写插件内部路径——skill 不带随附模板,模板的唯一来源是 `plugin/templates/` 与 `specs/_template/`),然后跑 `python3 scripts/sync-prompts.py --write` 重新生成副本(CI 用 `--check` 防漂移,**勿手改副本**)。
2. **改了 `plugin/` 就要发版**:`plugin/.claude-plugin/plugin.json`、`plugin/.zcode-plugin/plugin.json`(zcode 原生清单)、`plugin/.kimi-plugin/plugin.json` 与仓库根 `kimi.plugin.json`(Kimi Code 原生清单两份:随 zip 分发 + GitHub 安装入口)、`.claude-plugin/marketplace.json`(两处:顶层 + `plugins[0]`)、`VERSION` 七处版本号同步递增(CI 校验七处一致),`CHANGELOG.md` 加新版本条目,重新打包 .plugin。**先跑 `python3 scripts/vibe-release.py check` 报漂移,再 `bump <新版本>` 半自动处理**(改版本号、同步 skill 名册、起草 CHANGELOG、重打包)。发布 = push + 打 `v*` tag(CI 自动打包并发 GitHub Release)。
3. **registry 变更**:改 `registry/services.yaml` 后运行 registry-check 与 registry-graph;规则见 `registry/README.md`。
4. **文档规范**:遵循 `docs/doc-style.md`(AGENTS.md ≤150 行、只写可证实内容、权威来源唯一、图用 mermaid);修改模板时保持与 WORKFLOW.md、README.md、`plugin/USAGE.md` 的交叉引用一致。
5. 团队宪法基线(`plugin/templates/constitution-base.md`)条款变更需团队评审,不得随手改。

## 测试与 CI

- 测试在 `tests/`,与 `scripts/` 下的脚本一一对应(registry-check、registry-graph、vibe-paths、sync-prompts),以子进程方式跑真实脚本;**改脚本必须同步补测试**并跑通 `pytest tests/`。
- CI 见 `.github/workflows/`,**触发路径以 workflow 文件为准,勿在此复述**:
  - `registry-check.yml` — pytest + registry-check;合入 main 后自动重生成 `docs/service-graph.md` 并提交。
  - `plugin-release.yml` — 版本/清单/skill 名册 + prompt 副本同源;打 `v*` tag 时打包 `vibe-kit.plugin` 并发 GitHub Release。
- **提交前跑本地校验**,与 CI 是同一组命令(CI 不内联任何额外规则,校验逻辑只在脚本里):

  ```bash
  python3 -m pytest tests/ && python3 scripts/registry-check.py && \
  python3 scripts/vibe-release.py check && python3 scripts/sync-prompts.py --check
  ```

## 安全与边界

- `.vibe-hub`、`.vibe-paths.local.yaml` 是个人本地配置(含本机绝对路径),已 gitignore,**不得入库**;registry 只存远程身份(repo URL)与关系。
- registry 与脚本中禁止写入任何凭据、内网地址以外的敏感信息;hub 可能公开分发(kit 与 hub 可分离,见 WORKFLOW.md §1.1)。
- 脚本不做写破坏性操作;`vibe-release.py bump` 有确认提示(可 `--yes` 跳过)。
- 禁止为定位 hub 或其他仓库代码而 clone 仓库(skills 硬性规则);跨仓库跳转用 `scripts/vibe-paths.py resolve`。

## 文档地图

- WORKFLOW.md — 工作流方案(痛点→机制、hub 部署形态)
- README.md — 目录与快速开始
- CHANGELOG.md — 版本变更记录(由 `scripts/vibe-release.py` 起草)
- docs/requirement-playbook.md — 需求处理手册(团队必读)
- docs/doc-style.md — 文档写作规范(含分支与文档规则)
- docs/local-paths.md — 服务仓库本地路径映射(AI 跨仓库跳转)
- registry/README.md — registry 维护规范
- plugin/USAGE.md — 插件使用说明(人 + AI)
- specs/README.md — 跨应用总 spec 流程

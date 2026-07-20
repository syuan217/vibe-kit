# v0.5.0 发版前体检报告

> 生成时间:2026-07-20
> 范围:0.4.4 → 0.5.0 的改动批(目录迁移 `templates/` → `plugin/templates/`、hub 解耦、`docs/.sync-commit` 改为本地不入库)
> 三处同源(skill / prompts / plugin/templates/app/prompts)版本号已同步至 0.5.0,基本完整,以下为待处理项。

---

## P0 — 必须在发版前修

### 1. `cross-app-spec` 缺两处同源副本

> ✅ 2026-07-20 已修复:新增 hub 级 `prompts/cross-app-spec.md`(供 Cursor/Codex 在 hub 仓库使用);不补应用仓库副本(操作对象是 hub)。同源范围见 #4 的约定改写。

**现状**
- AGENTS.md 第 22 行写明"三处同源",但 `cross-app-spec` 目前只有 `plugin/skills/cross-app-spec/SKILL.md` 一处。
- `prompts/` 下 5 个文件、`plugin/templates/app/prompts/` 下 3 个文件,均无 `cross-app-spec`。

**影响**
- Cursor / Codex 用户无法触发跨应用总 spec 流程。
- 应用仓库内也没有对应副本。

**建议**
- 推荐补齐 `prompts/cross-app-spec.md` 与 `plugin/templates/app/prompts/cross-app-spec.md`;或
- 在 AGENTS.md 显式声明"cross-app-spec 仅 skill 版本,因为它操作的是 hub 而非应用仓库",并相应放宽同源约定。

---

### 2. `.gitignore` 合并逻辑边界(scripts/vibe-init.sh:64)

> ✅ 2026-07-20 已修复:循环改为 `while IFS= read -r line || [ -n "$line" ]`。

**现状**
```bash
while IFS= read -r line; do
  [[ -z "$line" ]] && continue
  grep -qxF "$line" .gitignore || echo "$line" >> .gitignore
done < "$TPL_DIR/app/gitignore"
```

**风险**
- `while IFS= read` 读不到末尾无换行的最后一行。
- 当前模板恰好以换行结尾,暂未触发,但属于潜在 bug。

**建议**
改用 `grep -vFx` 批量去重,或循环改用 `while IFS= read -r line || [ -n "$line" ]`。

---

### 3. `registry-check.py` 运行失败

> ✅ 2026-07-20 已修复:脚本 import 加 try/except 友好提示;registry/README.md 增加 `pip install pyyaml` 前置说明。

**现状**
```
python3 scripts/registry-check.py
→ ModuleNotFoundError: No module named 'yaml'
```

**影响**
- AGENTS.md 硬性约定 #3 要求"改 services.yaml 后运行 registry-check"。
- 协作者环境若无 PyYAML,该约定实际失效。

**建议**
- 在 README.md 或 registry/README.md 加前置说明:`pip install pyyaml`;或
- 在脚本头部检测依赖缺失时打印友好提示。

---

## P1 — 建议修但不阻塞发版

### 4. AGENTS.md 同源约定 #1 与现状不符

> ✅ 2026-07-20 已修复:AGENTS.md 约定 #1 改写为精确范围——三处同源(finalize-feature/rebuild-wiki/sync-docs)、两处同源(cross-app-spec/registry-sync/vibe-init-docs)、仅 skill(vibe-init,脚本驱动)。

**现状**
约定写"工作流内容三处同源",但实际:
- `cross-app-spec`:1 处(仅 skill)
- `vibe-init`:1 处(脚本驱动,无 prompt 副本,合理)
- `vibe-init-docs`:`prompts/` 有,`plugin/templates/app/prompts/` 无
- `registry-sync`:`prompts/` 有,`plugin/templates/app/prompts/` 无

**建议**
把约定改写为更精确的范围,例如:

> 下列工作流需三处同源:finalize-feature、rebuild-wiki、sync-docs。
> 其余按需:vibe-init 由脚本驱动不另出 prompt 副本;cross-app-spec / registry-sync 仅 skill + prompts 两处(操作对象是 hub 而非应用仓库,应用仓库副本无意义);vibe-init-docs 仅 skill + prompts 两处。

避免后续 AI 机械补齐产生冗余副本。

---

### 5. `docs/.sync-commit` 语义变更缺迁移说明

> ✅ 2026-07-20 已修复:plugin/USAGE.md FAQ 增加"从 0.4.x 升级到 0.5.0"迁移指引(`git rm --cached` + 重跑 vibe-init)。

**现状**
- 0.4.2(commit e9187fa)把它作为"入库基线"引入。
- 0.5.0 改为"本地不入库",并入 `plugin/templates/app/gitignore`。

**影响**
已接入团队升级到 0.5.0 后:
- 他们仓库里历史已入库的 `docs/.sync-commit`、`.vibe-hub`、`.vibe-kit-version` 会变成"未跟踪文件"持续出现在 `git status`。
- 已入库版本与本地新写版本可能冲突。

**建议**
在 README.md 或 plugin/USAGE.md 的"升级"小节加迁移指引,例如:

```bash
# 从 0.4.x 升级到 0.5.0 后,在应用仓库执行一次:
git rm --cached docs/.sync-commit .vibe-hub .vibe-kit-version 2>/dev/null || true
# 然后重跑 vibe-init 合并新 .gitignore 条目
```

---

### 6. hub 定位优先级三处表述不一致

> ✅ 2026-07-20 已修复:统一为 `.vibe-hub → $VIBE_HUB → 对话上下文 → 询问用户`(finalize-feature skill/prompt/模板副本已对齐);vibe-init 保留「用户指明」最高优先档并注明原因(首次接入时 `.vibe-hub` 尚不存在)。

| 文件 | 表述 |
|------|------|
| `plugin/skills/vibe-init/SKILL.md` | 用户指明 → `.vibe-hub` → `$VIBE_HUB` → 询问 |
| `plugin/skills/registry-sync/SKILL.md` | `.vibe-hub` → `$VIBE_HUB` → 对话上下文 → 询问 |
| `plugin/skills/cross-app-spec/SKILL.md` | `.vibe-hub` → `$VIBE_HUB` → 对话上下文 → 询问 |
| `plugin/USAGE.md:128` | `.vibe-hub` → `$VIBE_HUB` → 对话上下文 → 询问 |

**建议**
统一为一种表述。推荐使用 vibe-init 以外那版(更常见、更通用),vibe-init 因涉及首次写入 `.vibe-hub`,可保留"用户指明"优先档,但需注释清楚为何不同。

---

## P2 — 锦上添花

### 7. `.plugin` 打包未执行

> ❎ 2026-07-20 关闭(不成立):`plugin-release.yml` 的 release job 在打 tag 时自动打包并附到 GitHub Release,符合"CI 自动打包则忽略"。

**现状**:仓库根没有 `vibe-kit.plugin` zip。

**建议**
- 若 CI 自动打包则忽略;否则发版前手动执行:
  ```bash
  cd plugin && zip -r ../vibe-kit.plugin . -x "*.DS_Store"
  ```
- AGENTS.md 约定 #2 要求"重新打包 .plugin"。

---

### 8. `doc-freshness.yml` 排除清单可补

> ❎ 2026-07-20 关闭(不修):`.vibe-hub`/`.vibe-kit-version` 已被 gitignore,不会出现在 PR diff,加排除项属死代码。

**现状**:`.specify/` 已在排除清单,但新增的 `.vibe-hub`、`.vibe-kit-version` 未列。

**建议**:虽是 dot-file 不在源码 grep 范围、无害,但显式加入更清晰。

---

## 处理顺序建议

1. **立即发版前**:P0 #1(cross-app-spec 同源)、P1 #5(迁移说明)、P1 #6(优先级统一)。
2. **发版后跟进**:P0 #2(脚本边界)、P0 #3(registry-check 依赖说明)、P1 #4(AGENTS.md 约定措辞)。
3. **随手做**:P2 #7、#8。

---

## 附:本次 0.5.0 已完成的关键改动(备查)

- 模板迁移:`templates/` → `plugin/templates/`(随插件分发,免 clone)。
- hub 解耦:找不到 hub 时强制询问用户,禁止 AI 自行 clone 仓库。
- 本地化标记:`docs/.sync-commit`、`.vibe-hub`、`.vibe-kit-version` 改为本地不入库,新增 `plugin/templates/app/gitignore` 合并机制。
- rebuild-wiki / finalize-feature:强化入口清单 + 覆盖率检查 + 逐条验证。
- 版本号:VERSION / plugin.json / marketplace.json 三处同步至 0.5.0。

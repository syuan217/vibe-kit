#!/usr/bin/env bash
# 在应用仓库根目录执行,初始化 vibe-kit 工作流:
#   /path/to/vibe-kit/scripts/vibe-init.sh [--hub <hub目录>]
# hub 目录优先级: --hub 参数 > $VIBE_HUB 环境变量 > kit 仓库自身(合一模式)
set -euo pipefail

KIT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TPL_DIR="$KIT_DIR/plugin/templates"
HUB_DIR="${VIBE_HUB:-$KIT_DIR}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --hub) HUB_DIR="$2"; shift 2 ;;
    -h|--help) grep '^#' "$0" | head -4; exit 0 ;;
    *) echo "未知参数: $1"; exit 1 ;;
  esac
done

[[ -d .git ]] || { echo "错误: 请在应用仓库根目录执行"; exit 1; }
[[ -f "$HUB_DIR/registry/services.yaml" ]] || {
  echo "错误: hub 目录无效(缺少 registry/services.yaml): $HUB_DIR"
  echo "如需独立 hub,先执行: $KIT_DIR/scripts/init-hub.sh <目录> --git"
  exit 1
}

# 0. 提示安装工作流引擎依赖(mattpocock skills:grill-with-docs/code-review/tdd 等)
#    这是外部依赖,不随 vibe-kit 插件分发;不自动跑(避免 npx 网络问题阻断初始化)
echo ">> 检查工作流引擎依赖(mattpocock skills)"
echo "本工作流的澄清/评审引擎(grill-with-docs、code-review、tdd)来自 mattpocock/skills(外部依赖)。"
echo "若尚未安装,请在初始化完成后于本仓库执行(按你用的 AI agent 选 -a):"
echo "  npx skills add mattpocock/skills -a claude-code    # 或 codex / cursor / zcode / kimi-code-cli"
echo ""

# 2. 拷贝应用模板(不覆盖已存在的文件;gitignore 模板单独合并处理)
echo ">> 拷贝应用模板"
had_gitignore=0; [[ -e ./gitignore ]] && had_gitignore=1  # 记录:用户原本是否有裸 gitignore
cp -Rn "$TPL_DIR/app/." . || true
# 模板中的 gitignore 以合并方式写入 .gitignore,不落地为裸文件;
# 仅清理本次拷入的副本,避免误删用户原有的同名文件
(( had_gitignore )) || rm -f ./gitignore

# 3. 注入团队 constitution 基线(仅当尚未存在有效内容时)
mkdir -p docs
if [[ ! -s docs/constitution.md ]] || ! grep -q "工程宪法" docs/constitution.md; then
  cp "$TPL_DIR/constitution-base.md" docs/constitution.md
  echo ">> 已写入团队宪法基线(docs/constitution.md,应用级补充直接编辑该文件)"
fi

# 4. 记录 kit 版本与 hub 位置(均为本地文件,已被 .gitignore 忽略)
cp "$KIT_DIR/VERSION" .vibe-kit-version
mkdir -p docs
git rev-parse HEAD > docs/.sync-commit 2>/dev/null || true  # 文档一致性基线
HUB_ABS="$(cd "$HUB_DIR" && pwd)"
echo "$HUB_ABS" > .vibe-hub

# 5. 合并 gitignore 模板(逐行去重追加,不动用户已有条目)
touch .gitignore
# 重跑时不再追加注释:注释按行去重会脱离它描述的条目、糊在文件末尾
has_block=0; grep -qF '# ===== vibe-kit' .gitignore && has_block=1
while IFS= read -r line || [ -n "$line" ]; do
  [[ -z "$line" ]] && continue
  [[ "$line" == \#* && $has_block -eq 1 ]] && continue
  grep -qxF "$line" .gitignore || echo "$line" >> .gitignore
done < "$TPL_DIR/app/gitignore"
echo ">> 已合并 .gitignore(本地配置与过程产物不入库)"

echo ""
echo "完成。hub: $HUB_ABS(已写入 .vibe-hub,AI 工具据此定位)"
echo "下一步:"
echo "  1. 安装工作流引擎依赖(若上面未装):npx skills add mattpocock/skills -a <你的 agent>"
echo "  2. 编辑 AGENTS.md 填写应用信息(存量仓库可让 AI 按 prompts/vibe-init-docs.md 反向生成)"
echo "  3. 在 hub 的 registry/services.yaml 登记本应用及依赖: $HUB_ABS/registry/services.yaml"
echo "  4. 将 AGENTS.md、docs/、prompts/、specs/_template/ 提交入库"
echo "     (specs/ 下的需求目录是过程产物已被 .gitignore 忽略;_template/ 是骨架,入库供队友直接用)"

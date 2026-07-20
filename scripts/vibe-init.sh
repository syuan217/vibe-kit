#!/usr/bin/env bash
# 在应用仓库根目录执行,初始化 vibe-kit 工作流:
#   /path/to/vibe-kit/scripts/vibe-init.sh [--integrations claude,cursor,codex] [--hub <hub目录>]
# hub 目录优先级: --hub 参数 > $VIBE_HUB 环境变量 > kit 仓库自身(合一模式)
set -euo pipefail

KIT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TPL_DIR="$KIT_DIR/plugin/templates"
INTEGRATIONS="claude,cursor,codex"
HUB_DIR="${VIBE_HUB:-$KIT_DIR}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --integrations) INTEGRATIONS="$2"; shift 2 ;;
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

if ! command -v specify >/dev/null 2>&1; then
  if command -v uv >/dev/null 2>&1; then
    echo "未检测到 specify CLI(spec-kit)。"
    read -r -p "是否现在安装? [y/N] " ans
    if [[ "$ans" == "y" || "$ans" == "Y" ]]; then
      uv tool install specify-cli --from git+https://github.com/github/spec-kit.git
    else
      echo "已取消。手动安装: uv tool install specify-cli --from git+https://github.com/github/spec-kit.git"
      exit 1
    fi
  else
    echo "错误: 未安装 specify CLI,且缺少 uv(其安装器)。请依次执行:"
    echo "  curl -LsSf https://astral.sh/uv/install.sh | sh"
    echo "  uv tool install specify-cli --from git+https://github.com/github/spec-kit.git"
    exit 1
  fi
fi

# 1. spec-kit 初始化:每个 agent 各跑一次,.specify/ 核心共享,各 agent 命令目录都会生成
IFS=',' read -ra AGENTS <<< "$INTEGRATIONS"
for a in "${AGENTS[@]}"; do
  echo ">> specify init (--integration $a)"
  specify init . --force --integration "$a" --ignore-agent-tools
done

# 2. 拷贝应用模板(不覆盖已存在的文件;gitignore 模板单独合并处理)
echo ">> 拷贝应用模板"
cp -Rn "$TPL_DIR/app/." . || true
rm -f ./gitignore  # 模板中的 gitignore 以合并方式写入 .gitignore,不落地为裸文件

# 3. 注入团队 constitution 基线(仅当尚未存在有效内容时)
mkdir -p .specify/memory
if [[ ! -s .specify/memory/constitution.md ]] || ! grep -q "工程宪法" .specify/memory/constitution.md; then
  cp "$TPL_DIR/constitution-base.md" .specify/memory/constitution.md
  echo ">> 已写入团队宪法基线(可用 /speckit.constitution 追加应用级原则)"
fi

# 4. 记录 kit 版本与 hub 位置(均为本地文件,已被 .gitignore 忽略)
cp "$KIT_DIR/VERSION" .vibe-kit-version
mkdir -p docs
git rev-parse HEAD > docs/.sync-commit 2>/dev/null || true  # 文档一致性基线
HUB_ABS="$(cd "$HUB_DIR" && pwd)"
echo "$HUB_ABS" > .vibe-hub

# 5. 合并 gitignore 模板(逐行去重追加,不动用户已有条目)
touch .gitignore
while IFS= read -r line || [ -n "$line" ]; do
  [[ -z "$line" ]] && continue
  grep -qxF "$line" .gitignore || echo "$line" >> .gitignore
done < "$TPL_DIR/app/gitignore"
echo ">> 已合并 .gitignore(本地配置与过程产物不入库)"

echo ""
echo "完成。hub: $HUB_ABS(已写入 .vibe-hub,AI 工具据此定位)"
echo "下一步:"
echo "  1. 编辑 AGENTS.md 填写应用信息(存量仓库可让 AI 按 prompts/vibe-init-docs.md 反向生成)"
echo "  2. 在 hub 的 registry/services.yaml 登记本应用及依赖: $HUB_ABS/registry/services.yaml"
echo "  3. 将 AGENTS.md、docs/、prompts/ 提交入库(.specify/、specs/、agent 命令目录已被 .gitignore 忽略,各人由本脚本重新生成)"

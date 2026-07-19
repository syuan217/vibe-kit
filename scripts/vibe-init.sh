#!/usr/bin/env bash
# 在应用仓库根目录执行,初始化 vibe-kit 工作流:
#   /path/to/vibe-kit/scripts/vibe-init.sh [--integrations claude,cursor,codex]
set -euo pipefail

KIT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
INTEGRATIONS="claude,cursor,codex"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --integrations) INTEGRATIONS="$2"; shift 2 ;;
    -h|--help) grep '^#' "$0" | head -3; exit 0 ;;
    *) echo "未知参数: $1"; exit 1 ;;
  esac
done

[[ -d .git ]] || { echo "错误: 请在应用仓库根目录执行"; exit 1; }

command -v specify >/dev/null 2>&1 || {
  echo "错误: 未安装 specify CLI,请先执行:"
  echo "  uv tool install specify-cli --from git+https://github.com/github/spec-kit.git"
  exit 1
}

# 1. spec-kit 初始化:每个 agent 各跑一次,.specify/ 核心共享,各 agent 命令目录都会生成
IFS=',' read -ra AGENTS <<< "$INTEGRATIONS"
for a in "${AGENTS[@]}"; do
  echo ">> specify init (--integration $a)"
  specify init . --force --integration "$a" --ignore-agent-tools
done

# 2. 拷贝应用模板(不覆盖已存在的文件)
echo ">> 拷贝应用模板"
cp -Rn "$KIT_DIR/templates/app/." . || true

# 3. 注入团队 constitution 基线(仅当尚未存在有效内容时)
mkdir -p .specify/memory
if [[ ! -s .specify/memory/constitution.md ]] || ! grep -q "工程宪法" .specify/memory/constitution.md; then
  cp "$KIT_DIR/templates/constitution-base.md" .specify/memory/constitution.md
  echo ">> 已写入团队宪法基线(可用 /speckit.constitution 追加应用级原则)"
fi

# 4. 记录 kit 版本
cp "$KIT_DIR/VERSION" .vibe-kit-version

echo ""
echo "完成。下一步:"
echo "  1. 编辑 AGENTS.md 填写应用信息(存量仓库可让 AI 按 prompts/vibe-init-docs.md 反向生成)"
echo "  2. 在 vibe-kit 的 registry/services.yaml 中登记本应用及依赖"
echo "  3. 将 AGENTS.md、docs/、.specify/、各 agent 命令目录等全部提交入库"

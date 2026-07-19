#!/usr/bin/env bash
# 在指定目录创建独立的 vibe-kit hub(与 kit 仓库分离的团队协调目录)
# 用法: /path/to/vibe-kit/scripts/init-hub.sh <目标目录> [--git]
#   --git  同时初始化 git 仓库并完成首次提交(团队协作必须共享 git)
set -euo pipefail

KIT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET="${1:?用法: init-hub.sh <目标目录> [--git]}"
shift || true
INIT_GIT=false
[[ "${1:-}" == "--git" ]] && INIT_GIT=true

mkdir -p "$TARGET/registry" "$TARGET/specs" "$TARGET/docs" "$TARGET/scripts"

# 组装 hub(不覆盖已有文件)
cp -n "$KIT_DIR/registry/services.yaml" "$TARGET/registry/" 2>/dev/null || true
cp -n "$KIT_DIR/registry/README.md" "$TARGET/registry/" 2>/dev/null || true
cp -Rn "$KIT_DIR/specs/." "$TARGET/specs/" 2>/dev/null || true
for f in architecture.md conventions.md doc-style.md requirement-playbook.md; do
  cp -n "$KIT_DIR/docs/$f" "$TARGET/docs/" 2>/dev/null || true
done
cp -n "$KIT_DIR/scripts/registry-graph.py" "$KIT_DIR/scripts/registry-check.py" "$TARGET/scripts/" 2>/dev/null || true
cp "$KIT_DIR/VERSION" "$TARGET/.vibe-kit-version"

if [[ ! -f "$TARGET/README.md" ]]; then
  cat > "$TARGET/README.md" <<'EOF'
# team-hub(vibe-kit hub)

团队跨应用协调中心:服务注册表(registry/)、跨应用总 spec(specs/)、公共文档(docs/)。
由 vibe-kit 的 `scripts/init-hub.sh` 生成;工作流与模板见 kit 仓库。

> ⚠️ 团队协作时本目录必须是共享 git 仓库(总 spec 评审、registry 变更都走 PR)。
> 仅个人试用阶段可以保持本地目录。

- 需求怎么处理:docs/requirement-playbook.md
- registry 怎么维护:registry/README.md
- 校验:`python3 scripts/registry-check.py`;依赖图:`python3 scripts/registry-graph.py`
EOF
fi

if $INIT_GIT && [[ ! -d "$TARGET/.git" ]]; then
  git -C "$TARGET" init -b main -q
  git -C "$TARGET" add -A
  git -C "$TARGET" commit -qm "chore: init vibe-kit hub"
  echo ">> 已初始化 git,请添加远端并推送以便团队共享"
fi

echo "hub 已创建: $TARGET"
echo "应用仓库接入时指定: vibe-init.sh --hub $TARGET(或 export VIBE_HUB=$TARGET)"

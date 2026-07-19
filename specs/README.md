# 跨应用需求 spec

只有**涉及 2 个及以上应用**的需求在此立总 spec;单应用需求直接在其仓库走 spec-kit 流程。

## 流程

1. 复制 `_template/` 为 `NNN-需求名/`(NNN 全局递增三位编号,如 `001-unified-login`)
2. 填写 spec.md:需求概述 → 影响面(可让 AI 读 `../registry/services.yaml` 辅助分析)→ 契约变更 → 各服务职责 → 上线顺序
3. 契约章节经涉及服务的 owner 评审定稿后,方可开始各服务实现
4. 各应用仓库 `/speckit.specify` 时在子 spec 首行引用本 spec 链接;并回填本 spec 影响面表格中的子 spec 链接
5. 全部服务完成并按上线顺序发布后,将状态改为 done

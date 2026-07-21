---
name: cross-app-spec
description: Creates a cross-application master spec in the vibe-kit hub repo for requirements spanning multiple services - analyzes impact via the service registry, defines contract changes first, and splits work per service. Use when the user says "跨应用需求", "这个需求涉及多个服务", "建总 spec", "cross-app spec", or "影响面分析".
---

# cross-app-spec — 跨应用需求总 spec

适用:涉及 **2 个及以上应用**的需求(单应用需求直接在其仓库走 `/speckit.specify`)。

## 步骤

1. 定位 hub,按优先级:当前应用仓库根 `.vibe-hub` 文件内容 → `$VIBE_HUB` 环境变量 → 对话上下文 → **询问用户**;不要猜,**禁止为定位 hub 而 clone 任何仓库**。
2. **影响面分析**:读 hub `registry/services.yaml`,根据需求描述与依赖关系推断涉及哪些服务、通过什么方式(REST/gRPC/MQ)关联;把推断结果给用户确认,不确定的服务标注存疑。对于涉及的服务,若 hub `.vibe-paths.local.yaml` 有映射(见 `docs/local-paths.md`),在确认表里标注「本地可直达」。
3. 在 hub `specs/` 下建 `NNN-需求名/spec.md`(NNN 取现有最大编号 +1,三位数;模板 `references/spec-template.md`),重点填写:
   - 需求概述(what/why,不谈实现)
   - 影响面表(服务、仓库、变更类型;子 spec 列暂留空)
   - **契约变更**(先于实现定稿,标注兼容/破坏性)
   - 各服务职责拆分与验收标准
   - 上线顺序(通常先提供方后消费方)
4. 提醒流程:契约章节须经涉及服务的 owner 评审(状态改 `contracts-approved`)后,各应用仓库才开始实现;子 spec 首行引用本 spec 链接,并回填影响面表。**此评审是人工闸口,不要替用户跳过。**
5. **生成各服务启动指令**(拷贝即用):为每个涉及服务输出一条预填好的命令。先在 hub 跑 `python3 scripts/vibe-paths.py resolve <service-id>` 取本地 clone 路径——已映射则指令注释写成 `# 在 <绝对路径> 执行:` 并附 `cd <路径>`;未映射则保持 `# 在 <service-id> 仓库执行:` 占位,并提示用户可用 `vibe-paths.py add` 登记(机制见 `docs/local-paths.md`,禁止为定位而 clone)。指令格式:

   ```
   # 在 <本地路径或 service-id 仓库> 执行:
   /speckit.specify 实现跨应用需求「NNN-需求名」中本服务的部分。总 spec:<hub spec 链接或路径>。本服务职责:<职责拆分章节内容摘要>。契约约束:<该服务相关的契约变更摘要>。完成后回填总 spec 影响面表。
   ```

   用户在对应仓库粘贴即进入标准 spec-kit 流程(specify → clarify → plan → tasks → implement)。
6. 若本需求会新增/改变服务依赖:契约定稿(contracts-approved)时即在 `registry/services.yaml` 以 `status: planned` + `spec: NNN` 预登记新依赖(上线关闭需求时转 `active`),并重新生成依赖图:`python3 scripts/registry-graph.py`。

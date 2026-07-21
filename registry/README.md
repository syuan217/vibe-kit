# registry 维护规范

`services.yaml` 是全系统服务关系的唯一权威来源。它的准确性决定了跨应用影响面分析的质量,按以下机制维护。

> 前置依赖:校验与依赖图脚本需要 PyYAML——`pip install pyyaml`。

## 字段说明

| 字段 | 必填 | 说明 |
|---|---|---|
| id | ✅ | 服务唯一标识,kebab-case,与仓库名一致 |
| repo | ✅ | 仓库地址 |
| owner | ✅ | 负责人(registry 变更需其评审) |
| description | ✅ | 一句话职责 |
| docs | ✅ | 文档指针(agents/architecture/api,相对仓库根) |
| depends_on | ✅(可为 []) | 上游依赖:id + via(REST/gRPC/MQ/DB/其他)+ contract 指针 |
| depends_on[].status | 可选 | `active`(默认,已生效)/ `planned`(契约定稿、尚未上线)——显式表达 hub 超前于应用的中间态 |
| depends_on[].spec | 可选 | 引入该依赖的总 spec 编号,溯源用 |

只声明 `depends_on`(我调用谁);"谁调用我"由脚本从全表反推,**不要手工维护 consumers**,避免双向声明打架。

## 三个维护时机(声明式更新)

1. **服务接入时**(vibe-init):新服务必须登记后才算接入完成。
2. **需求收尾时**(finalize-feature):本次需求新增/移除了对外调用、或契约变化 → 更新对应条目,同一 PR 提交。
3. **跨应用立项时**(cross-app-spec):做影响面分析时顺手校对涉及服务的条目,发现失真当场修。

## 自动校验(CI)

`scripts/registry-check.py` 在每次 PR 时由 CI 运行(也可本地跑):

- 结构:yaml 合法、必填字段齐全、id 唯一且 kebab-case、via 取值合法
- 引用:depends_on 指向的服务必须已登记(未登记 → 报错,这是发现"漏登记"的主要手段)
- 提示:孤立服务(无依赖也无消费方)、依赖图 service-graph.md 是否过期

## 定期校准(从代码反推)

声明可能撒谎,代码不会。用 **registry-sync**(插件 skill 或 `prompts/registry-sync.md`)在应用仓库扫描真实调用——RPC 注解(Feign/Dubbo/SOFA 及 XML 配置)、构建坐标(其他服务的 api/client 包引用)、HTTP client、gRPC stub、MQ 生产消费——与 registry 声明对比,报告缺失/多余/方式不符的依赖。**注解与坐标得出的关系是推测,必须经人逐项确认(附证据)后才写入 registry**,注意"仅引用 DTO 未实际调用"的假阳性。建议:每次大需求后、或每月对全部服务跑一轮。

## 与应用文档的对应关系

hub 与应用文档存在受控时间差,规则是让它**可见、可控**,而非假装不存在:

1. **职责边界压缩不对应面积**:hub 只存关系与指针,契约细节在应用仓库 `docs/api.md` 随代码分支走。永远不要把接口定义抄进 hub——抄一份就多一份漂移源。
2. **变更时序(互链规则)**:应用 PR(含文档)与 hub registry 变更同时提出,PR 描述互相引用链接,前后脚合并。两边 git 历史留下对齐记录,审计时可互相追溯。
3. **中间态显式化**:跨应用需求契约定稿(contracts-approved)时,新依赖可先以 `status: planned` 预登记;全部上线、需求关闭时转 `active`(发起人在关闭总 spec 时顺手完成)。AI 做影响面分析时能同时看到"已生效"与"在途"的关系。
4. **兜底**:registry-sync 从代码(main)反推校准,修正一切声明漂移。

## 本地代码路径映射(local paths)

registry 只存服务的远程身份(repo URL)与关系;**不记任何服务的本地 clone 路径**——后者是个人视角(每人 clone 位置不同),不入 registry schema。AI 跨仓库操作时,用 hub 根目录的 `.vibe-paths.local.yaml`(个人配置,不进版本控制)把 service-id 映射到本机路径:

```yaml
paths:
  order-service: /Users/yinn/workspace/order-service
```

身份校验靠本地仓库的 `git remote URL` 必须匹配 registry 的 `repo` 字段。用 `scripts/vibe-paths.py` 维护(list / add / check / resolve 四个子命令),完整机制与 AI 使用规则见 `docs/local-paths.md`。粒度分工:

- **本地仓库路径**(稳)→ `.vibe-paths.local.yaml`(本节)
- **具体代码文件**(易变)→ 应用仓库自己的 `docs/wiki/code-map.md`,不由 hub 记录

## 变更流程

registry 只通过 PR 修改;涉及某服务条目的变更,该服务 owner 为必要评审人。合并后 CI 自动重新生成 `docs/service-graph.md` 依赖图(或本地 `python3 scripts/registry-graph.py`)。

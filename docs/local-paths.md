# 本地代码路径映射(local paths)

> 让 AI 从 hub registry 的 service-id 一步跳到本机 clone 的代码目录,而不是停在 GitHub URL。面向人(如何配置)与 AI(何时查询)。

## 解决什么问题

跨应用需求做影响面分析时,AI 从 `registry/services.yaml` 只能拿到对端的 `repo:` 远程 URL,无法直接读本机代码。两个粒度的需求分别由两层机制覆盖:

| 粒度 | 例子 | 稳定性 | 由谁记 |
|---|---|---|---|
| A. 服务仓库本地路径 | `~/workspace/order-service` | 高(clone 位置很少变) | 本文件讲的 `.vibe-paths.local.yaml` |
| B. 具体代码文件 | `order-service/.../OrderFeignClient.java` | 低(重构每天都在动) | 应用仓库 `docs/wiki/code-map.md` |

粒度 A 用本地映射文件解决;粒度 B 由应用仓库 wiki 兜底——AI 拿到 A 的本地路径后,再读该仓库 `docs/wiki/code-map.md` 定位到具体文件。

## 文件位置与格式

`.vibe-paths.local.yaml` 放在 hub 根目录,**不进版本控制**(个人配置,见 `.gitignore`)。格式:

```yaml
# 服务仓库本地路径映射(个人配置,不进版本控制)。
# 由 scripts/vibe-paths.py 维护,或参考本文件手工编辑。
paths:
  order-service: /Users/yinn/workspace/order-service
  user-service: /Users/yinn/workspace/user-service
```

key 必须与 `registry/services.yaml` 的 service-id 一致;value 是 clone 的绝对路径。身份锚点是本地仓库的 `git remote URL`——必须匹配 registry 的 `repo` 字段,挡住"路径填了但 clone 错仓库"。允许 fork / ssh-vs-https 形式的差异(只 WARN 不阻止)。

## 四个子命令

| 子命令 | 作用 |
|---|---|
| `python3 scripts/vibe-paths.py list` | 列出所有服务与映射状态:OK / 未映射 / remote 不匹配 / 孤儿(registry 无此服务) |
| `python3 scripts/vibe-paths.py add <sid> <path>` | 添加映射,自动校验 `.git/` 与 remote,文件不存在则创建 |
| `python3 scripts/vibe-paths.py check` | 仅校验,有 ERROR 返回 1(不进 CI,个人配置自检) |
| `python3 scripts/vibe-paths.py resolve <sid>` | 输出某服务本地绝对路径(供管道:`cd $(python3 scripts/vibe-paths.py resolve order-service)`) |

## AI 跨仓库跳转链路

```mermaid
graph LR
  Reg[registry/services.yaml<br/>service-id + repo URL] -->|.vibe-paths.local.yaml<br/>id → 本地路径| Local[本地 clone 路径]
  Local -->|docs/wiki/code-map.md<br/>业务功能 → 具体文件| Code[具体代码文件]
  Reg -.若 .vibe-paths 缺映射.-> Ask[询问用户<br/>禁止为定位而 clone]
```

## AI 使用规则

1. **跨仓库操作前先 resolve**:需要读对端服务代码时,先跑 `python3 scripts/vibe-paths.py resolve <sid>` 取本地路径。未映射(返回非 0)则询问用户去 `add`,**禁止为定位代码而 clone 任何仓库**。
2. **定位到仓库后走 wiki**:拿到本地路径后,优先读 `<路径>/docs/wiki/code-map.md` 找具体文件,查不到再全库搜索——和单仓库定位规则一致。
3. **不把本地路径写进团队文档**:本地路径是个人视角,`registry/services.yaml` / `specs/` / cross-app-spec 的影响面表都只记 repo URL。映射数据只活在 `.vibe-paths.local.yaml`。

## 与 registry 的关系

`.vibe-paths.local.yaml` 是 hub 的**可选个人配置**,不在 `registry/services.yaml` 的 schema 里(权威来源唯一原则:服务关系由 registry 管,本地路径由个人管)。两者关系见 `registry/README.md` 的「本地代码路径映射」一节。

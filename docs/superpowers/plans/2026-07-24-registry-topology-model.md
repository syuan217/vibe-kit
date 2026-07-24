# registry 拓扑模型升级 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 MQ topic 与 RPC facade 升级为 registry 的一等实体、给服务加 boundary 字段,让"一个需求涉及哪些服务、各自边界、如何交互"能从 registry 图遍历得出。

**Architecture:** registry schema v1→v2:服务条目只保留 `depends_on`(收窄为 REST/DB);MQ 关系存 `topics[]`(producers/consumers),facade 关系存 `facades[]`(owner/called_by),关系单一来源不镜像到服务侧。校验/图脚本、cross-app-spec/registry-sync/finalize-feature 三条工作流、spec 模板随之升级。属 `plugin/` 改动,收尾发 0.7.0。

**Tech Stack:** Python 3.9(标准库 + PyYAML)、pytest(子进程集成测试)、Markdown(skill/prompt/模板)、mermaid(依赖图)。

**同源约束(AGENTS.md 硬约定,实现时必须遵守):**
- cross-app-spec、registry-sync:**两处同源** = `plugin/skills/<name>/SKILL.md` + `prompts/<name>.md`,一起改。
- finalize-feature:**三处同源** = skill + `prompts/finalize-feature.md` + `plugin/templates/app/prompts/finalize-feature.md`。
- 影响面表模板:`plugin/skills/cross-app-spec/references/spec-template.md` + `specs/_template/spec.md`,一起改。
- 动了 `plugin/` → 末尾走发版(Task 11)。

---

## 文件结构总览

**新建:**
- `tests/test_registry_check.py` — registry-check 的子进程集成测试
- `tests/test_registry_graph.py` — registry-graph 的子进程集成测试
- `tests/conftest.py` — 构造 fixture hub 目录的公共 helper

**修改:**
- `scripts/registry-check.py` — 校验 topics/facades、收窄 via、单一来源提示
- `scripts/registry-graph.py` — 渲染 topic/facade 节点
- `registry/services.yaml` — 迁移到 v2 示例(含 topic 一产多消、facade 一接口多调用)
- `registry/README.md` — 字段说明与维护规范
- `plugin/skills/cross-app-spec/SKILL.md` + `prompts/cross-app-spec.md` — 图遍历影响面
- `plugin/skills/cross-app-spec/references/spec-template.md` + `specs/_template/spec.md` — 影响面表加列
- `plugin/skills/registry-sync/SKILL.md` + `prompts/registry-sync.md` — 扫描规则 + 边界软提醒
- `plugin/skills/finalize-feature/SKILL.md` + `prompts/finalize-feature.md` + `plugin/templates/app/prompts/finalize-feature.md` — 边界软提醒
- `WORKFLOW.md` — §2.2 registry 描述
- `plugin/USAGE.md` — registry-sync / cross-app-spec 条目
- `CHANGELOG.md` + 四处版本号 + `.plugin`(Task 11 由 vibe-release.py 处理)
- `.github/workflows/registry-check.yml` — 增测试步骤

---

## Task 1: 测试脚手架 + registry-check v2 校验(TDD)

**Files:**
- Create: `tests/conftest.py`
- Create: `tests/test_registry_check.py`
- Modify: `scripts/registry-check.py`

- [ ] **Step 1: 写 fixture helper**

创建 `tests/conftest.py`,提供"把一个 registry dict 写成临时 hub 目录"的 helper:

```python
import subprocess
import sys
import pathlib
import textwrap
import yaml
import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent


@pytest.fixture
def make_hub(tmp_path):
    """把 registry dict 写成一个临时 hub 目录,返回该目录路径。"""
    def _make(registry: dict) -> pathlib.Path:
        reg_dir = tmp_path / "registry"
        reg_dir.mkdir(parents=True, exist_ok=True)
        (reg_dir / "services.yaml").write_text(
            yaml.safe_dump(registry, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )
        (tmp_path / "docs").mkdir(exist_ok=True)
        return tmp_path
    return _make


def run_check(hub_dir: pathlib.Path):
    """以子进程运行 registry-check.py,返回 CompletedProcess。"""
    return subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "registry-check.py"), str(hub_dir)],
        capture_output=True, text=True,
    )


def run_graph(hub_dir: pathlib.Path):
    return subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "registry-graph.py"), str(hub_dir)],
        capture_output=True, text=True,
    )
```

- [ ] **Step 2: 写失败测试**

创建 `tests/test_registry_check.py`:

```python
from conftest import run_check


def _valid_v2():
    """一份合法的 v2 registry:1 topic 一产多消、1 facade 一接口多调用、1 REST 依赖。"""
    return {
        "version": 2,
        "services": [
            {"id": "order-service", "repo": "https://x/order", "owner": "a",
             "description": "订单", "boundary": "负责订单;不负责库存。",
             "docs": {"agents": "AGENTS.md"},
             "depends_on": [{"id": "user-service", "via": "REST",
                             "contract": "user-service:docs/api.md"}]},
            {"id": "user-service", "repo": "https://x/user", "owner": "b",
             "description": "用户", "boundary": "负责用户与鉴权。",
             "docs": {"agents": "AGENTS.md"}, "depends_on": []},
            {"id": "inventory-service", "repo": "https://x/inv", "owner": "c",
             "description": "库存", "boundary": "负责库存。",
             "docs": {"agents": "AGENTS.md"}, "depends_on": []},
        ],
        "topics": [
            {"name": "order.created", "owner": "order-service",
             "contract": "order-service:docs/events/order-created.md",
             "producers": ["order-service"],
             "consumers": ["inventory-service", "user-service"],
             "status": "active"},
        ],
        "facades": [
            {"id": "user-facade", "owner": "user-service", "via": "Dubbo",
             "contract": "user-service:docs/api.md",
             "called_by": ["order-service"], "status": "active"},
        ],
    }


def test_valid_v2_passes(make_hub):
    r = run_check(make_hub(_valid_v2()))
    assert r.returncode == 0, r.stdout


def test_topic_producer_must_be_known_service(make_hub):
    reg = _valid_v2()
    reg["topics"][0]["producers"] = ["ghost-service"]
    r = run_check(make_hub(reg))
    assert r.returncode == 1
    assert "ghost-service" in r.stdout


def test_topic_needs_at_least_one_producer(make_hub):
    reg = _valid_v2()
    reg["topics"][0]["producers"] = []
    r = run_check(make_hub(reg))
    assert r.returncode == 1
    assert "producer" in r.stdout.lower()


def test_facade_consumer_must_be_known_service(make_hub):
    reg = _valid_v2()
    reg["facades"][0]["called_by"] = ["ghost-service"]
    r = run_check(make_hub(reg))
    assert r.returncode == 1
    assert "ghost-service" in r.stdout


def test_facade_via_must_be_valid(make_hub):
    reg = _valid_v2()
    reg["facades"][0]["via"] = "REST"   # facade 不允许 REST
    r = run_check(make_hub(reg))
    assert r.returncode == 1
    assert "via" in r.stdout


def test_depends_on_via_narrowed_to_rest_db(make_hub):
    reg = _valid_v2()
    reg["services"][0]["depends_on"][0]["via"] = "gRPC"  # 收窄后非法
    r = run_check(make_hub(reg))
    assert r.returncode == 1
    assert "via" in r.stdout


def test_duplicate_topic_name(make_hub):
    reg = _valid_v2()
    reg["topics"].append(dict(reg["topics"][0]))
    r = run_check(make_hub(reg))
    assert r.returncode == 1
    assert "重复" in r.stdout


def test_service_mirror_field_warns(make_hub):
    reg = _valid_v2()
    reg["services"][0]["produces"] = ["order.created"]
    r = run_check(make_hub(reg))
    assert "produces" in r.stdout  # 提示不要在服务条目镜像关系
```

- [ ] **Step 3: 运行,确认失败**

Run: `cd /Users/yinnfeng/Documents/workspace/vibe-kit && python3 -m pytest tests/test_registry_check.py -v`
Expected: 多条 FAIL(旧脚本不认 topics/facades,`test_facade_via_must_be_valid` 等失败;`test_depends_on_via_narrowed` 因旧 VALID_VIA 含 gRPC 而失败)。

- [ ] **Step 4: 改 registry-check.py**

改 `scripts/registry-check.py`。第 40 行 `VALID_VIA` 收窄,并新增 facade via 与 status 集合:

```python
ROOT = find_hub()
VALID_VIA = {"REST", "DB"}                      # depends_on 收窄:facade/MQ 各有归处
VALID_FACADE_VIA = {"Dubbo", "SOFA", "gRPC", "Feign"}
VALID_STATUS = {"active", "planned"}
REQUIRED = ["id", "repo", "owner", "description", "docs"]
MIRROR_FIELDS = ("produces", "consumes", "calls")  # 关系单一来源:不应出现在服务条目
```

把 `depends_on` 循环里的 status 校验改用 `VALID_STATUS`(原第 82-83 行):

```python
            if dep.get("status", "active") not in VALID_STATUS:
                errors.append(f"{sid} -> {did}: status 必须为 active 或 planned")
```

在服务循环内(原第 86-87 行 consumers 提示处)替换为镜像字段提示:

```python
        for mf in MIRROR_FIELDS:
            if mf in s:
                warnings.append(
                    f"{sid}: {mf} 请勿写在服务条目(关系单一来源,在 topics/facades 维护),建议删除")
        if "consumers" in s:
            warnings.append(f"{sid}: consumers 请勿手工维护,建议删除该字段")
```

在服务循环**之后**、孤立服务检查**之前**,新增 topics 与 facades 校验块:

```python
    topics = reg.get("topics") or []
    facades = reg.get("facades") or []

    # ── topics 校验 ──
    topic_names = [t.get("name") for t in topics]
    dup_t = {n for n in topic_names if topic_names.count(n) > 1}
    if dup_t:
        errors.append(f"topic name 重复: {dup_t}")
    for t in topics:
        name = t.get("name", "<无name>")
        if not t.get("name"):
            errors.append("topic 缺少 name")
        if t.get("owner") not in known:
            errors.append(f"topic {name}: owner {t.get('owner')} 未登记为服务")
        if not t.get("contract"):
            warnings.append(f"topic {name}: 建议补 contract 指针(schema 文档)")
        producers = t.get("producers") or []
        consumers = t.get("consumers") or []
        if not producers:
            errors.append(f"topic {name}: 至少需要 1 个 producer")
        for svc in producers + consumers:
            if svc not in known:
                errors.append(f"topic {name}: 引用了未登记的服务 {svc}")
        if t.get("status", "active") not in VALID_STATUS:
            errors.append(f"topic {name}: status 必须为 active 或 planned")

    # ── facades 校验 ──
    facade_ids = [f.get("id") for f in facades]
    dup_f = {i for i in facade_ids if facade_ids.count(i) > 1}
    if dup_f:
        errors.append(f"facade id 重复: {dup_f}")
    for f in facades:
        fid = f.get("id", "<无id>")
        if not f.get("id") or not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", str(fid)):
            errors.append(f"facade {fid}: id 必须为 kebab-case")
        if f.get("owner") not in known:
            errors.append(f"facade {fid}: owner {f.get('owner')} 未登记为服务")
        if f.get("via") not in VALID_FACADE_VIA:
            errors.append(f"facade {fid}: via 必须为 {sorted(VALID_FACADE_VIA)} 之一")
        if not f.get("contract"):
            warnings.append(f"facade {fid}: 建议补 contract 指针(方法签名文档)")
        for svc in f.get("called_by") or []:
            if svc not in known:
                errors.append(f"facade {fid}: called_by 引用了未登记的服务 {svc}")
        if f.get("status", "active") not in VALID_STATUS:
            errors.append(f"facade {fid}: status 必须为 active 或 planned")
```

把孤立服务检查(原第 90-93 行)升级为"考虑 topics/facades 参与":

```python
    # 孤立服务提示(连接性:depends_on / 被依赖 / 参与 topic / 参与 facade)
    connected = set(consumed)
    for t in topics:
        connected.update(t.get("producers") or [])
        connected.update(t.get("consumers") or [])
    for f in facades:
        if f.get("owner"):
            connected.add(f["owner"])
        connected.update(f.get("called_by") or [])
    for s in services:
        sid = s.get("id", "<无id>")
        if not (s.get("depends_on") or []) and sid not in connected:
            warnings.append(f"{sid}: 孤立服务(无任何依赖/被依赖/收发/接口关系),确认是否真实")
```

把结尾统计行(原第 107 行)补上 topic/facade 计数:

```python
    print(f"\n{len(services)} 个服务, {len(topics)} 个 topic, {len(facades)} 个 facade, "
          f"{len(errors)} 个错误, {len(warnings)} 个警告")
```

- [ ] **Step 5: 运行,确认通过**

Run: `python3 -m pytest tests/test_registry_check.py -v`
Expected: 全部 PASS。

- [ ] **Step 6: 提交**

```bash
git add scripts/registry-check.py tests/conftest.py tests/test_registry_check.py
git commit -m "feat(registry): registry-check 校验 topics/facades 一等实体,收窄 depends_on via"
```

---

## Task 2: 迁移 registry/services.yaml 到 v2

**Files:**
- Modify: `registry/services.yaml`

- [ ] **Step 1: 重写为 v2 示例**

用下面内容整体替换 `registry/services.yaml`:

```yaml
# 服务注册表 — 全系统唯一权威的服务清单与关系(schema v2)
# 三类关系各有归处:
#   - REST 直连 / 跨库   → services[].depends_on(via: REST | DB)
#   - MQ 发布/订阅        → topics[](producers/consumers)
#   - RPC facade 接口调用 → facades[](owner/called_by)
# 关系单一来源:服务条目不镜像 produces/consumes/calls,关系只在 topics/facades 维护。
# AI 处理跨应用需求时先读本文件,图遍历得出影响面。以下为示例,替换为真实服务。
version: 2

services:
  - id: order-service
    repo: https://github.com/your-org/order-service
    owner: yinn
    description: 订单核心服务
    boundary: |
      负责订单生命周期(创建、支付回调、状态流转)。
      不负责:库存扣减(inventory-service)、履约(fulfillment-service)。
    docs:
      agents: AGENTS.md               # 路径相对各自仓库根目录
      architecture: docs/architecture.md
      api: docs/api.md
    depends_on:                       # 仅 REST 直连 / 跨库;RPC 走 facades、MQ 走 topics
      - id: user-service
        via: REST
        contract: user-service:docs/api.md
        status: active                # active(默认,已生效)| planned(契约定稿未上线)
        spec: "001"

  - id: user-service
    repo: https://github.com/your-org/user-service
    owner: teammate
    description: 用户与鉴权服务
    boundary: |
      负责用户资料、登录鉴权、权限。
      不负责:订单、支付。
    docs:
      agents: AGENTS.md
      architecture: docs/architecture.md
      api: docs/api.md
    depends_on: []

  - id: inventory-service
    repo: https://github.com/your-org/inventory-service
    owner: teammate
    description: 库存服务
    boundary: |
      负责 SKU 库存扣减、回补、库存查询。
      不负责:订单状态、履约。
    docs:
      agents: AGENTS.md
      architecture: docs/architecture.md
      api: docs/api.md
    depends_on: []

  - id: notification-service
    repo: https://github.com/your-org/notification-service
    owner: teammate
    description: 通知服务
    boundary: |
      负责站内信、短信、推送的发送。
      不负责:通知内容的业务判定(由各业务方决定发不发)。
    docs:
      agents: AGENTS.md
      architecture: docs/architecture.md
      api: docs/api.md
    depends_on: []

# ── MQ topic:一等实体,天然表达"一产多消"(order.created 被库存与通知同时消费) ──
topics:
  - name: order.created
    owner: order-service              # schema 归属(契约定义方)
    contract: order-service:docs/events/order-created.md
    producers: [order-service]
    consumers: [inventory-service, notification-service]
    status: active
    spec: "001"

# ── RPC facade 接口:一等实体(接口级),天然表达"一接口多调用" ──
facades:
  - id: user-facade
    owner: user-service
    via: Dubbo                        # Dubbo | SOFA | gRPC | Feign
    contract: user-service:docs/api.md   # 方法签名在契约文档,registry 不重复
    called_by: [order-service]
    status: active
    spec: "001"
```

- [ ] **Step 2: 校验通过**

Run: `python3 scripts/registry-check.py`
Expected: `4 个服务, 1 个 topic, 1 个 facade, 0 个错误, ...`,退出码 0。

- [ ] **Step 3: 提交**

```bash
git add registry/services.yaml
git commit -m "feat(registry): 迁移 services.yaml 到 v2(topic/facade/boundary 示例)"
```

---

## Task 3: registry-graph.py 渲染 topic/facade 节点(TDD)

**Files:**
- Create: `tests/test_registry_graph.py`
- Modify: `scripts/registry-graph.py`

- [ ] **Step 1: 写失败测试**

创建 `tests/test_registry_graph.py`:

```python
from conftest import run_graph
from test_registry_check import _valid_v2


def test_graph_renders_topic_and_facade(make_hub):
    hub = make_hub(_valid_v2())
    r = run_graph(hub)
    assert r.returncode == 0, r.stderr
    out = (hub / "docs" / "service-graph.md").read_text(encoding="utf-8")
    # 服务节点
    assert "order_service" in out
    # topic 节点(hexagon)与产/消边
    assert "order.created" in out
    assert "produces" in out
    assert "consumes" in out
    # facade 节点与调用边
    assert "user-facade" in out
    assert "Dubbo" in out
```

- [ ] **Step 2: 运行,确认失败**

Run: `python3 -m pytest tests/test_registry_graph.py -v`
Expected: FAIL(旧脚本不输出 topic/facade)。

- [ ] **Step 3: 改 registry-graph.py**

把 `node_id`(原第 42-43 行)改为兼容 topic 名里的点号,并新增前缀 helper:

```python
def node_id(sid: str) -> str:
    return sid.replace("-", "_").replace(".", "_")


def s_node(sid: str) -> str:  # 服务
    return "s_" + node_id(sid)


def t_node(name: str) -> str:  # topic
    return "t_" + node_id(name)


def f_node(fid: str) -> str:  # facade
    return "f_" + node_id(fid)
```

把 `main()` 的节点/边生成(原第 46-71 行)整体替换:

```python
def main() -> None:
    reg = yaml.safe_load((ROOT / "registry" / "services.yaml").read_text(encoding="utf-8"))
    services = reg.get("services") or []
    topics = reg.get("topics") or []
    facades = reg.get("facades") or []
    known = {s["id"] for s in services}

    lines = [
        "# 服务依赖图",
        "",
        "> 由 `scripts/registry-graph.py` 从 `registry/services.yaml` 自动生成,勿手改。",
        "> 矩形=服务,六边形=MQ topic,平行四边形=facade 接口。",
        "",
        "```mermaid",
        "graph LR",
    ]
    # 服务节点(矩形)
    for s in services:
        desc = s.get("description", "")
        lines.append(f'  {s_node(s["id"])}["{s["id"]}<br/><small>{desc}</small>"]')
    # REST/DB 直连依赖
    for s in services:
        for dep in s.get("depends_on") or []:
            via = dep.get("via", "")
            if dep["id"] not in known:
                print(f'警告: {s["id"]} 依赖了未登记的服务 {dep["id"]}')
            lines.append(f'  {s_node(s["id"])} -->|{via}| {s_node(dep["id"])}')
    # topic 节点(六边形)+ 产/消边
    for t in topics:
        name = t["name"]
        lines.append(f'  {t_node(name)}{{{{"{name}"}}}}')
        for p in t.get("producers") or []:
            lines.append(f'  {s_node(p)} -->|produces| {t_node(name)}')
        for c in t.get("consumers") or []:
            lines.append(f'  {t_node(name)} -->|consumes| {s_node(c)}')
    # facade 节点(平行四边形)+ 调用/归属边
    for f in facades:
        fid = f["id"]
        via = f.get("via", "")
        lines.append(f'  {f_node(fid)}[/"{fid}"/]')
        if f.get("owner"):
            lines.append(f'  {f_node(fid)} -.owns.-> {s_node(f["owner"])}')
        for caller in f.get("called_by") or []:
            lines.append(f'  {s_node(caller)} -->|{via}| {f_node(fid)}')
    lines += ["```", ""]

    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"已生成 {OUT.relative_to(ROOT)}")
```

- [ ] **Step 4: 运行,确认通过**

Run: `python3 -m pytest tests/test_registry_graph.py -v`
Expected: PASS。

- [ ] **Step 5: 重新生成真实图并核对**

Run: `python3 scripts/registry-graph.py && cat docs/service-graph.md`
Expected: 图含 4 个服务矩形、`order.created` 六边形(order-service produces、inventory-service+notification-service consumes)、`user-facade` 平行四边形(order-service 经 Dubbo 调用、owns 指向 user-service)。

- [ ] **Step 6: 提交**

```bash
git add scripts/registry-graph.py tests/test_registry_graph.py docs/service-graph.md
git commit -m "feat(registry): 依赖图渲染 topic(六边形)与 facade(平行四边形)节点"
```

---

## Task 4: 更新 registry/README.md 维护规范

**Files:**
- Modify: `registry/README.md`

- [ ] **Step 1: 替换「字段说明」小节**

把 `registry/README.md` 第 7-20 行(`## 字段说明` 到"避免双向声明打架。"那段)替换为:

````markdown
## schema v2:三类关系

registry 用三类关系描述系统,**各有归处、关系单一来源**(同一关系不存两处):

| 关系 | 归处 | 形状 |
|---|---|---|
| REST 直连 / 跨库访问 | `services[].depends_on` | 有向点对点,`via: REST` 或 `DB` |
| MQ 发布/订阅 | `topics[]` | `producers[]` → topic → `consumers[]`,天然一产多消 |
| RPC facade 接口调用 | `facades[]` | `called_by[]` → facade → `owner`,天然一接口多调用 |

**服务条目不镜像 `produces/consumes/calls`**——要看某服务收发什么,遍历 topics/facades 即可(`registry-graph.py` 会渲染)。RPC/MQ 一律不进 `depends_on`。

### services[] 字段

| 字段 | 必填 | 说明 |
|---|---|---|
| id | ✅ | 服务唯一标识,kebab-case,与仓库名一致 |
| repo | ✅ | 仓库地址 |
| owner | ✅ | 负责人(registry 变更需其评审) |
| description | ✅ | 一句话职责 |
| boundary | 建议 | 服务边界:负责什么 / **不**负责什么。需求分析据此输出各服务边界。人工维护,代码推不出 |
| docs | ✅ | 文档指针(agents/architecture/api,相对仓库根) |
| depends_on | ✅(可为 []) | **仅** REST 直连 / 跨库:id + via(`REST`\|`DB`)+ contract + 可选 status/spec |

### topics[] 字段

| 字段 | 必填 | 说明 |
|---|---|---|
| name | ✅ | topic 名(如 `order.created`),全局唯一 |
| owner | ✅ | schema 归属服务(契约定义方) |
| contract | 建议 | 事件 schema 文档指针 |
| producers | ✅(≥1) | 生产该 topic 的服务(可多个) |
| consumers | ✅(可为 []) | 消费该 topic 的服务(可多个) |
| status / spec | 可选 | `active`\|`planned`;引入该 topic 的总 spec 编号 |

### facades[] 字段

| 字段 | 必填 | 说明 |
|---|---|---|
| id | ✅ | facade 接口标识,kebab-case,全局唯一 |
| owner | ✅ | 提供该接口的服务 |
| via | ✅ | `Dubbo`\|`SOFA`\|`gRPC`\|`Feign` |
| contract | 建议 | 方法签名文档指针(registry 不抄方法) |
| called_by | ✅(可为 []) | 调用该接口的服务(可多个) |
| status / spec | 可选 | 同上 |
````

- [ ] **Step 2: 更新「自动校验」小节**

把「## 自动校验(CI)」小节的三条要点(原第 32-34 行)替换为:

```markdown
- 结构:yaml 合法、必填字段齐全、id 唯一且 kebab-case、depends_on via 仅 REST/DB、facade via 合法、status 合法
- 引用:depends_on / topic producers·consumers / facade owner·called_by 指向的服务必须已登记(未登记 → 报错)
- 完整性:每个 topic ≥1 producer、每个 facade 有 owner;topic name / facade id 全局唯一
- 提示:服务条目误写 produces/consumes/calls、孤立服务、依赖图是否过期
```

- [ ] **Step 3: 更新「定期校准」小节的扫描证据源**

把「## 定期校准」段里"RPC 注解…MQ 生产消费"那句(原第 38 行中部)确认覆盖新模型——把该句改为:

```markdown
用 **registry-sync** 在应用仓库扫描真实调用——RPC facade(Feign/Dubbo/SOFA 提供方与消费方注解及 XML)映射到 `facades[]`、MQ 生产/消费(`@RocketMQMessageListener`/`@KafkaListener`/`rocketMQTemplate`/`kafkaTemplate`)映射到 `topics[]`、REST/跨库映射到 `depends_on`——与 registry 声明对比,报告缺失/多余/方式不符。
```

- [ ] **Step 4: 提交**

```bash
git add registry/README.md
git commit -m "docs(registry): README 更新 v2 三类关系字段与校验规范"
```

---

## Task 5: cross-app-spec 图遍历影响面(两处同源)

**Files:**
- Modify: `plugin/skills/cross-app-spec/SKILL.md`(第 2 步)
- Modify: `prompts/cross-app-spec.md`(第 2 步)

- [ ] **Step 1: 改 skill 的影响面分析步骤**

`plugin/skills/cross-app-spec/SKILL.md` 第 2 步(`2. **影响面分析**...`整段)替换为:

```markdown
2. **影响面分析(图遍历)**:读 hub `registry/services.yaml`(schema v2:services + topics + facades),从需求 NL 定位种子(直接点名或语义命中的 service / topic / facade),沿三类关系扩散:
   - 种子服务作为某 topic 的 **producer** → 拉该 topic 全部 `consumers`(下游影响面)
   - 种子服务作为某 topic 的 **consumer** → 标注该 topic 的 `producer`(可能需协调)
   - 种子服务作为某 facade 的 **called_by** → 拉 facade `owner`(上游接口可能要改);作为 **owner** → 拉全部 `called_by`
   - 种子本身是 topic/facade → 直接拉其全部关联服务
   - REST/跨库沿 `depends_on` 扩散
   把推断结果给用户确认,不确定的标存疑。涉及服务若 hub `.vibe-paths.local.yaml` 有映射(见 `docs/local-paths.md`),标注「本地可直达」。**每个受影响服务据其 `boundary` 与交互角色,给一句「本需求中它要改什么」。**
```

- [ ] **Step 2: 改 skill 第 3 步的影响面表描述**

`plugin/skills/cross-app-spec/SKILL.md` 第 3 步里"影响面表(服务、仓库、变更类型;子 spec 列暂留空)"一行改为:

```markdown
   - 影响面表(服务、**边界**、**交互方式**、变更类型;子 spec 列暂留空)
```

- [ ] **Step 3: 同步改 prompt 副本**

对 `prompts/cross-app-spec.md` 做与 Step 1、Step 2 **完全相同**的两处替换(第 9 行影响面分析整段、第 11 行影响面表那行),措辞逐字一致。

- [ ] **Step 4: 核对两处同源一致**

Run: `diff <(sed -n '/影响面分析/,/本地可直达/p' plugin/skills/cross-app-spec/SKILL.md) <(sed -n '/影响面分析/,/本地可直达/p' prompts/cross-app-spec.md)`
Expected: 无差异输出(两处措辞一致)。

- [ ] **Step 5: 提交**

```bash
git add plugin/skills/cross-app-spec/SKILL.md prompts/cross-app-spec.md
git commit -m "feat(cross-app-spec): 影响面分析升级为图遍历,输出边界与交互方式"
```

---

## Task 6: 影响面表模板加列(两处同源)

**Files:**
- Modify: `plugin/skills/cross-app-spec/references/spec-template.md`
- Modify: `specs/_template/spec.md`

- [ ] **Step 1: 改 spec-template.md 的影响面表**

`plugin/skills/cross-app-spec/references/spec-template.md` 的「## 2. 影响面」表格替换为:

```markdown
## 2. 影响面

| 服务 | 边界 | 交互方式 | 变更类型 | 子 spec |
|---|---|---|---|---|
| order-service | 订单生命周期(不含库存) | produces order.created | 事件加字段 | <repo>/specs/NNN-xxx/spec.md |
| inventory-service | SKU 库存扣减 | consumes order.created | 新增消费逻辑 | <repo>/specs/NNN-xxx/spec.md |
```

- [ ] **Step 2: 同步改 _template/spec.md**

对 `specs/_template/spec.md` 的「## 2. 影响面」表格做**完全相同**的替换。

- [ ] **Step 3: 核对两处一致**

Run: `diff plugin/skills/cross-app-spec/references/spec-template.md specs/_template/spec.md`
Expected: 无差异(两文件本就应逐字相同)。

- [ ] **Step 4: 提交**

```bash
git add plugin/skills/cross-app-spec/references/spec-template.md specs/_template/spec.md
git commit -m "feat(cross-app-spec): 总 spec 影响面表新增边界/交互方式列"
```

---

## Task 7: registry-sync 扫描规则 + 边界软提醒(两处同源)

**Files:**
- Modify: `plugin/skills/registry-sync/SKILL.md`
- Modify: `prompts/registry-sync.md`

- [ ] **Step 1: 改 skill 的扫描步骤**

`plugin/skills/registry-sync/SKILL.md` 第 2 步(`2. 扫描代码找出**真实**对外依赖...`整个列表)替换为:

```markdown
2. 扫描代码找出**真实**对外关系,按 v2 三类归位(注解与构建配置是重要证据源):
   - **facade 提供**(→ `facades[].owner`):`@DubboService`/`@Service`(Dubbo)、`@SofaService`、gRPC service impl
   - **facade 调用**(→ `facades[].called_by`):`@FeignClient(name=...)`、`@DubboReference`/`@Reference`、`@SofaReference` 及 XML(`<dubbo:reference>`/`<sofa:reference>`);按注解服务名/接口归属映射对端 facade。核对对端接口真实存在时,先 `python3 scripts/vibe-paths.py resolve <对端 service-id>` 取本地路径;未登记则列待确认,不要 clone
   - **构建坐标**:pom.xml / build.gradle 引用其他服务的 `xxx-api`/`xxx-client`/`xxx-facade` artifact → 推测对端 facade
   - **MQ 生产**(→ `topics[].producers`):`rocketMQTemplate.send`/`syncSend`/`asyncSend`、`kafkaTemplate.send`、topic 常量定义
   - **MQ 消费**(→ `topics[].consumers`):`@RocketMQMessageListener(topic=...)`、`@KafkaListener(topics=...)`、`@RabbitListener`
   - **REST/跨库**(→ `depends_on`,via 仅 REST/DB):RestTemplate/WebClient/axios/fetch 封装的 base URL 与服务发现名;读写其他服务拥有的库/表(跨库是重依赖也是坏味道,单独标注)
```

- [ ] **Step 2: 改 skill 第 3 步差异分类**

`plugin/skills/registry-sync/SKILL.md` 第 3 步"输出三类差异"改为按实体分组:

```markdown
3. 对比"代码实际" vs "registry 声明",**按 topics / facades / depends_on 三类分别**输出:
   - **缺失**:代码中存在、registry 未声明(最危险,影响面分析会漏)
   - **多余**:registry 声明、代码中已不存在(历史残留)
   - **不符**:producers/consumers/called_by 名单、via 方式或 contract 指针与实际不一致
```

- [ ] **Step 3: 新增边界软提醒(skill 第 5 步之后加第 6 步)**

在 `plugin/skills/registry-sync/SKILL.md` 现第 5 步后追加:

```markdown
6. **边界软提醒**:若本次校准发现某服务**新增**了它 owner 的 facade 或 topic(对外契约面扩大),提示「<service> 新增对外接口/事件,其 registry `boundary` 描述可能需要更新」——不自动改,交用户决定。
```

- [ ] **Step 4: 同步改 prompt 副本**

对 `prompts/registry-sync.md` 做与 Step 1-3 **完全相同**的三处替换(第 2 步扫描列表、第 3 步差异分类、追加边界软提醒步)。

- [ ] **Step 5: 核对两处同源一致**

Run: `diff <(sed -n '/facade 提供/,/单独标注/p' plugin/skills/registry-sync/SKILL.md) <(sed -n '/facade 提供/,/单独标注/p' prompts/registry-sync.md)`
Expected: 无差异输出。

- [ ] **Step 6: 提交**

```bash
git add plugin/skills/registry-sync/SKILL.md prompts/registry-sync.md
git commit -m "feat(registry-sync): 扫描按 v2 三类归位 + 边界软提醒"
```

---

## Task 8: finalize-feature 边界软提醒(三处同源)

**Files:**
- Modify: `plugin/skills/finalize-feature/SKILL.md`
- Modify: `prompts/finalize-feature.md`
- Modify: `plugin/templates/app/prompts/finalize-feature.md`

- [ ] **Step 1: 确认三处当前内容一致**

Run: `diff prompts/finalize-feature.md plugin/templates/app/prompts/finalize-feature.md; echo "exit=$?"`
Expected: 记录当前差异(两个 prompt 副本应基本一致;skill 是完整版)。据此确定在哪一句后插入。

- [ ] **Step 2: 在 skill 第 4 步(hub registry 更新)追加一句边界提醒**

`plugin/skills/finalize-feature/SKILL.md` 第 4 步末尾(依赖变化更新 registry 那句之后)追加:

```markdown
   若本次为本服务**新增**了对外 facade 接口或 MQ topic(producer),提示用户其 registry `boundary` 描述是否需要更新(边界人工维护,不自动改)。
```

- [ ] **Step 3: 同步改两个 prompt 副本**

在 `prompts/finalize-feature.md` 和 `plugin/templates/app/prompts/finalize-feature.md` 对应的"更新 hub registry"步骤后,追加与 Step 2 **完全相同**的那句话。

- [ ] **Step 4: 核对三处提醒措辞一致**

Run: `grep -h "boundary" plugin/skills/finalize-feature/SKILL.md prompts/finalize-feature.md plugin/templates/app/prompts/finalize-feature.md`
Expected: 三行,措辞一致。

- [ ] **Step 5: 提交**

```bash
git add plugin/skills/finalize-feature/SKILL.md prompts/finalize-feature.md plugin/templates/app/prompts/finalize-feature.md
git commit -m "feat(finalize-feature): 新增对外接口/事件时提醒复核服务边界"
```

---

## Task 9: 更新 WORKFLOW.md 与 USAGE.md

**Files:**
- Modify: `WORKFLOW.md`(§2.2)
- Modify: `plugin/USAGE.md`

- [ ] **Step 1: 改 WORKFLOW.md §2.2 registry 描述**

`WORKFLOW.md` §2.2 里描述 registry 的那段(现"`registry/services.yaml` 是全系统唯一权威的服务清单... 即可知道'改 A 会影响谁'。")后补一句 schema v2 说明:

```markdown
- registry 用三类关系描述系统:REST/跨库走 `depends_on`、MQ 发布订阅走 `topics`(producers/consumers)、RPC facade 接口走 `facades`(owner/called_by);服务另有 `boundary` 字段声明职责边界。跨应用需求分析由此从"查一层依赖"升级为图遍历,输出"涉及哪些服务 + 各自边界 + 如何交互"。
```

- [ ] **Step 2: 改 plugin/USAGE.md 的 registry-sync 与 cross-app-spec 条目**

`plugin/USAGE.md` 第 4 条(cross-app-spec)的"做什么"格改为:

```markdown
| 做什么 | 读 registry(v2:services+topics+facades)图遍历推断影响面给你确认;建 spec(概述、影响面表含边界/交互方式、契约变更、职责拆分、上线顺序);为每个涉及服务生成拷贝即用的 /speckit.specify 启动指令 |
```

第 7 条(registry-sync)的"做什么"格改为:

```markdown
| 做什么 | 扫描代码 → 按 topics/facades/depends_on 三类报告缺失/多余/方式不符(存疑项列证据不静默写入)→ 新增对外接口时提醒复核 boundary → 确认后更新 registry、跑校验、重生成依赖图 |
```

- [ ] **Step 3: 提交**

```bash
git add WORKFLOW.md plugin/USAGE.md
git commit -m "docs: WORKFLOW/USAGE 同步 registry v2 拓扑模型"
```

---

## Task 10: 全量校验与 CI 接线

**Files:**
- Modify: `.github/workflows/registry-check.yml`

- [ ] **Step 1: 跑全部测试与校验**

Run: `python3 -m pytest tests/ -v && python3 scripts/registry-check.py && python3 scripts/registry-graph.py`
Expected: pytest 全绿;check 退出码 0;graph 生成成功。

- [ ] **Step 2: 给 CI 增测试步骤**

`.github/workflows/registry-check.yml` 的 `check` job,在 `Validate registry` 步骤前插入:

```yaml
      - name: Install test deps
        run: pip install pyyaml pytest
      - name: Run script tests
        run: python3 -m pytest tests/ -v
```

(把原有的 `- run: pip install pyyaml` 合并进上面的 Install 步骤,避免重复。)

- [ ] **Step 3: 提交**

```bash
git add .github/workflows/registry-check.yml
git commit -m "ci: registry-check workflow 增加脚本测试步骤"
```

---

## Task 11: 发版 0.7.0

**Files:**
- Modify(由 `vibe-release.py` 处理):`VERSION`、`plugin/.claude-plugin/plugin.json`、`.claude-plugin/marketplace.json`(两处)、`CHANGELOG.md`、`vibe-kit.plugin`

- [ ] **Step 1: 先查漂移**

Run: `python3 scripts/vibe-release.py check`
Expected: 报告当前版本号一致性与 skill 名册状态(本次未增删 skill,名册应无变化)。

- [ ] **Step 2: bump 到 0.7.0**

Run: `python3 scripts/vibe-release.py bump 0.7.0`
Expected: 四处版本号改为 0.7.0、起草 CHANGELOG 条目、重打包 `.plugin`。

- [ ] **Step 3: 校对并补全 CHANGELOG**

编辑 `CHANGELOG.md` 的 `[0.7.0]` 条目,确保包含:

```markdown
### Changed
- **registry schema v1 → v2(破坏性)**:`depends_on.via` 收窄为 `REST`/`DB`;MQ 关系迁移到 `topics[]`(producers/consumers)、RPC facade 迁移到 `facades[]`(owner/called_by);服务新增 `boundary` 字段。关系单一来源,服务条目不再镜像 produces/consumes/calls。
- cross-app-spec 影响面分析升级为图遍历,总 spec 影响面表新增「边界」「交互方式」列。
- registry-sync 扫描按三类归位,新增对外接口时提醒复核 boundary;finalize-feature 同。
- registry-check / registry-graph 支持 topics/facades;新增 `tests/` 脚本测试并接入 CI。

### 迁移指引
- 已有 registry:`version: 1 → 2`;把 `via: gRPC/Dubbo/SOFA` 的 depends_on 改写为 `facades[]` 条目、`via: MQ` 改写为 `topics[]` 条目;给各服务补 `boundary`。跑 `python3 scripts/registry-check.py` 校验。
```

- [ ] **Step 4: 校验四处版本一致**

Run: `python3 scripts/vibe-release.py check`
Expected: 版本号四处一致,无漂移错误。

- [ ] **Step 5: 提交**

```bash
git add -A
git commit -m "release: vibe-kit v0.7.0 — registry 拓扑模型升级(topic/facade 一等实体 + boundary)"
```

- [ ] **Step 6: 发布提示(交用户手动)**

告知用户:如需发布,`git push` 后打 tag `v0.7.0`(CI 自动发 Release)。**不代替用户 push 或打 tag。**

---

## 收尾验收(对照 spec §9)

- [ ] registry/services.yaml 用 v2 描述,含 topic 一产多消、facade 一接口多调用、REST 依赖 —— Task 2
- [ ] registry-check 通过,且对坏引用/无 producer/facade 违规 via 报错 —— Task 1 测试覆盖
- [ ] registry-graph 区分服务/topic/facade 三类节点 —— Task 3
- [ ] cross-app-spec skill 与 prompt 一致,影响面为图遍历、输出边界与交互方式 —— Task 5 Step 4 diff
- [ ] registry-sync skill 与 prompt 一致,覆盖 MQ 生产消费与 facade 提供调用,含边界软提醒 —— Task 7 Step 5 diff
- [ ] 版本四处一致、CHANGELOG 有条目、.plugin 重打包 —— Task 11
- [ ] 走查:用一个虚构跨应用需求跑 cross-app-spec,影响面表含"服务+边界+交互方式+改造点"(人工验收,非脚本)
```

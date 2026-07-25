from conftest import run_check


def _valid_v3():
    """一份合法的 v3 registry:1 topic 一产多消、1 条服务级 RPC 依赖。"""
    return {
        "version": 3,
        "services": [
            {"id": "order-service", "repo": "https://x/order", "owner": "a",
             "description": "订单", "boundary": "负责订单;不负责库存。",
             "docs": {"agents": "AGENTS.md"},
             "depends_on": [{"id": "user-service", "via": "Dubbo",
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
    }


def test_valid_v3_passes(make_hub):
    r = run_check(make_hub(_valid_v3()))
    assert r.returncode == 0, r.stdout


def test_topic_producer_must_be_known_service(make_hub):
    reg = _valid_v3()
    reg["topics"][0]["producers"] = ["ghost-service"]
    r = run_check(make_hub(reg))
    assert r.returncode == 1
    assert "ghost-service" in r.stdout


def test_topic_needs_at_least_one_producer(make_hub):
    reg = _valid_v3()
    reg["topics"][0]["producers"] = []
    r = run_check(make_hub(reg))
    assert r.returncode == 1
    assert "producer" in r.stdout.lower()


def test_depends_on_accepts_rpc_via(make_hub):
    """v3 起 RPC 折叠进 depends_on,Dubbo/SOFA/gRPC/Feign 都合法。"""
    for via in ("REST", "DB", "Dubbo", "SOFA", "gRPC", "Feign"):
        reg = _valid_v3()
        reg["services"][0]["depends_on"][0]["via"] = via
        r = run_check(make_hub(reg))
        assert r.returncode == 0, f"via={via} 应合法: {r.stdout}"


def test_depends_on_via_rejects_mq(make_hub):
    """MQ 关系归 topics[],不允许写进 depends_on。"""
    reg = _valid_v3()
    reg["services"][0]["depends_on"][0]["via"] = "MQ"
    r = run_check(make_hub(reg))
    assert r.returncode == 1
    assert "via" in r.stdout
    assert "order-service" in r.stdout


def test_legacy_facades_rejected_with_migration_hint(make_hub):
    """v2 遗留的顶层 facades[] 要报明确的迁移错误,而不是难懂的字段错误。"""
    reg = _valid_v3()
    reg["facades"] = [{"id": "user-facade", "owner": "user-service",
                       "via": "Dubbo", "called_by": ["order-service"]}]
    r = run_check(make_hub(reg))
    assert r.returncode == 1
    assert "facades" in r.stdout
    assert "depends_on" in r.stdout   # 告诉用户折叠成什么


def test_boundary_required(make_hub):
    """v3 起 boundary 必填:facade 拿掉后它是唯一能表达"这个服务负责什么"的字段。"""
    reg = _valid_v3()
    del reg["services"][0]["boundary"]
    r = run_check(make_hub(reg))
    assert r.returncode == 1
    assert "boundary" in r.stdout


def test_boundary_without_negative_half_warns(make_hub):
    """只写"负责什么"、不写"不负责什么"时给 WARN(不阻止)。"""
    reg = _valid_v3()
    reg["services"][0]["boundary"] = "负责订单生命周期。"
    r = run_check(make_hub(reg))
    assert r.returncode == 0
    assert "不负责" in r.stdout


def test_missing_contract_warns(make_hub):
    """contract 是消费方找契约文档的唯一入口,缺了要提醒(不阻止)。"""
    reg = _valid_v3()
    del reg["services"][0]["depends_on"][0]["contract"]
    r = run_check(make_hub(reg))
    assert r.returncode == 0
    assert "contract" in r.stdout


def test_bare_path_contract_warns(make_hub):
    """裸路径没有 `<service-id>:` 前缀,无法判断属于哪个仓库。"""
    reg = _valid_v3()
    reg["services"][0]["depends_on"][0]["contract"] = "docs/api.md"
    r = run_check(make_hub(reg))
    assert r.returncode == 0
    assert "前缀" in r.stdout


def test_contract_pointing_at_wrong_service_warns(make_hub):
    """契约由提供方维护:依赖的 contract 必须指向对端,不是自己。"""
    reg = _valid_v3()
    reg["services"][0]["depends_on"][0]["contract"] = "order-service:docs/api.md"
    r = run_check(make_hub(reg))
    assert r.returncode == 0
    assert "应为 user-service" in r.stdout


def test_url_contract_accepted(make_hub):
    """外部 API 门户用 URL,允许(弱于入库文档但不误报)。"""
    reg = _valid_v3()
    reg["services"][0]["depends_on"][0]["contract"] = "https://api-portal.corp/user-service"
    r = run_check(make_hub(reg))
    assert r.returncode == 0
    assert "contract" not in r.stdout


def test_topic_contract_must_point_at_owner(make_hub):
    """topic 的 schema 由 owner 定义,contract 前缀应是 owner。"""
    reg = _valid_v3()
    reg["topics"][0]["contract"] = "inventory-service:docs/events/x.md"  # owner 是 order-service
    r = run_check(make_hub(reg))
    assert r.returncode == 0
    assert "应为 order-service" in r.stdout


def test_duplicate_topic_name(make_hub):
    reg = _valid_v3()
    reg["topics"].append(dict(reg["topics"][0]))
    r = run_check(make_hub(reg))
    assert r.returncode == 1
    assert "重复" in r.stdout


def test_service_mirror_field_warns(make_hub):
    reg = _valid_v3()
    reg["services"][0]["produces"] = ["order.created"]
    r = run_check(make_hub(reg))
    assert r.returncode == 0
    assert "produces" in r.stdout  # 提示不要在服务条目镜像关系


def test_schema_version_required(make_hub):
    reg = _valid_v3()
    del reg["version"]
    r = run_check(make_hub(reg))
    assert r.returncode == 1
    assert "version" in r.stdout


def test_schema_version_2_rejected(make_hub):
    """v2 是上一代 schema,必须显式拒绝并指向迁移指引。"""
    reg = _valid_v3()
    reg["version"] = 2
    r = run_check(make_hub(reg))
    assert r.returncode == 1
    assert "version" in r.stdout
    assert "迁移" in r.stdout


def test_graph_freshness_by_content_hash(make_hub):
    from conftest import run_graph

    hub = make_hub(_valid_v3())
    # 未生成图时提示生成
    r = run_check(hub)
    assert "service-graph.md" in r.stdout
    # 生成后无过期警告
    assert run_graph(hub).returncode == 0
    r = run_check(hub)
    assert r.returncode == 0, r.stdout
    assert "过期" not in r.stdout
    # services.yaml 内容变化后报过期(与 mtime 无关)
    reg = _valid_v3()
    reg["services"][0]["description"] = "订单核心(改)"
    make_hub(reg)
    r = run_check(hub)
    assert "过期" in r.stdout
    assert r.returncode == 0  # 仅警告

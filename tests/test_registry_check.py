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

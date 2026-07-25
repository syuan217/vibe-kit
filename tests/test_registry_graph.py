from conftest import run_graph
from test_registry_check import _valid_v3


def test_graph_renders_topic_and_dependency(make_hub):
    hub = make_hub(_valid_v3())
    r = run_graph(hub)
    assert r.returncode == 0, r.stderr
    out = (hub / "docs" / "service-graph.md").read_text(encoding="utf-8")
    # 服务节点
    assert "order_service" in out
    # topic 节点(hexagon)与产/消边
    assert "order.created" in out
    assert "t_order_created" in out   # 锁定 topic 节点 id 的 dot→underscore 处理
    assert "produces" in out
    assert "consumes" in out
    # v3:RPC 是服务级边,via 作标签;不再有 facade 节点
    assert "s_order_service -->|Dubbo| s_user_service" in out
    assert "f_" not in out


def test_graph_embeds_source_hash(make_hub):
    hub = make_hub(_valid_v3())
    assert run_graph(hub).returncode == 0
    out = (hub / "docs" / "service-graph.md").read_text(encoding="utf-8")
    assert "<!-- source-hash:" in out  # registry-check 以此判断新鲜度


def test_graph_escapes_quotes_in_description(make_hub):
    reg = _valid_v3()
    reg["services"][0]["description"] = '订单"核心"服务'
    hub = make_hub(reg)
    r = run_graph(hub)
    assert r.returncode == 0, r.stderr
    out = (hub / "docs" / "service-graph.md").read_text(encoding="utf-8")
    assert "订单'核心'服务" in out  # mermaid 标签内双引号会破坏渲染,须转义

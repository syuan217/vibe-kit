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
    assert "t_order_created" in out   # 锁定 topic 节点 id 的 dot→underscore 处理
    assert "produces" in out
    assert "consumes" in out
    # facade 节点与调用边
    assert "user-facade" in out
    assert "Dubbo" in out

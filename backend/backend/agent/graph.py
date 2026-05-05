from langgraph.graph import StateGraph, END
from backend.agent.state import AgentState

# ── Node imports (sẽ implement từng cái sau) ───────────────
from backend.agent.nodes.reasoning_node import reasoning_node
from backend.agent.nodes.router_node import router_node, route_decision
from backend.agent.nodes.consultant_node import consultant_node
from backend.agent.nodes.order_node import order_node
from backend.agent.nodes.response_node import response_node


def build_graph() -> StateGraph:
    graph = StateGraph(AgentState)

    # ── Đăng ký nodes ──────────────────────────────────────
    graph.add_node("reasoning_node", reasoning_node)
    graph.add_node("router_node", router_node)
    graph.add_node("consultant_node", consultant_node)
    graph.add_node("order_node", order_node)
    graph.add_node("response_node", response_node)

    # ── Entry point ────────────────────────────────────────
    graph.set_entry_point("reasoning_node")

    # ── Edges cố định ──────────────────────────────────────
    graph.add_edge("reasoning_node", "router_node")
    graph.add_edge("consultant_node", "response_node")
    graph.add_edge("order_node", "response_node")
    graph.add_edge("response_node", END)

    # ── Conditional edge: router_node → ? ──────────────────
    graph.add_conditional_edges(
        "router_node",
        route_decision,
        {
            "consultant": "consultant_node",
            "order": "order_node",
            "response": "response_node",   # general / fallback
        },
    )

    return graph.compile()


# Singleton — import và dùng ở runner.py
agent_graph = build_graph()

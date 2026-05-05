from backend.agent.state import AgentState


async def router_node(state: AgentState) -> AgentState:
    """Checkpoint thuần — logic điều hướng nằm trong route_decision()."""
    return state


def route_decision(state: AgentState) -> str:
    """
    Ưu tiên pending_step (multi-turn) trước,
    sau đó mới xét intent mới từ Reasoning Agent.
    """
    pending = state.get("pending_step")
    intent = state.get("current_intent", "general")

    # ── Đang giữa 1 flow chưa xong ─────────────────────────
    if pending in ("ask_quantity", "ask_phone", "ask_name",
                   "ask_email", "ask_note", "ask_order_type",
                   "confirm_order"):
        return "order"

    if pending in ("ask_budget", "ask_purpose"):
        return "consultant"

    # ── Intent mới ─────────────────────────────────────────
    if intent == "consult":
        return "consultant"

    if intent in ("order", "check_stock"):
        return "order"

    # fallback
    return "response"

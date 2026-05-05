import asyncio
from backend.agent.graph import agent_graph
from backend.agent.state import AgentState
from backend.agent.memory import load_memory, save_memory
from backend.agent.nodes.order_node import _fetch_product
from backend.redis_client import sync_redis_client
from backend.database.db_models import SessionLocal, Message as MessageModel


async def _run_agent_async(
    session_id: str,
    messages: list,
    context_product_id: str = None,
) -> None:
    channel = f"session:{session_id}"

    try:
        chat_history = messages[:-1]
        user_input = messages[-1]["content"]

        # ── Load memory từ Redis ────────────────────────────
        memory = load_memory(session_id)
        current_product = memory.get("current_product")

        # Nếu UI truyền product_id → ưu tiên hơn memory
        # (user đang nhìn vào sản phẩm cụ thể lúc hỏi)
        if context_product_id:
            fetched = _fetch_product(context_product_id)
            if fetched:
                current_product = fetched

        initial_state: AgentState = {
            # Input
            "session_id": session_id,
            "user_input": user_input,
            "chat_history": chat_history,

            # Memory — merge từ Redis + UI context
            "current_product":    current_product,
            "current_intent":     memory.get("current_intent"),
            "pending_step":       memory.get("pending_step"),
            "suggested_products": memory.get("suggested_products") or [],
            "order_info":         memory.get("order_info"),
            "consultant_context": memory.get("consultant_context"),

            # Working state — luôn reset mỗi turn
            "extracted_entities": {},
            "node_output": {},
            "last_node": "",
            "final_response": "",
        }

        # ── Chạy graph ──────────────────────────────────────
        final_state = await agent_graph.ainvoke(initial_state)

        # ── Save memory về Redis ────────────────────────────
        save_memory(session_id, final_state)

        # ── Lưu response vào DB ─────────────────────────────
        response_text = final_state.get("final_response", "")
        with SessionLocal() as db:
            db.add(MessageModel(
                session_id=session_id,
                role="assistant",
                content=response_text,
            ))
            db.commit()

        # response_node đã stream token → chỉ cần publish [DONE]
        sync_redis_client.publish(channel, "[DONE]")

    except Exception as e:
        sync_redis_client.publish(channel, f"[ERROR]{str(e)}")


def run_agent(
    session_id: str,
    messages: list,
    context_product_id: str = None,
) -> None:
    asyncio.run(_run_agent_async(session_id, messages, context_product_id))
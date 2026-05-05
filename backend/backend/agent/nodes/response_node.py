from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from backend.agent.state import AgentState
from backend.redis_client import sync_redis_client
import json

_llm = ChatOpenAI(model="gpt-4o", temperature=0.4, streaming=True)

# ── Prompt theo từng context ────────────────────────────────

_PROMPTS = {
    "consultant_success": """Bạn là nhân viên tư vấn thân thiện.
Dựa vào danh sách sản phẩm gợi ý bên dưới, viết câu trả lời tự nhiên cho khách.
Giới thiệu ngắn gọn từng sản phẩm, nêu điểm nổi bật, gợi ý nên chọn cái nào và tại sao.
Cuối câu hỏi xem khách có muốn biết thêm hoặc đặt hàng không.
Trả lời bằng tiếng Việt, thân thiện, không dùng markdown.""",

    "consultant_need_more_info": """Bạn là nhân viên tư vấn thân thiện.
Hỏi thêm thông tin từ khách theo câu hỏi được cung cấp.
Ngắn gọn, tự nhiên, không hỏi nhiều thứ một lúc.
Trả lời bằng tiếng Việt.""",

    "consultant_no_result": """Bạn là nhân viên tư vấn thân thiện.
Thông báo lịch sự rằng hiện tại không có sản phẩm phù hợp với nhu cầu của khách.
Đề nghị khách mô tả lại nhu cầu hoặc xem toàn bộ danh sách sản phẩm.
Trả lời bằng tiếng Việt.""",

    "order_need_more_info": """Bạn là nhân viên xử lý đơn hàng thân thiện.
Hỏi thêm thông tin còn thiếu theo câu hỏi được cung cấp.
Ngắn gọn, lịch sự, chỉ hỏi 1 thứ.
Trả lời bằng tiếng Việt.""",

    "order_confirmed": """Bạn là nhân viên xử lý đơn hàng thân thiện.
Thông báo đặt hàng thành công, nhắc lại thông tin đơn hàng ngắn gọn.
Cảm ơn khách và hỏi có cần hỗ trợ thêm không.
Trả lời bằng tiếng Việt.""",

    "order_out_of_stock": """Bạn là nhân viên tư vấn thân thiện.
Thông báo sản phẩm đã hết hàng, xin lỗi khách.
Đề nghị khách xem sản phẩm tương tự hoặc quay lại sau.
Trả lời bằng tiếng Việt.""",

    "order_preorder_available": """Bạn là nhân viên tư vấn thân thiện.
Thông báo sản phẩm hết hàng nhưng có thể đặt trước (preorder).
Hỏi khách có muốn preorder không.
Trả lời bằng tiếng Việt.""",

    "order_insufficient_stock": """Bạn là nhân viên tư vấn thân thiện.
Thông báo số lượng tồn kho không đủ theo yêu cầu.
Đề nghị phương án thay thế (mua số lượng còn lại hoặc preorder nếu có).
Trả lời bằng tiếng Việt.""",

    "order_preorder_not_allowed": """Bạn là nhân viên tư vấn thân thiện.
Thông báo sản phẩm không hỗ trợ đặt trước.
Hỏi khách có muốn mua hàng có sẵn không.
Trả lời bằng tiếng Việt.""",

    "order_product_not_found": """Bạn là nhân viên tư vấn thân thiện.
Thông báo không tìm thấy sản phẩm.
Hỏi lại khách muốn mua sản phẩm nào.
Trả lời bằng tiếng Việt.""",

    "check_stock_in_stock": """Bạn là nhân viên tư vấn thân thiện.
Thông báo sản phẩm còn hàng với số lượng cụ thể.
Hỏi khách có muốn đặt hàng không.
Trả lời bằng tiếng Việt.""",

    "check_stock_out_of_stock": """Bạn là nhân viên tư vấn thân thiện.
Thông báo sản phẩm đã hết hàng.
Nếu có preorder thì đề nghị, không thì xin lỗi và đề nghị xem sản phẩm khác.
Trả lời bằng tiếng Việt.""",

    "general": """Bạn là trợ lý bán hàng thân thiện của cửa hàng.
Trả lời câu hỏi chung của khách một cách tự nhiên, ngắn gọn.
Nếu không biết, hãy thành thật và đề nghị khách liên hệ trực tiếp.
Trả lời bằng tiếng Việt.""",

    "error": """Bạn là trợ lý bán hàng thân thiện.
Thông báo lỗi xảy ra một cách lịch sự, xin lỗi khách và đề nghị thử lại.
Trả lời bằng tiếng Việt.""",
}


def _resolve_prompt_key(last_node: str, node_output: dict) -> str:
    """Map last_node + status → prompt key."""
    status = node_output.get("status", "")

    if last_node == "consultant":
        return f"consultant_{status}" if f"consultant_{status}" in _PROMPTS else "general"

    if last_node == "order":
        if status == "in_stock":
            return "check_stock_in_stock"
        if status == "out_of_stock":
            return "order_out_of_stock"
        key = f"order_{status}"
        return key if key in _PROMPTS else "general"

    return "general"


def _build_context_message(last_node: str, node_output: dict) -> str:
    """Tạo message context từ node_output để đưa vào prompt."""
    status = node_output.get("status", "")

    if last_node == "consultant":
        if status == "success":
            products = node_output.get("products", [])
            lines = [f"Sản phẩm gợi ý ({len(products)} sản phẩm):"]
            for p in products:
                stock_info = f"Còn {p['stock']} cái" if p["stock"] > 0 else ("Có thể preorder" if p["preorder"] else "Hết hàng")
                lines.append(f"- [{p['product_id']}] {p['name']} | Giá: {p['price']} | {stock_info} | {p['short_desc']}")
            lines.append(f"\nLý do gợi ý: {node_output.get('reasoning', '')}")
            return "\n".join(lines)

        if status == "need_more_info":
            return f"Câu hỏi cần hỏi user: {node_output.get('ask_user', '')}"

    if last_node == "order":
        if status == "confirmed":
            return (
                f"Đặt hàng thành công!\n"
                f"Mã đơn: {node_output.get('order_id')}\n"
                f"Sản phẩm: {node_output.get('product', {}).get('name')}\n"
                f"Số lượng: {node_output.get('quantity')}\n"
                f"Loại: {node_output.get('order_type')}\n"
                f"Tên khách: {node_output.get('name')}"
            )

        if status in ("need_more_info", "ask_product"):
            return f"Câu hỏi cần hỏi user: {node_output.get('ask_user', '')}"

        if status in ("out_of_stock", "preorder_available", "insufficient_stock",
                      "preorder_not_allowed", "product_not_found"):
            product = node_output.get("product", {})
            lines = []
            if product:
                lines.append(f"Sản phẩm: {product.get('name')} | Tồn kho: {product.get('stock')} | Preorder: {product.get('preorder')}")
            if node_output.get("ask_user"):
                lines.append(f"Gợi ý câu trả lời: {node_output.get('ask_user')}")
            if node_output.get("available_stock") is not None:
                lines.append(f"Số lượng còn lại: {node_output.get('available_stock')}")
            return "\n".join(lines)

        if status in ("in_stock",):
            product = node_output.get("product", {})
            return (
                f"Sản phẩm: {product.get('name')}\n"
                f"Tồn kho: {node_output.get('available_stock')} cái"
            )

    return json.dumps(node_output, ensure_ascii=False)


def _build_chat_history(messages: list) -> list:
    result = []
    for m in messages[-6:]:
        if m["role"] == "user":
            result.append(HumanMessage(content=m["content"]))
        elif m["role"] == "assistant":
            result.append(AIMessage(content=m["content"]))
    return result


# ── Main node ──────────────────────────────────────────────

async def response_node(state: AgentState) -> AgentState:
    last_node = state.get("last_node", "general")
    node_output = state.get("node_output", {})
    session_id = state["session_id"]
    channel = f"session:{session_id}"

    # Resolve prompt
    prompt_key = _resolve_prompt_key(last_node, node_output)
    system_prompt = _PROMPTS.get(prompt_key, _PROMPTS["general"])
    context_msg = _build_context_message(last_node, node_output)

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder("chat_history"),
        ("human", "{context}\n\nTin nhắn user: {user_input}"),
    ])

    chain = prompt | _llm

    # Stream từng token → publish lên Redis
    full_response = ""
    async for chunk in chain.astream({
        "context": context_msg,
        "user_input": state["user_input"],
        "chat_history": _build_chat_history(state.get("chat_history", [])),
    }):
        token = chunk.content
        if token:
            full_response += token
            sync_redis_client.publish(channel, token)

    state["final_response"] = full_response
    return state
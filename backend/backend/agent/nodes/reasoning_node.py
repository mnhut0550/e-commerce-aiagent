import json
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from backend.agent.state import AgentState, OrderInfo, ConsultantContext

_llm = ChatOpenAI(model="gpt-4o", temperature=0)

_SYSTEM_PROMPT = """Bạn là module phân tích ngôn ngữ của hệ thống bán hàng.
Nhiệm vụ: đọc tin nhắn user + context → trả về JSON. KHÔNG trả lời user.

## CONTEXT HIỆN TẠI
- pending_step: {pending_step}
- current_product: {current_product_name}
- consultant_context: budget={known_budget}, purpose={known_purpose}
- order_info: {order_info}

## OUTPUT FORMAT (JSON thuần, không markdown)
{{
  "intent": "consult" | "order" | "check_stock" | "general",
  "is_clarification": true | false,
  "refers_to_current": true | false,
  "product_id": null | string,
  "product_keyword": null | string,
  "category": null | string,
  "quantity": null | number,
  "order_type": null | "buy" | "preorder",
  "budget": null | number,
  "purpose": null | string,
  "name": null | string,
  "phone": null | string,
  "email": null | string,
  "note": null | string
}}

## QUY TẮC QUAN TRỌNG

### is_clarification = true khi:
- User đang xác nhận/làm rõ thông tin đã nói, không đổi chủ đề
- Tin nhắn ngắn, bổ sung thêm cho câu trước
- VD: "28 triệu hà" sau khi đã nói "28M" → clarification
- VD: "ý mình là để làm đồ họa" → clarification
- VD: "không, mình nói laptop cơ" → clarification
Khi is_clarification=true: KHÔNG thay đổi intent, chỉ update field mới

### intent
- "consult": hỏi gợi ý, tư vấn, so sánh, xem sản phẩm
- "order": mua, đặt, lấy, order
- "check_stock": hỏi còn hàng không
- "general": chào, cảm ơn, hỏi khác

### refers_to_current = true khi:
- "cái đó", "cái này", "nó", "sản phẩm đó", "ok đặt đi", "lấy đi"
- Đang trong pending_step (user đang trả lời câu hỏi)

### budget
- Chỉ extract số tiền user THỰC SỰ đề cập trong tin nhắn này
- "28M" | "28 triệu" | "28tr" | "28,000,000" → 28000000
- KHÔNG suy luận nếu user không đề cập

### purpose
- Chỉ extract mục đích user THỰC SỰ nói
- "đồ họa", "chơi game", "văn phòng", "học tập"
- KHÔNG suy luận

## FEW-SHOT EXAMPLES

User: "laptop đồ họa khoảng 30 triệu"
→ {{"intent":"consult","is_clarification":false,"refers_to_current":false,"product_keyword":"laptop","category":"laptop","budget":30000000,"purpose":"đồ họa",...}}

User: "28 triệu hà" (context: đang hỏi tư vấn, đã nói budget 28M trước đó)
→ {{"intent":"consult","is_clarification":true,"budget":28000000,...}}

User: "ý mình là để làm việc văn phòng"
→ {{"intent":"consult","is_clarification":true,"purpose":"làm việc văn phòng",...}}

User: "thôi lấy cái MacBook đi"
→ {{"intent":"order","is_clarification":false,"refers_to_current":true,...}}

User: "còn hàng không?"
→ {{"intent":"check_stock","is_clarification":false,"refers_to_current":true,...}}

User: "cái nào rẻ hơn?"
→ {{"intent":"consult","is_clarification":false,"refers_to_current":true,...}}

User: "mình tên Minh, 0909123456"
→ {{"intent":"order","is_clarification":true,"name":"Minh","phone":"0909123456",...}}
"""

_prompt = ChatPromptTemplate.from_messages([
    ("system", _SYSTEM_PROMPT),
    MessagesPlaceholder("chat_history"),
    ("human", "{user_input}"),
])


def _build_chat_history(messages: list) -> list:
    result = []
    for m in messages[-10:]:
        if m["role"] == "user":
            result.append(HumanMessage(content=m["content"]))
        elif m["role"] == "assistant":
            result.append(AIMessage(content=m["content"]))
    return result


def _merge_order_info(existing: OrderInfo | None, entities: dict) -> OrderInfo:
    base: OrderInfo = existing or {
        "product_id": None, "quantity": None, "order_type": None,
        "name": None, "phone": None, "email": None, "note": None,
    }
    for field in ["product_id", "quantity", "order_type", "name", "phone", "email", "note"]:
        val = entities.get(field)
        if val is not None:
            base[field] = val  # type: ignore
    return base


def _merge_consultant_context(
    existing: ConsultantContext | None,
    entities: dict,
) -> ConsultantContext:
    """Merge entities mới vào consultant_context — không ghi đè bằng None."""
    base: ConsultantContext = existing or {
        "budget": None, "purpose": None, "category": None, "keyword": None,
    }
    for field in ["budget", "purpose", "category"]:
        val = entities.get(field)
        if val is not None:
            base[field] = val  # type: ignore
    if entities.get("product_keyword"):
        base["keyword"] = entities["product_keyword"]
    return base


async def reasoning_node(state: AgentState) -> AgentState:
    current_product = state.get("current_product")
    order_info = state.get("order_info")
    consultant_context = state.get("consultant_context") or {}

    context = {
        "pending_step": state.get("pending_step") or "null",
        "current_product_name": current_product["name"] if current_product else "null",
        "known_budget": consultant_context.get("budget") or "chưa biết",
        "known_purpose": consultant_context.get("purpose") or "chưa biết",
        "order_info": json.dumps(order_info, ensure_ascii=False) if order_info else "null",
        "user_input": state["user_input"],
        "chat_history": _build_chat_history(state.get("chat_history", [])),
    }

    chain = _prompt | _llm
    response = await chain.ainvoke(context)

    try:
        raw = response.content.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        entities = json.loads(raw.strip())
    except Exception as e:
        print(f"[ReasoningNode] parse error: {e}\nRaw: {response.content}")
        entities = {"intent": "general"}

    is_clarification = entities.get("is_clarification", False)

    # Giữ nguyên intent nếu là clarification
    if is_clarification and state.get("current_intent"):
        entities["intent"] = state["current_intent"]

    intent = entities.get("intent", "general")
    state["current_intent"] = intent
    state["extracted_entities"] = entities

    # Merge consultant_context — persist budget/purpose
    if intent in ("consult", "check_stock") or is_clarification:
        state["consultant_context"] = _merge_consultant_context(
            state.get("consultant_context"), entities
        )

    # Reset current_product nếu user nhắc sản phẩm mới
    if not entities.get("refers_to_current") and not is_clarification:
        if entities.get("product_id") or entities.get("product_keyword"):
            state["current_product"] = None

    # Merge order_info
    if intent in ("order", "check_stock"):
        if entities.get("refers_to_current") and current_product:
            entities["product_id"] = current_product["product_id"]
        state["order_info"] = _merge_order_info(order_info, entities)

    state["pending_step"] = None
    return state
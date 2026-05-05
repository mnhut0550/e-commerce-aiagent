import json
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from backend.agent.state import AgentState, ProductSnapshot, ConsultantContext
from backend.services.sheets import read_sheet
from cachetools import TTLCache

_cache = TTLCache(maxsize=1, ttl=60)
_llm = ChatOpenAI(model="gpt-4o", temperature=0)

# ── Prompt: LLM chỉ rank + giải thích, Python đã filter trước ─

_SYSTEM_PROMPT = """Bạn là tư vấn viên bán hàng.
Danh sách sản phẩm bên dưới đã được lọc sẵn theo ngân sách và nhu cầu của khách.
Nhiệm vụ: chọn tối đa 3 sản phẩm phù hợp nhất và giải thích ngắn gọn lý do.

## SẢN PHẨM ĐÃ LỌC
{products_json}

## NHU CẦU KHÁCH
- Ngân sách: {budget}
- Mục đích: {purpose}
- Từ khóa: {keyword}

## QUY TẮC BẮT BUỘC
1. CHỈ dùng thông tin có trong full_desc và short_desc để tư vấn
2. KHÔNG đề cập màu sắc, dung lượng, RAM... nếu không có trong mô tả sản phẩm
3. KHÔNG hỏi thêm thông tin kỹ thuật không có trong data
4. Nếu danh sách rỗng → status = "no_result"
5. Nếu chỉ có 1 sản phẩm → vẫn trả về, không cần so sánh

## OUTPUT FORMAT (JSON thuần)
{{
  "status": "success" | "need_more_info" | "no_result",
  "product_ids": ["id1", "id2"],
  "missing_info": null | "budget" | "purpose",
  "ask_user": null | "câu hỏi ngắn nếu need_more_info",
  "reasoning": "lý do chọn (dựa trên mô tả thực tế)"
}}

Khi need_more_info: chỉ hỏi budget HOẶC purpose, không hỏi cả 2 cùng lúc.
Khi hỏi: hỏi ngắn gọn, không hỏi màu, dung lượng, hay thông số không có trong data.
"""

_prompt = ChatPromptTemplate.from_messages([
    ("system", _SYSTEM_PROMPT),
    MessagesPlaceholder("chat_history"),
    ("human", "{user_input}"),
])


# ── Helpers ────────────────────────────────────────────────

def _parse_price(price_str: str) -> int:
    """Convert chuỗi giá về số nguyên."""
    try:
        return int(str(price_str).replace(",", "").replace(".", "").strip())
    except Exception:
        return 0


def _get_products() -> list[ProductSnapshot]:
    if "products" in _cache:
        return _cache["products"]

    rows = read_sheet("PRODUCTS!A1:Z")
    if not rows:
        return []

    headers = rows[0]
    result = []
    for row in rows[1:]:
        p = dict(zip(headers, row))
        if p.get("active", "").lower() != "true":
            continue
        price_int = _parse_price(p.get("price", "0"))
        result.append(ProductSnapshot(
            product_id=p["id"],
            name=p.get("name", ""),
            price=p.get("price", ""),
            price_int=price_int,
            stock=int(p.get("stock", 0)),
            preorder=p.get("preorder", "no").lower() in ("yes", "true"),
            category=p.get("category", "").lower(),
            subcategory=p.get("subcategory", "").lower(),
            short_desc=p.get("short_desc", ""),
            full_desc=p.get("full_desc", p.get("short_desc", "")),
        ))

    _cache["products"] = result
    return result


def _python_filter(
    products: list[ProductSnapshot],
    ctx: ConsultantContext,
    entities: dict,
    suggested: list[str],
) -> list[ProductSnapshot]:
    """
    Python filter trước — LLM không cần tự filter nữa.
    Thứ tự ưu tiên: budget → category → keyword → loại đã gợi
    """
    result = [p for p in products if p["product_id"] not in suggested]

    # Filter theo budget — strict
    budget = ctx.get("budget")
    if budget:
        in_budget = [p for p in result if p["price_int"] <= budget]
        # Nếu không có gì trong budget thì vẫn trả về tất cả (để báo no_result đúng)
        if in_budget:
            result = in_budget

    # Filter theo category từ entities
    category = entities.get("category") or ctx.get("category")
    if category:
        by_cat = [p for p in result if p["category"] == category.lower()]
        if by_cat:
            result = by_cat

    # Nếu lọc hết thì reset suggested và thử lại
    if not result:
        result = [p for p in products]
        if budget:
            in_budget = [p for p in result if p["price_int"] <= budget]
            if in_budget:
                result = in_budget

    # Ưu tiên còn hàng
    in_stock = [p for p in result if p["stock"] > 0]
    return in_stock if in_stock else result


def _serialize(products: list[ProductSnapshot]) -> str:
    return json.dumps([
        {
            "id": p["product_id"],
            "name": p["name"],
            "price": p["price"],
            "stock": p["stock"],
            "preorder": p["preorder"],
            "short_desc": p["short_desc"],
            "full_desc": p["full_desc"],
        }
        for p in products
    ], ensure_ascii=False)


def _build_chat_history(messages: list) -> list:
    result = []
    for m in messages[-6:]:
        if m["role"] == "user":
            result.append(HumanMessage(content=m["content"]))
        elif m["role"] == "assistant":
            result.append(AIMessage(content=m["content"]))
    return result


# ── Main node ──────────────────────────────────────────────

async def consultant_node(state: AgentState) -> AgentState:
    state["last_node"] = "consultant"
    entities = state.get("extracted_entities", {})
    ctx: ConsultantContext = state.get("consultant_context") or {
        "budget": None, "purpose": None, "category": None, "keyword": None,
    }
    suggested = state.get("suggested_products") or []

    all_products = _get_products()

    # Python filter trước — LLM nhận danh sách đã lọc
    filtered = _python_filter(all_products, ctx, entities, suggested)

    # Nếu không có gì sau filter → no_result luôn, không cần gọi LLM
    if not filtered:
        state["node_output"] = {"status": "no_result"}
        state["pending_step"] = None
        return state

    # Cần budget hoặc purpose để tư vấn chính xác?
    need_budget = not ctx.get("budget")
    need_purpose = not ctx.get("purpose")

    # Nếu thiếu cả 2 và có nhiều sản phẩm → hỏi purpose trước
    if need_budget and need_purpose and len(filtered) > 3:
        state["node_output"] = {
            "status": "need_more_info",
            "missing_info": "purpose",
            "ask_user": "Bạn muốn dùng sản phẩm này cho mục đích gì? (VD: làm việc, học tập, giải trí...)",
        }
        state["pending_step"] = "ask_purpose"
        return state

    # Gọi LLM rank và giải thích
    chain = _prompt | _llm
    response = await chain.ainvoke({
        "products_json": _serialize(filtered),
        "budget": f"{ctx.get('budget'):,} VNĐ" if ctx.get("budget") else "không giới hạn",
        "purpose": ctx.get("purpose") or "chưa rõ",
        "keyword": ctx.get("keyword") or entities.get("product_keyword") or "không có",
        "user_input": state["user_input"],
        "chat_history": _build_chat_history(state.get("chat_history", [])),
    })

    try:
        raw = response.content.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        result = json.loads(raw.strip())
    except Exception as e:
        print(f"[ConsultantNode] parse error: {e}")
        result = {"status": "no_result"}

    status = result.get("status", "no_result")

    if status == "need_more_info":
        missing = result.get("missing_info", "purpose")
        state["node_output"] = {
            "status": "need_more_info",
            "missing_info": missing,
            "ask_user": result.get("ask_user"),
        }
        state["pending_step"] = f"ask_{missing}"

    elif status == "success":
        product_ids = result.get("product_ids", [])
        id_map = {p["product_id"]: p for p in filtered}
        matched = [id_map[pid] for pid in product_ids if pid in id_map]

        state["node_output"] = {
            "status": "success",
            "products": matched,
            "reasoning": result.get("reasoning", ""),
        }
        state["suggested_products"] = suggested + product_ids
        if len(matched) == 1:
            state["current_product"] = matched[0]
        state["pending_step"] = None

    else:
        state["node_output"] = {"status": "no_result"}
        state["pending_step"] = None

    return state
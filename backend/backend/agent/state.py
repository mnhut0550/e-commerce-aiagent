from typing import TypedDict, Optional, List


class ProductSnapshot(TypedDict):
    product_id: str
    name: str
    price: str
    price_int: int          # giá dạng số để filter
    stock: int
    preorder: bool
    category: str
    subcategory: str
    short_desc: str
    full_desc: str          # chứa specs thực tế


class OrderInfo(TypedDict):
    product_id: Optional[str]
    quantity: Optional[int]
    order_type: Optional[str]
    name: Optional[str]
    phone: Optional[str]
    email: Optional[str]
    note: Optional[str]


class ConsultantContext(TypedDict):
    """Persist qua các turn — không bị mất khi clarify"""
    budget: Optional[int]       # VNĐ
    purpose: Optional[str]
    category: Optional[str]
    keyword: Optional[str]


class AgentState(TypedDict):
    # ── Input ──────────────────────────────────────────────
    session_id: str
    user_input: str

    # ── Memory (persist qua các turn) ──────────────────────
    chat_history: List[dict]            # [{"role": "user"|"assistant", "content": "..."}]
    current_intent: Optional[str]       # consult | order | check_stock | general
    pending_step: Optional[str]         # đang chờ user trả lời gì
                                        # vd: "ask_quantity" | "ask_phone" | "ask_budget"
                                        #     "ask_purpose" | "confirm_order"

    # Context sản phẩm đang nói tới
    current_product: Optional[ProductSnapshot]  # snapshot đầy đủ
    suggested_products: List[str]       # list product_id đã gợi ý (tránh gợi lại)

    # Thông tin đơn hàng đang gom
    order_info: Optional[OrderInfo]
    consultant_context: Optional[ConsultantContext]  # budget/purpose persist
    
    # ── Reasoning output (reset mỗi turn) ──────────────────
    extracted_entities: dict
    # Các key hay dùng trong extracted_entities:
    # {
    #   "intent": "consult" | "order" | "check_stock" | "general",
    #   "product_id": "...",       # nếu nhắc đến sản phẩm cụ thể
    #   "product_keyword": "...",  # nếu mơ hồ ("điện thoại chơi game")
    #   "quantity": 2,
    #   "budget": 5000000,
    #   "purpose": "chơi game",
    #   "name": "...",
    #   "phone": "...",
    #   "email": "...",
    #   "note": "...",
    #   "order_type": "buy" | "preorder",
    #   "refers_to_current": True  # "lấy cái đó", "ok đặt đi"
    # }

    # ── Node output (reset mỗi turn) ───────────────────────
    last_node: str                      # "consultant" | "order" | "general"
    node_output: dict
    # Consultant node_output:
    # {
    #   "status": "success" | "need_more_info" | "no_result",
    #   "products": [...],             # list ProductSnapshot
    #   "missing_info": "budget" | "purpose" | ...,
    #   "ask_user": "Bạn có ngân sách khoảng bao nhiêu?"  # câu hỏi cụ thể
    # }
    #
    # Order node_output:
    # {
    #   "status": "need_more_info"
    #           | "out_of_stock"
    #           | "insufficient_stock"   # có hàng nhưng không đủ số lượng
    #           | "preorder_not_allowed"
    #           | "preorder_available"   # hết hàng nhưng cho preorder
    #           | "confirmed",
    #   "missing_fields": ["quantity", "phone"],  # nếu need_more_info
    #   "ask_user": "Bạn muốn mua bao nhiêu?",   # câu hỏi cụ thể
    #   "available_stock": 3,          # nếu insufficient_stock
    #   "order_id": "O-xxx"            # nếu confirmed
    # }

    # ── Final output ───────────────────────────────────────
    final_response: str

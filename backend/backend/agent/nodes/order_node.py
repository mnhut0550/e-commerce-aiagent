from backend.agent.state import AgentState, ProductSnapshot, OrderInfo
from backend.services.sheets import read_sheet, append_row
from uuid import uuid4
from datetime import datetime


# ── Helpers ────────────────────────────────────────────────

def _fetch_product(product_id: str) -> ProductSnapshot | None:
    """Load sản phẩm từ Sheets theo ID."""
    rows = read_sheet("PRODUCTS!A1:Z")
    if not rows:
        return None
    headers = rows[0]
    for row in rows[1:]:
        p = dict(zip(headers, row))
        if p.get("id") == product_id and p.get("active", "").lower() == "true":
            return ProductSnapshot(
                product_id=p["id"],
                name=p.get("name", ""),
                price=p.get("price", ""),
                stock=int(p.get("stock", 0)),
                preorder=p.get("preorder", "no").lower() == "yes",
                short_desc=p.get("short_desc", ""),
            )
    return None


def _missing_fields(order_info: OrderInfo) -> list[str]:
    """Trả về list field còn thiếu để tạo order."""
    required = ["product_id", "quantity", "order_type", "name", "phone"]
    return [f for f in required if not order_info.get(f)]


def _next_pending_step(missing: list[str]) -> tuple[str, str]:
    """
    Trả về (pending_step, ask_user) cho field thiếu đầu tiên.
    Ưu tiên hỏi theo thứ tự tự nhiên.
    """
    priority = [
        ("product_id",  "ask_product",   "Bạn muốn mua sản phẩm nào?"),
        ("quantity",    "ask_quantity",  "Bạn muốn mua bao nhiêu cái?"),
        ("order_type",  "ask_order_type","Bạn muốn mua ngay hay đặt trước (preorder)?"),
        ("name",        "ask_name",      "Cho mình xin tên của bạn nhé?"),
        ("phone",       "ask_phone",     "Cho mình xin số điện thoại của bạn nhé?"),
    ]
    for field, step, question in priority:
        if field in missing:
            return step, question
    return "", ""


def _create_order(order_info: OrderInfo) -> str:
    """Ghi đơn hàng vào Sheets, trả về order_id."""
    order_id = "O-" + str(uuid4())[:8]
    append_row("ORDERS!A1", [
        order_id,
        order_info["product_id"],
        order_info["order_type"],
        order_info.get("quantity", 1),
        order_info["name"],
        order_info["phone"],
        order_info.get("email", ""),
        order_info.get("note", ""),
        "web",
        "new",
        datetime.utcnow().isoformat(),
    ])
    return order_id


# ── Main node ──────────────────────────────────────────────

async def order_node(state: AgentState) -> AgentState:
    state["last_node"] = "order"
    entities = state.get("extracted_entities", {})
    order_info: OrderInfo = state.get("order_info") or {}
    intent = state.get("current_intent")

    # ── 1. Load product nếu chưa có ────────────────────────
    product = state.get("current_product")

    if not product and order_info.get("product_id"):
        product = _fetch_product(order_info["product_id"])
        if not product:
            state["node_output"] = {
                "status": "product_not_found",
                "ask_user": "Mình không tìm thấy sản phẩm đó. Bạn có thể mô tả lại không?",
            }
            state["pending_step"] = "ask_product"
            state["order_info"] = order_info
            return state
        state["current_product"] = product

    # ── 2. Check stock only ─────────────────────────────────
    if intent == "check_stock":
        if not product:
            state["node_output"] = {
                "status": "need_more_info",
                "missing_fields": ["product_id"],
                "ask_user": "Bạn muốn kiểm tra tồn kho sản phẩm nào?",
            }
            state["pending_step"] = "ask_product"
            return state

        if product["stock"] > 0:
            state["node_output"] = {
                "status": "in_stock",
                "product": product,
                "available_stock": product["stock"],
            }
        elif product["preorder"]:
            state["node_output"] = {
                "status": "preorder_available",
                "product": product,
            }
        else:
            state["node_output"] = {
                "status": "out_of_stock",
                "product": product,
            }
        return state

    # ── 3. Order flow ───────────────────────────────────────

    # 3a. Thiếu thông tin → hỏi từng bước
    missing = _missing_fields(order_info)
    if missing:
        pending_step, ask_user = _next_pending_step(missing)
        state["node_output"] = {
            "status": "need_more_info",
            "missing_fields": missing,
            "ask_user": ask_user,
        }
        state["pending_step"] = pending_step
        state["order_info"] = order_info
        return state

    # 3b. Đủ thông tin → validate stock
    quantity = int(order_info.get("quantity", 1))
    order_type = order_info.get("order_type")

    # Chưa load product (trường hợp product_id có sẵn từ đầu)
    if not product:
        product = _fetch_product(order_info["product_id"])
        if not product:
            state["node_output"] = {
                "status": "product_not_found",
                "ask_user": "Mình không tìm thấy sản phẩm. Bạn có thể chọn lại không?",
            }
            state["pending_step"] = "ask_product"
            return state
        state["current_product"] = product

    # Hết hàng hoàn toàn
    if product["stock"] <= 0:
        if product["preorder"]:
            state["node_output"] = {
                "status": "preorder_available",
                "product": product,
                "ask_user": f"{product['name']} hiện đã hết hàng nhưng có thể đặt trước. Bạn có muốn preorder không?",
            }
            state["pending_step"] = "ask_order_type"
            # Cập nhật order_type nếu user đã chọn preorder
            if order_type == "preorder":
                pass  # tiếp tục xuống tạo order
            else:
                state["order_info"] = order_info
                return state
        else:
            state["node_output"] = {
                "status": "out_of_stock",
                "product": product,
            }
            state["order_info"] = order_info
            return state

    # Không đủ số lượng
    if order_type == "buy" and product["stock"] < quantity:
        state["node_output"] = {
            "status": "insufficient_stock",
            "product": product,
            "requested_quantity": quantity,
            "available_stock": product["stock"],
            "preorder_available": product["preorder"],
            "ask_user": (
                f"{product['name']} chỉ còn {product['stock']} cái. "
                f"Bạn muốn mua {product['stock']} cái có sẵn"
                + (" hay đặt trước số còn lại?" if product["preorder"] else "?")
            ),
        }
        state["pending_step"] = "ask_quantity"
        state["order_info"] = order_info
        return state

    # Không cho preorder
    if order_type == "preorder" and not product["preorder"]:
        state["node_output"] = {
            "status": "preorder_not_allowed",
            "product": product,
            "ask_user": f"{product['name']} không hỗ trợ đặt trước. Bạn có muốn mua ngay không? (còn {product['stock']} cái)",
        }
        state["pending_step"] = "ask_order_type"
        state["order_info"] = order_info
        return state

    # ── 3c. Tất cả hợp lệ → tạo order ─────────────────────
    try:
        order_id = _create_order(order_info)
        state["node_output"] = {
            "status": "confirmed",
            "order_id": order_id,
            "product": product,
            "quantity": quantity,
            "order_type": order_type,
            "name": order_info["name"],
        }
        # Reset order context sau khi tạo xong
        state["order_info"] = None
        state["pending_step"] = None

    except Exception as e:
        state["node_output"] = {
            "status": "error",
            "message": str(e),
        }

    return state
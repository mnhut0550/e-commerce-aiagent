import json
from backend.redis_client import sync_redis_client

# TTL 30 phút — đủ cho 1 session mua hàng
_TTL = 60 * 30

# Các field cần persist qua các turn
_MEMORY_FIELDS = [
    "current_product",
    "current_intent",
    "pending_step",
    "suggested_products",
    "order_info",
    "consultant_context",   # budget/purpose persist
]


def load_memory(session_id: str) -> dict:
    """Đọc memory từ Redis, trả về dict để merge vào initial_state."""
    key = f"memory:{session_id}"
    raw = sync_redis_client.get(key)
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except Exception:
        return {}


def save_memory(session_id: str, state: dict) -> None:
    """Lưu các field memory từ final_state vào Redis."""
    key = f"memory:{session_id}"
    memory = {field: state.get(field) for field in _MEMORY_FIELDS}
    sync_redis_client.setex(key, _TTL, json.dumps(memory, ensure_ascii=False))


def clear_memory(session_id: str) -> None:
    """Xóa memory khi session bị delete."""
    sync_redis_client.delete(f"memory:{session_id}")
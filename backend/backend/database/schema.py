from pydantic import BaseModel, model_validator
from typing import Optional, Generic, TypeVar, List


T = TypeVar("T")


# ==========================
# BASE RESPONSE
# ==========================
class APIResponse(BaseModel, Generic[T]):
    success: bool
    message: str
    status_code: int
    error: Optional[str] = None

class SessionDetail(BaseModel):
    session_id: str
    created_at: str

# ==========================
# MESSAGES
# ==========================

class SendMessageRequest(BaseModel):
    message: Optional[str] = None
    session_id: Optional[str] = None
    context_product_id: Optional[str] = None  # user đang xem sản phẩm nào trên UI

    @model_validator(mode="after")
    def check_at_least_one(self):
        if not self.message:
            raise ValueError("Message is required")
        return self


class MessageInfo(BaseModel):
    id: int
    role: str
    content: str
    created_at: str


class SessionMessagesResponse(BaseModel):
    session: SessionDetail
    messages: List[MessageInfo]
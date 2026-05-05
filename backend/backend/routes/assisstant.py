from fastapi import APIRouter
from fastapi.responses import StreamingResponse, JSONResponse
from backend.server.server_services import (
    get_session_messages,
    delete_session,
    message as services_message,
    create_session,
)
from backend.server.responses import _service_response
from backend.redis_client import async_redis
from backend.database.db_models import SessionLocal, Session as SessionModel
from backend.database.schema import (
    SendMessageRequest,
    APIResponse,
    MessageInfo,
    SessionMessagesResponse,
)

router = APIRouter()


# ==========================
# SESSIONS
# ==========================

@router.get(
    "/sessions/{session_id}/messages",
    tags=["Chat Session"],
    response_model=APIResponse[SessionMessagesResponse],
    summary="Get session messages",
)
async def get_session_messages_route(session_id: str):
    return _service_response(
        await get_session_messages({"session_id": session_id})
    )


@router.delete(
    "/sessions/{session_id}",
    tags=["Chat Session"],
    response_model=APIResponse[None],
    summary="Delete session",
)
async def delete_session_route(session_id: str):
    return _service_response(
        await delete_session({"session_id": session_id})
    )


# ==========================
# MESSAGES
# ==========================

@router.post(
    "/assistant_chat",
    tags=["Chat with Assistant"],
    response_model=APIResponse[MessageInfo],
    summary="Send message",
    description="Gửi tin nhắn. Nếu chưa có session_id thì tạo mới luôn.",
)
async def send_message(payload: SendMessageRequest):
    data = payload.dict()
    session_id = data.get("session_id")

    if session_id is None:
        result = await create_session(data)
    else:
        result = await services_message(data)

    return _service_response(result)


# ==========================
# SSE — nhận token streaming
# ==========================

@router.get(
    "/sse/{session_id}",
    tags=["Chat with Assistant"],
    summary="SSE stream",
    description="Subscribe để nhận response từ Agent theo từng token.",
)
async def sse_stream(session_id: str):
    # Validate session tồn tại
    with SessionLocal() as db:
        session = db.query(SessionModel).filter(
            SessionModel.session_id == session_id
        ).first()
        if not session:
            return JSONResponse(
                content={"success": False, "message": "Session not found"},
                status_code=404,
            )

    async def event_stream():
        pubsub = async_redis.pubsub()
        await pubsub.subscribe(f"session:{session_id}")

        try:
            async for msg in pubsub.listen():
                if msg["type"] != "message":
                    continue

                data = msg["data"]

                yield f"data: {data}\n\n"

        finally:
            await pubsub.unsubscribe(f"session:{session_id}")
            await pubsub.aclose()

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # quan trọng nếu đứng sau Nginx
        },
    )
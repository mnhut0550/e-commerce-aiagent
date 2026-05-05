import uuid
from backend.database.db_models import SessionLocal, Session as SessionModel, Message as MessageModel
from backend.database.db_logaudit import log_audit
from backend.server.responses import success, fail


def _load_history(session_id: str) -> list:
    """Load conversation history để gửi cho OpenAI."""
    with SessionLocal() as db:
        messages = (
            db.query(MessageModel)
            .filter(MessageModel.session_id == session_id)
            .order_by(MessageModel.created_at.asc())
            .all()
        )
        return [{"role": m.role, "content": m.content} for m in messages]


async def create_session(data: dict):
    first_message = data.get("message")

    if not first_message:
        return fail("Missing message", code=400)
    if len(first_message) > 10000:
        return fail("Message too long", code=422)

    with SessionLocal() as db:
        try:
            new_session = SessionModel(session_id=str(uuid.uuid4()))
            db.add(new_session)
            db.commit()
            db.refresh(new_session)
            log_audit(db, "create_session", f"Created session {new_session.session_id}")
        except Exception as e:
            db.rollback()
            return fail(f"Internal error: {str(e)}", code=500)

    # Gửi message đầu tiên
    msg_result = await message({
        "session_id": str(new_session.session_id),
        "message": first_message,
    })

    if not msg_result.get("success"):
        # Rollback session nếu message thất bại
        with SessionLocal() as db:
            db_session = db.query(SessionModel).filter(
                SessionModel.session_id == new_session.session_id
            ).first()
            if db_session:
                db.delete(db_session)
                db.commit()
        return fail(msg_result.get("message"), code=msg_result.get("status_code", 500))

    return success(
        message="Session created",
        data={
            "session": {
                "session_id": str(new_session.session_id),
                "created_at": str(new_session.created_at),
            },
            # Không có assistant_message nữa — client tự subscribe SSE
            "status": "processing",
        },
    )


async def get_session_messages(data: dict):
    session_id = data.get("session_id")

    if not session_id:
        return fail("Missing required fields", code=400)

    with SessionLocal() as db:
        session = db.query(SessionModel).filter(
            SessionModel.session_id == session_id
        ).first()

        if not session:
            return fail("Session not found", code=404)

        messages = (
            db.query(MessageModel)
            .filter(MessageModel.session_id == session_id)
            .order_by(MessageModel.created_at.asc())
            .all()
        )

        return success(
            message="Session and messages fetched",
            data={
                "session": {
                    "session_id": str(session.session_id),
                    "created_at": str(session.created_at),
                },
                "messages": [
                    {
                        "message_id": str(m.id),
                        "role": m.role,
                        "content": m.content,
                        "timestamp": str(m.created_at),
                    }
                    for m in messages
                ],
            },
        )


async def delete_session(data: dict):
    from backend.agent.memory import clear_memory
    session_id = data.get("session_id")

    if not session_id:
        return fail("Missing required fields", code=400)

    with SessionLocal() as db:
        session = db.query(SessionModel).filter(
            SessionModel.session_id == session_id
        ).first()

        if not session:
            return fail("Session not found", code=404)

        db.delete(session)
        log_audit(db, "delete_session", f"Deleted session {session_id}")
        db.commit()

        clear_memory(session_id)
        return success(message="Session deleted")


async def message(data: dict):
    from backend.agent.tasks import process_message  # import ở đây tránh circular

    session_id = data.get("session_id")
    message_content = data.get("message")
    context_product_id = data.get("context_product_id")

    if not session_id:
        return fail("Missing required fields", code=400)
    if not message_content:
        return fail("Message is required", code=400)
    if len(message_content) > 10000:
        return fail("Message too long", code=422)

    with SessionLocal() as db:
        session = db.query(SessionModel).filter(
            SessionModel.session_id == session_id
        ).first()

        if not session:
            return fail("Session not found", code=404)

        try:
            user_msg = MessageModel(
                session_id=session_id,
                role="user",
                content=message_content,
            )
            db.add(user_msg)
            db.flush()
            log_audit(db, "send_message", f"User sent message in {session_id}")
            db.commit()
            db.refresh(user_msg)

        except Exception as e:
            db.rollback()
            return fail(f"Internal error: {str(e)}", code=500)

    # Load history sau khi đã lưu user message
    history = _load_history(session_id)

    # Đẩy vào Celery queue — non-blocking
    process_message.delay(session_id, history, context_product_id)

    return success(
        message="Message queued",
        data={
            "status": "processing",
            "user_message": {
                "message_id": str(user_msg.id),
                "content": user_msg.content,
                "timestamp": str(user_msg.created_at),
            },
        },
    )
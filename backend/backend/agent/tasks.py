from backend.celery_app import celery_app
from backend.agent.runner import run_agent


@celery_app.task(
    bind=True,
    max_retries=2,
    default_retry_delay=3,
    name="agent.process_message",
)
def process_message(self, session_id: str, messages: list, context_product_id: str = None):
    """
    Celery task xử lý tin nhắn — mỗi session chạy độc lập.
    Retry tự động nếu lỗi tạm thời (network, timeout...).
    """
    try:
        run_agent(session_id, messages, context_product_id)
    except Exception as exc:
        raise self.retry(exc=exc)

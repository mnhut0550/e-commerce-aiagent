from sqlalchemy.orm import Session
from backend.database.db_models import AuditLog


def log_audit(db: Session, action: str, details: str = "") -> None:
    """Create an audit log entry."""
    db.add(AuditLog(action=action, detail=details)) ##
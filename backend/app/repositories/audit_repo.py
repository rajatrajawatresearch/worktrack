import json

from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


def create(
    db: Session,
    *,
    action: str,
    user_id=None,
    company_id=None,
    entity_type: str | None = None,
    entity_id=None,
    ip_address: str | None = None,
    meta: dict | None = None,
) -> AuditLog:
    log = AuditLog(
        user_id=user_id,
        company_id=company_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        ip_address=ip_address,
        meta=json.dumps(meta) if meta is not None else None,
    )
    db.add(log)
    db.flush()
    return log

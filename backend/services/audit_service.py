import json
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from backend.database.models import AuditLog

def log_audit_event(
    db: Session,
    action: str,
    user_id: Optional[int] = None,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> AuditLog:
    """
    Creates an append-only audit log entry in the database.
    Ensures passwords, tokens, and sensitive credentials are never stored.
    """
    safe_metadata = metadata.copy() if metadata else {}
    
    # Strip any potential sensitive fields
    for k in ["password", "password_hash", "token", "access_token", "secret"]:
        safe_metadata.pop(k, None)

    metadata_str = json.dumps(safe_metadata) if safe_metadata else None

    log_entry = AuditLog(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id) if entity_id is not None else None,
        metadata_json=metadata_str
    )
    db.add(log_entry)
    db.commit()
    db.refresh(log_entry)
    return log_entry

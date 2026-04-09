# app/api/v1/endpoints/logs.py
# Admin-only endpoint to view chat logs.

from fastapi import APIRouter, Depends, HTTPException, status, Header, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.db.session import get_db
from app.services.log_service import get_logs
from app.services.user_service import UserService
from app.core.security import verify_token

router = APIRouter()


def _require_admin(
    authorization: str = Header(None),
    db: Session = Depends(get_db),
):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
        )

    token   = authorization.split(" ", 1)[1]
    payload = verify_token(token)

    # verify_token returns a dict on success, None on failure
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
        )

    # payload is a dict — get username from "sub"
    username = payload.get("sub") if isinstance(payload, dict) else payload
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload.",
        )

    user = UserService.get_user_by_username(db, username)
    if not user or not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required.",
        )
    return user


@router.get("/")
def list_logs(
    skip:       int           = Query(0,   ge=0),
    limit:      int           = Query(100, ge=1, le=500),
    session_id: Optional[str] = Query(None),
    username:   Optional[str] = Query(None),
    db:         Session       = Depends(get_db),
    _admin                    = Depends(_require_admin),
):
    """Return paginated chat logs. Admin-only."""
    logs = get_logs(db, skip=skip, limit=limit, session_id=session_id, username=username)
    return [
        {
            "id":         log.id,
            "session_id": log.session_id,
            "username":   log.username,
            "ip_address": log.ip_address,
            "query":      log.query,
            "response":   log.response,
            "intent":     log.intent,
            "timestamp":  log.timestamp.isoformat() if log.timestamp else None,
        }
        for log in logs
    ]

from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Tuple



def _now() -> datetime:
    return datetime.now(timezone.utc)


def new_signup_token() -> Tuple[str, str, datetime]:
    token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(token.encode('utf-8')).hexdigest()
    expires_at = _now() + timedelta(hours=24)
    return token, token_hash, expires_at


def is_expired(expires_at: datetime) -> bool:
    try:
        return expires_at.replace(tzinfo=timezone.utc) < _now()
    except Exception:
        return True


def new_reset_token() -> Tuple[str, str, datetime]:
    token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(token.encode('utf-8')).hexdigest()
    # reset tokens: shorter TTL (2 hours)
    expires_at = _now() + timedelta(hours=2)
    return token, token_hash, expires_at

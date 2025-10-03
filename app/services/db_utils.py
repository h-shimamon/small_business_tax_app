from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

from app.extensions import db


@contextmanager
def session_scope() -> Iterator:
    """Provide a transactional scope around a series of operations."""
    try:
        yield db.session
        db.session.commit()
    except Exception:  # pragma: no cover - re-raise after rollback
        db.session.rollback()
        raise
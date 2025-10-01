from __future__ import annotations

import datetime as _dt
from sqlalchemy import event


def _to_date(value) -> _dt.date | None:
    if value is None or value == "":
        return None
    if isinstance(value, _dt.date):
        return value
    if isinstance(value, _dt.datetime):
        return value.date()
    s = str(value)
    try:
        return _dt.date.fromisoformat(s)
    except Exception:
        return None


def _to_iso(value: _dt.date | None) -> str | None:
    if value is None:
        return None
    if isinstance(value, _dt.datetime):
        value = value.date()
    if isinstance(value, _dt.date):
        return value.isoformat()
    return str(value)


def attach_date_string_sync(model_cls, string_attr: str, date_attr: str) -> None:
    """
    Keep a pair of attributes in sync: a String(10) ISO date and a Date column.
    - When the string attr is set, parse and update the date attr.
    - When the date attr is set, format and update the string attr.
    This avoids touching calling code and preserves current behavior.
    """

    @event.listens_for(getattr(model_cls, string_attr), "set", retval=False)
    def _on_set_string(target, value, oldvalue, initiator):  # type: ignore
        d = _to_date(value)
        try:
            setattr(target, date_attr, d)
        except Exception:
            # Never raise from sync; keep original assignment behavior
            pass
        return value

    @event.listens_for(getattr(model_cls, date_attr), "set", retval=False)
    def _on_set_date(target, value, oldvalue, initiator):  # type: ignore
        iso = _to_iso(value)
        try:
            setattr(target, string_attr, iso)
        except Exception:
            pass
        return value


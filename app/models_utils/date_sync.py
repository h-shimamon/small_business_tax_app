"""SQLAlchemy モデルの文字列日付と Date カラムを双方向同期させるユーティリティ。"""

from __future__ import annotations

from sqlalchemy import event

from app.models_utils.date_readers import normalize_date, to_iso


def attach_date_string_sync(model_cls, string_attr: str, date_attr: str) -> None:
    """
    Keep a pair of attributes in sync: a String(10) ISO date and a Date column.

    - When the string attr is set, parse and update the date attr.
    - When the date attr is set, format and update the string attr.

    既存コードとの互換のため、例外は握りつぶして元の代入動作を優先させる。
    """

    @event.listens_for(getattr(model_cls, string_attr), "set", retval=False)
    def _on_set_string(target, value, oldvalue, initiator):  # type: ignore[arg-type]
        parsed = normalize_date(value)
        try:
            setattr(target, date_attr, parsed)
        except Exception:
            pass
        return value

    @event.listens_for(getattr(model_cls, date_attr), "set", retval=False)
    def _on_set_date(target, value, oldvalue, initiator):  # type: ignore[arg-type]
        iso = to_iso(value)
        try:
            setattr(target, string_attr, iso)
        except Exception:
            pass
        return value


__all__ = ['attach_date_string_sync']

from __future__ import annotations

from typing import Callable

from app.company.models import (
    AccountingData,
    Company,
    Office,
    Shareholder,
    UserAccountMapping,
)
from app.extensions import db
from app.primitives.dates import get_company_period


def _filled_str(v) -> bool:
    try:
        return bool(str(v).strip())
    except Exception:
        return False



def _get_company(company_id: int) -> Company | None:
    try:
        return db.session.get(Company, company_id)
    except Exception:
        return None

def _company_info_completed(company_id: int, user_id: int) -> bool:
    c = _get_company(company_id)
    if not c:
        return False
    return all([
        _filled_str(c.corporate_number),
        _filled_str(c.company_name),
        _filled_str(c.company_name_kana),
        _filled_str(c.zip_code),
        _filled_str(c.prefecture),
        _filled_str(c.city),
        _filled_str(c.address),
        _filled_str(c.phone_number),
        bool(c.establishment_date),
    ])


def _shareholders_completed(company_id: int, user_id: int) -> bool:
    return Shareholder.query.filter_by(company_id=company_id, parent_id=None).count() > 0


def _declaration_completed(company_id: int, user_id: int) -> bool:
    c = _get_company(company_id)
    if not c:
        return False
    # Keep original string-based gating, but also accept date presence via centralized readers
    str_ok = _filled_str(c.accounting_period_start or '') and _filled_str(c.accounting_period_end or '')
    try:
        period = get_company_period(c)
        date_ok = bool(period.start and period.end)
    except Exception:
        date_ok = False
    return str_ok or date_ok


def _office_list_completed(company_id: int, user_id: int) -> bool:
    return Office.query.filter_by(company_id=company_id).count() > 0


def _data_mapping_completed(company_id: int, user_id: int) -> bool:
    return UserAccountMapping.query.filter_by(user_id=user_id).count() > 0


def _journals_completed(company_id: int, user_id: int) -> bool:
    return AccountingData.query.filter_by(company_id=company_id).first() is not None


REGISTRY: dict[str, Callable[[int, int], bool]] = {
    'company_info': _company_info_completed,
    'shareholders': _shareholders_completed,
    'declaration': _declaration_completed,
    'office_list': _office_list_completed,
    'data_mapping': _data_mapping_completed,
    'journals': _journals_completed,
}


def compute_completed(company_id: int, user_id: int) -> set[str]:
    completed: set[str] = set()
    for key, fn in REGISTRY.items():
        try:
            if fn(company_id, user_id):
                completed.add(key)
        except Exception:
            continue
    return completed

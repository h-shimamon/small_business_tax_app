from __future__ import annotations

from typing import Optional

from app import db
from app.company.models import AccountingData, Company


def _company_id_for_user(user_id: int) -> Optional[int]:
    company = Company.query.filter_by(user_id=user_id).first()
    return company.id if company else None


def invalidate_accounting_data(company_id: int) -> bool:
    """Delete persisted accounting data for the given company.

    Returns True if any records were deleted. Caller handles session/redirect.
    """
    deleted = db.session.query(AccountingData).filter_by(company_id=company_id).delete()
    db.session.commit()
    return bool(deleted)


def has_accounting_data(company_id: int) -> bool:
    return db.session.query(AccountingData.id).filter_by(company_id=company_id).first() is not None


def on_mapping_saved(user_id: int) -> bool:
    cid = _company_id_for_user(user_id)
    if cid is None:
        return False
    return invalidate_accounting_data(cid)


def on_mapping_deleted(user_id: int) -> bool:
    cid = _company_id_for_user(user_id)
    if cid is None:
        return False
    return invalidate_accounting_data(cid)


def on_mappings_reset(user_id: int) -> bool:
    cid = _company_id_for_user(user_id)
    if cid is None:
        return False
    return invalidate_accounting_data(cid)


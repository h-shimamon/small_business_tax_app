from __future__ import annotations

from typing import Optional, Tuple

from flask import g, has_request_context
from flask_login import current_user
from sqlalchemy import func

from app import db
from app.company.forms import MainShareholderForm, RelatedShareholderForm
from app.company.models import Company, Shareholder
from .protocols import ShareholderServiceProtocol


class ShareholderService(ShareholderServiceProtocol):
    """Concrete implementation of shareholder-domain operations."""

    def _resolve_user_id(self, user_id: Optional[int]) -> int:
        if user_id is not None:
            return int(user_id)
        try:
            resolved = getattr(current_user, 'id', None)
        except Exception:
            resolved = None
        if resolved is None:
            raise RuntimeError('user_id is required when current_user is not available')
        return int(resolved)

    def _company_scope(self, company_id: int, user_id: int):
        return Company.query.filter_by(id=company_id, user_id=user_id)

    def get_shareholders_by_company(self, company_id: int, user_id: Optional[int] = None):
        uid = self._resolve_user_id(user_id)
        return (
            Shareholder.query.join(Company)
            .filter(Company.id == company_id, Company.user_id == uid)
            .order_by(Shareholder.id)
            .all()
        )

    def get_main_shareholders(self, company_id: int, user_id: Optional[int] = None):
        uid = self._resolve_user_id(user_id)
        return (
            Shareholder.query.join(Company)
            .filter(
                Company.id == company_id,
                Company.user_id == uid,
                Shareholder.parent_id.is_(None),
            )
            .order_by(Shareholder.id)
            .all()
        )

    def get_shareholder_by_id(self, shareholder_id: int, user_id: Optional[int] = None):
        uid = self._resolve_user_id(user_id)
        return (
            Shareholder.query.join(Company)
            .filter(Shareholder.id == shareholder_id, Company.user_id == uid)
            .first_or_404()
        )

    def add_shareholder(self, company_id: int, form, parent_id: int | None = None, user_id: Optional[int] = None):
        uid = self._resolve_user_id(user_id)
        company = self._company_scope(company_id, uid).first_or_404()
        new_shareholder = Shareholder(company_id=company.id)

        if parent_id:
            parent_shareholder = self.get_shareholder_by_id(parent_id, user_id=uid)
            if parent_shareholder.company_id != company.id:
                return None, "親株主の会社が一致しません。"
            new_shareholder.parent_id = parent_id
            if hasattr(form, 'is_address_same_as_main') and getattr(form.is_address_same_as_main, 'data', False):
                if hasattr(form, 'populate_address_from_main_shareholder'):
                    form.populate_address_from_main_shareholder(parent_shareholder)

        form.populate_obj(new_shareholder)
        db.session.add(new_shareholder)
        db.session.commit()
        return new_shareholder, None

    def get_related_shareholders(self, main_shareholder_id: int, user_id: Optional[int] = None):
        uid = self._resolve_user_id(user_id)
        main_shareholder = self.get_shareholder_by_id(main_shareholder_id, user_id=uid)
        return Shareholder.query.filter_by(parent_id=main_shareholder.id).all()

    def update_shareholder(self, shareholder_id: int, form, user_id: Optional[int] = None):
        uid = self._resolve_user_id(user_id)
        shareholder = self.get_shareholder_by_id(shareholder_id, user_id=uid)
        form.populate_obj(shareholder)
        if shareholder.parent_id is not None and hasattr(form, 'is_address_same_as_main'):
            same = False
            try:
                same = bool(form.is_address_same_as_main.data)
            except Exception:
                same = False
            if same and shareholder.parent is not None:
                shareholder.zip_code = shareholder.parent.zip_code
                shareholder.prefecture_city = shareholder.parent.prefecture_city
                shareholder.address = shareholder.parent.address
        db.session.commit()
        return shareholder

    def delete_shareholder(self, shareholder_id: int, user_id: Optional[int] = None):
        uid = self._resolve_user_id(user_id)
        shareholder = self.get_shareholder_by_id(shareholder_id, user_id=uid)
        db.session.delete(shareholder)
        db.session.commit()
        return shareholder

    def get_shareholder_form(self, shareholder):
        if shareholder.parent_id is None:
            return MainShareholderForm
        return RelatedShareholderForm

    def is_same_address(self, a: Shareholder | None, b: Shareholder | None) -> bool:
        def _nz(val):
            return (val or '').strip()

        if not (a and b):
            return False
        return (
            _nz(getattr(a, 'zip_code', None)) == _nz(getattr(b, 'zip_code', None))
            and _nz(getattr(a, 'prefecture_city', None)) == _nz(getattr(b, 'prefecture_city', None))
            and _nz(getattr(a, 'address', None)) == _nz(getattr(b, 'address', None))
        )

    def get_main_shareholder_group_number(self, company_id: int, main_shareholder_id: int, user_id: Optional[int] = None) -> int:
        uid = self._resolve_user_id(user_id)
        main_shareholders = self.get_main_shareholders(company_id, user_id=uid)
        for idx, shareholder in enumerate(main_shareholders, start=1):
            if shareholder.id == main_shareholder_id:
                return idx
        return -1

    # --- Aggregations ---

    def _get_metric_column_for_company(self, company_id: int, user_id: int):
        company = self._company_scope(company_id, user_id).first_or_404()
        name = company.company_name or ""
        if any(corp_type in name for corp_type in ['合同会社', '合名会社', '合資会社']):
            return Shareholder.investment_amount, 'investment_amount'
        return Shareholder.voting_rights, 'voting_rights'

    def _get_request_cache(self):
        if has_request_context():
            if not hasattr(g, '_shareholder_totals_cache'):
                g._shareholder_totals_cache = {}
            return g._shareholder_totals_cache
        return {}

    def compute_company_total(self, company_id: int, user_id: Optional[int] = None) -> int:
        uid = self._resolve_user_id(user_id)
        metric_col, metric_name = self._get_metric_column_for_company(company_id, uid)
        cache = self._get_request_cache()
        key = ("company_total", company_id, metric_name, uid)
        if key in cache:
            return cache[key]
        total = (
            db.session.query(func.sum(metric_col))
            .join(Company)
            .filter(
                Company.id == company_id,
                Company.user_id == uid,
                metric_col.isnot(None),
            )
            .scalar()
            or 0
        )
        cache[key] = int(total)
        return int(total)

    def compute_group_total(self, company_id: int, main_shareholder_id: int, user_id: Optional[int] = None) -> int:
        uid = self._resolve_user_id(user_id)
        metric_col, metric_name = self._get_metric_column_for_company(company_id, uid)
        cache = self._get_request_cache()
        key = ("group_total", company_id, main_shareholder_id, metric_name, uid)
        if key in cache:
            return cache[key]
        main = self.get_shareholder_by_id(main_shareholder_id, user_id=uid)
        if main.company_id != company_id:
            return 0
        totals_map = self.compute_group_totals_map(company_id, user_id=uid)
        total = int(totals_map.get(int(main_shareholder_id), 0))
        cache[key] = total
        return total

    def compute_group_totals_map(self, company_id: int, user_id: Optional[int] = None) -> dict[int, int]:
        uid = self._resolve_user_id(user_id)
        metric_col, metric_name = self._get_metric_column_for_company(company_id, uid)
        cache = self._get_request_cache()
        key = ("group_totals_map", company_id, metric_name, uid)
        if key in cache:
            return cache[key]
        group_key = func.coalesce(Shareholder.parent_id, Shareholder.id)
        rows = (
            db.session.query(group_key.label('group_id'), func.sum(metric_col).label('total'))
            .join(Company)
            .filter(
                Company.id == company_id,
                Company.user_id == uid,
                metric_col.isnot(None),
            )
            .group_by(group_key)
            .all()
        )
        totals_map = {int(row.group_id): int(row.total or 0) for row in rows}
        cache[key] = totals_map
        return totals_map

    def compute_group_totals_both_map(self, company_id: int, user_id: Optional[int] = None) -> dict[int, dict[str, int]]:
        uid = self._resolve_user_id(user_id)
        cache = self._get_request_cache()
        key = ("group_totals_both_map", company_id, uid)
        if key in cache:
            return cache[key]
        rows = (
            db.session.query(
                func.coalesce(Shareholder.parent_id, Shareholder.id).label('group_id'),
                func.sum(Shareholder.shares_held).label('sum_shares'),
                func.sum(Shareholder.voting_rights).label('sum_votes'),
            )
            .join(Company)
            .filter(Company.id == company_id, Company.user_id == uid)
            .group_by(func.coalesce(Shareholder.parent_id, Shareholder.id))
            .all()
        )
        totals_map = {
            int(row.group_id): {
                'sum_shares': int(row.sum_shares or 0),
                'sum_votes': int(row.sum_votes or 0),
            }
            for row in rows
        }
        cache[key] = totals_map
        return totals_map


shareholder_service = ShareholderService()


def get_shareholder_service_for(company) -> Tuple[ShareholderService, Optional[int]]:
    """Return the shared ShareholderService with the user scope derived from company."""
    return shareholder_service, getattr(company, 'user_id', None)

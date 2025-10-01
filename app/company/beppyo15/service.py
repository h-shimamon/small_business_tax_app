from __future__ import annotations

from collections.abc import Iterable
from flask import current_app
from flask_wtf import FlaskForm
from sqlalchemy.exc import SQLAlchemyError

from app.company.models import Beppyo15Breakdown
from app.extensions import db

from .constants import BEPPYO15_FIELD_DEFINITIONS
from .view_models import (
    Beppyo15ItemViewModel,
    Beppyo15PageViewModel,
    Beppyo15SummaryViewModel,
)


class Beppyo15Service:
    """別表15の内訳データを扱うサービス。"""

    def __init__(self, company_id: int) -> None:
        self.company_id = company_id

    # --- Query helpers -------------------------------------------------
    def list_items(self) -> list[Beppyo15Breakdown]:
        return (
            Beppyo15Breakdown.query
            .filter_by(company_id=self.company_id)
            .order_by(Beppyo15Breakdown.id.asc())
            .all()
        )

    def get_item(self, item_id: int) -> Beppyo15Breakdown | None:
        if not item_id:
            return None
        return (
            Beppyo15Breakdown.query
            .filter_by(id=item_id, company_id=self.company_id)
            .first()
        )

    # --- CRUD operations ----------------------------------------------
    def create_item(self, form: FlaskForm) -> tuple[bool, Beppyo15Breakdown | None, str | None]:
        item = Beppyo15Breakdown(company_id=self.company_id)
        self._apply_form(item, form)
        try:
            db.session.add(item)
            db.session.commit()
            return True, item, None
        except SQLAlchemyError as exc:
            db.session.rollback()
            current_app.logger.exception('Failed to create Beppyo15 breakdown: %s', exc)
            return False, None, '登録に失敗しました。'

    def update_item(self, item: Beppyo15Breakdown, form: FlaskForm) -> tuple[bool, Beppyo15Breakdown | None, str | None]:
        if item is None or item.company_id != self.company_id:
            return False, None, '対象データが見つかりません。'
        self._apply_form(item, form)
        try:
            db.session.commit()
            return True, item, None
        except SQLAlchemyError as exc:
            db.session.rollback()
            current_app.logger.exception('Failed to update Beppyo15 breakdown: %s', exc)
            return False, None, '更新に失敗しました。'

    def delete_item(self, item: Beppyo15Breakdown) -> tuple[bool, str | None]:
        if item is None or item.company_id != self.company_id:
            return False, '対象データが見つかりません。'
        try:
            db.session.delete(item)
            db.session.commit()
            return True, None
        except SQLAlchemyError as exc:
            db.session.rollback()
            current_app.logger.exception('Failed to delete Beppyo15 breakdown: %s', exc)
            return False, '削除に失敗しました。'

    # --- View-model builder -------------------------------------------
    def build_page_view(self, accounting_data=None) -> Beppyo15PageViewModel:
        items = self.list_items()
        item_vms = [
            Beppyo15ItemViewModel(
                id=item.id,
                subject=item.subject,
                expense_amount=item.expense_amount,
                deductible_amount=item.deductible_amount,
                net_amount=item.net_amount,
                hospitality_amount=item.hospitality_amount,
                remarks=item.remarks,
            )
            for item in items
        ]
        summary = self._compute_summary(item_vms, accounting_data)
        return Beppyo15PageViewModel(
            items=item_vms,
            summary=summary,
            field_definitions=BEPPYO15_FIELD_DEFINITIONS,
        )

    # --- Internal helpers ---------------------------------------------
    def _apply_form(self, target: Beppyo15Breakdown, form: FlaskForm) -> None:
        target.subject = (form.subject.data or '').strip()
        target.expense_amount = form.expense_amount.data or 0
        target.deductible_amount = form.deductible_amount.data or 0
        target.net_amount = target.expense_amount - target.deductible_amount
        target.hospitality_amount = form.hospitality_amount.data or 0
        target.remarks = (form.remarks.data or '').strip() or None

    @staticmethod
    def _calculate_accounting_months(accounting_data) -> int:
        from datetime import date

        from dateutil.relativedelta import relativedelta

        if not accounting_data:
            return 12
        start = getattr(accounting_data, 'period_start', None)
        end = getattr(accounting_data, 'period_end', None)
        if not isinstance(start, date) or not isinstance(end, date) or end < start:
            return 12

        delta = relativedelta(end, start)
        months = delta.years * 12 + delta.months
        if delta.days > 0:
            months += 1
        months = max(months, 1)
        return min(months, 12)


    @staticmethod
    def _compute_summary(items: Iterable[Beppyo15ItemViewModel], accounting_data=None) -> Beppyo15SummaryViewModel:
        expense_total = sum(item.expense_amount for item in items)
        deductible_total = sum(item.deductible_amount for item in items)
        net_total = sum(item.net_amount for item in items)
        hospitality_total = sum(item.hospitality_amount for item in items)

        spending_cross = max(expense_total - deductible_total, 0)
        hospitality_deduction = max((hospitality_total * 50) // 100, 0)

        months = Beppyo15Service._calculate_accounting_months(accounting_data)
        small_corp_limit = min(spending_cross, (8_000_000 * months + 11) // 12)
        deductible_limit = max(hospitality_deduction, small_corp_limit)

        non_deductible = max(spending_cross - deductible_limit, 0)

        return Beppyo15SummaryViewModel(
            expense_total=expense_total,
            deductible_total=deductible_total,
            net_total=net_total,
            hospitality_total=hospitality_total,
            spending_cross=spending_cross,
            hospitality_deduction=hospitality_deduction,
            small_corp_limit=small_corp_limit,
            deductible_limit=deductible_limit,
            non_deductible_amount=non_deductible,
        )

from __future__ import annotations

from typing import Dict, List, Any, TypedDict

from app.company.services.master_data_service import MasterDataService
from app.company.soa_mappings import SUMMARY_PAGE_MAP, PL_PAGE_ACCOUNTS
from app import db
from app.company.soa_config import STATEMENT_PAGES_CONFIG  # ページ→モデル解決用


class SoASummaryService:
    """
    Service for computing Statement of Accounts (SoA) source totals, breakdown totals,
    differences, and skip decisions.

    Notes
    - Mappings are centralized in app.company.soa_mappings and imported here and by the controller.
    - Public methods return primitive dicts/ints to keep controller context keys unchanged.
    """

    # mappings are imported from app.company.soa_mappings

    @staticmethod
    def _find_and_sum_by_names(data_dict: Dict[str, Any], names: List[str]) -> int:
        total_local = 0
        for _, value in data_dict.items():
            if isinstance(value, dict):
                items = value.get('items')
                if isinstance(items, list):
                    for it in items:
                        if isinstance(it, dict) and it.get('name') in names:
                            total_local += it.get('amount', 0) or 0
                else:
                    total_local += SoASummaryService._find_and_sum_by_names(value, names)
        return total_local

    @classmethod
    def resolve_target_accounts(cls, page: str, master_service: MasterDataService) -> Dict[str, Any]:
        if page not in SUMMARY_PAGE_MAP:
            return {'type': 'UNKNOWN', 'targets': []}
        master_type, breakdown_name = SUMMARY_PAGE_MAP[page]
        if page == 'borrowings':
            # Special: BS 借入金 + PL 支払利息
            bs_df = master_service.get_bs_master_df()
            bs_targets = bs_df[bs_df['breakdown_document'] == '借入金'].index.tolist()
            return {'type': 'BORROWINGS', 'bs_targets': bs_targets, 'pl_targets': ['支払利息']}
        if master_type == 'BS':
            df = master_service.get_bs_master_df()
            targets = df[df['breakdown_document'] == breakdown_name].index.tolist()
            return {'type': 'BS', 'targets': targets}
        else:  # PL
            df = master_service.get_pl_master_df()
            targets = PL_PAGE_ACCOUNTS.get(page, [])
            if not targets and breakdown_name in df.index:
                targets = [breakdown_name]
            return {'type': 'PL', 'targets': targets}

    @classmethod
    def compute_source_total(cls, company_id: int, page: str, accounting_data=None) -> SourceTotalResult:
        from app.company.models import AccountingData  # local import to avoid cycles

        if accounting_data is None:
            accounting_data = (
                AccountingData.query
                .filter_by(company_id=company_id)
                .order_by(AccountingData.created_at.desc())
                .first()
            )
        if accounting_data is None:
            if page == 'borrowings':
                return {'bs_total': 0, 'pl_interest_total': 0, 'source_total': 0}
            return {'source_total': 0}

        # 特例: 'miscellaneous' は PLの「雑収入」+「雑損失」を合算して source_total とする
        if page == 'miscellaneous':
            pl_source = accounting_data.data.get('profit_loss_statement', {})
            rev_total = cls._find_and_sum_by_names(pl_source, ['雑収入'])
            exp_total = cls._find_and_sum_by_names(pl_source, ['雑損失'])
            return {'source_total': (rev_total + exp_total)}

        master_service = MasterDataService()
        targets_info = cls.resolve_target_accounts(page, master_service)

        if targets_info.get('type') == 'BORROWINGS':
            bs_source = accounting_data.data.get('balance_sheet', {})
            pl_source = accounting_data.data.get('profit_loss_statement', {})
            bs_total = cls._find_and_sum_by_names(bs_source, targets_info.get('bs_targets', []))
            pl_interest_total = cls._find_and_sum_by_names(pl_source, targets_info.get('pl_targets', []))
            return {
                'bs_total': bs_total,
                'pl_interest_total': pl_interest_total,
                'source_total': bs_total + pl_interest_total,
            }

        if targets_info.get('type') == 'BS':
            source = accounting_data.data.get('balance_sheet', {})
            total = cls._find_and_sum_by_names(source, targets_info.get('targets', []))
            return {'source_total': total}
        elif targets_info.get('type') == 'PL':
            source = accounting_data.data.get('profit_loss_statement', {})
            total = cls._find_and_sum_by_names(source, targets_info.get('targets', []))
            return {'source_total': total}
        else:
            return {'source_total': 0}

    @staticmethod
    def compute_breakdown_total(company_id: int, page: str, model, total_field_name: str) -> int:
        # ページ指定だけで呼ばれた場合のフォールバック: ページ→モデル解決
        if model is None:
            try:
                cfg = STATEMENT_PAGES_CONFIG.get(page, {})
                model = cfg.get('model')
            except Exception:
                model = None
        if model is None:
            # モデル不明なら 0 扱い（テスト互換のため安全に戻す）
            return 0

        # Special handling for borrowings: sum of balance_at_eoy + paid_interest
        if page == 'borrowings':
            sum_balance = db.session.query(db.func.sum(model.balance_at_eoy))\
                .filter_by(company_id=company_id).scalar() or 0
            sum_interest = db.session.query(db.func.sum(model.paid_interest))\
                .filter_by(company_id=company_id).scalar() or 0
            return (sum_balance or 0) + (sum_interest or 0)

        total_field = getattr(model, total_field_name)
        return db.session.query(db.func.sum(total_field))\
            .filter_by(company_id=company_id).scalar() or 0

    @classmethod
    def compute_difference(cls, company_id: int, page: str, model, total_field_name: str, accounting_data=None) -> DifferenceResult:
        source = cls.compute_source_total(company_id, page, accounting_data=accounting_data)
        breakdown_total = cls.compute_breakdown_total(company_id, page, model, total_field_name)
        if page == 'borrowings':
            bs_total = source.get('bs_total', 0)
            pl_interest_total = source.get('pl_interest_total', 0)
            difference = (bs_total + pl_interest_total) - breakdown_total
            return {
                'bs_total': bs_total,
                'pl_interest_total': pl_interest_total,
                'breakdown_total': breakdown_total,
                'difference': difference,
            }
        else:
            source_total = source.get('source_total', 0)
            difference = source_total - breakdown_total
            return {
                'bs_total': source_total,  # to align with existing generic_summary key naming
                'breakdown_total': breakdown_total,
                'difference': difference,
            }

    @classmethod
    def should_skip(cls, company_id: int, page: str, accounting_data=None) -> bool:
        """
        A page is skipped when its source total equals zero.
        Borrowings uses the combined BS(借入金)+PL(支払利息) total.
        """
        source = cls.compute_source_total(company_id, page, accounting_data=accounting_data)
        if page == 'borrowings':
            return (source.get('bs_total', 0) + source.get('pl_interest_total', 0)) == 0
        return source.get('source_total', 0) == 0

    @classmethod
    def compute_skip_total(cls, company_id: int, page: str, accounting_data=None) -> int:
        """Return the numeric source total used to determine skip."""
        source = cls.compute_source_total(company_id, page, accounting_data=accounting_data)
        if page == 'borrowings':
            return (source.get('bs_total', 0) + source.get('pl_interest_total', 0))
        return source.get('source_total', 0)

# TypedDicts to clarify returned shapes (non-functional)
class SourceTotalResult(TypedDict, total=False):
    source_total: int
    bs_total: int
    pl_interest_total: int

class DifferenceResult(TypedDict, total=False):
    bs_total: int
    pl_interest_total: int
    breakdown_total: int
    difference: int

from __future__ import annotations

from typing import Any, Dict, List, Optional, TypedDict

from app.company.services.master_data_service import MasterDataService
from app.domain.soa.evaluation import SoAPageEvaluation
from app.services.soa_registry import PL_PAGE_ACCOUNTS, SUMMARY_PAGE_MAP
from app import db
from app.services.soa_registry import STATEMENT_PAGES_CONFIG  # ページ→モデル解決用


class SoASummaryService:
    """
    Service for computing Statement of Accounts (SoA) source totals, breakdown totals,
    differences, and skip decisions.

    Notes
    - Mappings are centralized in app.services.soa_registry and imported here and by the controller.
    - Public methods return primitive dicts/ints to keep controller context keys unchanged.
    """

    # mappings are imported from app.services.soa_registry

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
            return {'type': 'UNKNOWN', 'target_ids': [], 'targets': []}

        master_type, breakdown_name = SUMMARY_PAGE_MAP[page]
        if page == 'borrowings':
            bs_df = master_service.get_bs_master_df()
            bs_ids, bs_names = cls._extract_targets(bs_df, breakdown=breakdown_name)

            pl_df = master_service.get_pl_master_df()
            configured_names = PL_PAGE_ACCOUNTS.get(page, ['支払利息'])
            pl_ids, pl_names = cls._extract_targets(pl_df, names=configured_names or None)
            if not pl_ids and breakdown_name:
                alt_ids, alt_names = cls._extract_targets(pl_df, breakdown=breakdown_name)
                if alt_ids:
                    pl_ids, pl_names = alt_ids, alt_names

            return {
                'type': 'BORROWINGS',
                'bs_target_ids': bs_ids,
                'pl_target_ids': pl_ids,
                'bs_targets': bs_names,
                'pl_targets': pl_names or configured_names,
            }

        if master_type == 'BS':
            df = master_service.get_bs_master_df()
            target_ids, target_names = cls._extract_targets(df, breakdown=breakdown_name)
            return {'type': 'BS', 'target_ids': target_ids, 'targets': target_names}

        df = master_service.get_pl_master_df()
        configured_names = PL_PAGE_ACCOUNTS.get(page, [])
        target_ids, target_names = cls._extract_targets(df, names=configured_names or None)
        if not target_ids and breakdown_name:
            target_ids, target_names = cls._extract_targets(df, breakdown=breakdown_name)
        return {'type': 'PL', 'target_ids': target_ids, 'targets': target_names or configured_names}

    @classmethod
    def compute_source_total(cls, company_id: int, page: str, accounting_data=None, master_service: Optional[MasterDataService] = None) -> SourceTotalResult:
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

        master_service = master_service or MasterDataService()

        soa_breakdowns = {}
        account_balances = {}
        try:
            data_payload = accounting_data.data or {}
            if isinstance(data_payload, dict):
                candidate = data_payload.get('soa_breakdowns')
                if isinstance(candidate, dict):
                    soa_breakdowns = candidate
            account_balances = cls._extract_account_balances(accounting_data)
        except Exception:
            soa_breakdowns = {}

        targets_info = cls.resolve_target_accounts(page, master_service)

        if targets_info.get('type') == 'BORROWINGS':
            bs_ids = targets_info.get('bs_target_ids', [])
            pl_ids = targets_info.get('pl_target_ids', [])
            if account_balances and (bs_ids or pl_ids):
                bs_total = cls._sum_account_balances(account_balances, bs_ids)
                pl_interest_total = cls._sum_account_balances(account_balances, pl_ids)
                return {
                    'bs_total': bs_total,
                    'pl_interest_total': pl_interest_total,
                    'source_total': bs_total + pl_interest_total,
                }

            bs_source = accounting_data.data.get('balance_sheet', {})
            pl_source = accounting_data.data.get('profit_loss_statement', {})
            bs_total = cls._find_and_sum_by_names(bs_source, targets_info.get('bs_targets', []))
            if soa_breakdowns:
                breakdown_name = SUMMARY_PAGE_MAP.get(page, (None, None))[1]
                if breakdown_name:
                    bs_total = soa_breakdowns.get(breakdown_name, bs_total)
            pl_interest_total = cls._find_and_sum_by_names(pl_source, targets_info.get('pl_targets', []))
            return {
                'bs_total': bs_total,
                'pl_interest_total': pl_interest_total,
                'source_total': bs_total + pl_interest_total,
            }

        if targets_info.get('type') == 'BS':
            target_ids = targets_info.get('target_ids', [])
            if account_balances and target_ids:
                total = cls._sum_account_balances(account_balances, target_ids)
                return {'source_total': total}

            breakdown_name = SUMMARY_PAGE_MAP.get(page, (None, None))[1]
            if breakdown_name and soa_breakdowns and breakdown_name in soa_breakdowns:
                return {'source_total': soa_breakdowns[breakdown_name]}
            source = accounting_data.data.get('balance_sheet', {})
            total = cls._find_and_sum_by_names(source, targets_info.get('targets', []))
            return {'source_total': total}
        elif targets_info.get('type') == 'PL':
            target_ids = targets_info.get('target_ids', [])
            if account_balances and target_ids:
                total = cls._sum_account_balances(account_balances, target_ids)
                return {'source_total': total}

            source = accounting_data.data.get('profit_loss_statement', {})
            total = cls._find_and_sum_by_names(source, targets_info.get('targets', []))
            return {'source_total': total}
        else:
            return {'source_total': 0}

    @staticmethod
    def compute_breakdown_total(company_id: int, page: str, model, total_field_name: Optional[str]) -> int:
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

        if not total_field_name:
            total_field_name = 'amount'
        try:
            total_field = getattr(model, total_field_name)
        except AttributeError:
            return 0
        return db.session.query(db.func.sum(total_field)) \
            .filter_by(company_id=company_id).scalar() or 0

    @classmethod
    def compute_difference(cls, company_id: int, page: str, model, total_field_name: Optional[str], accounting_data=None, master_service: Optional[MasterDataService] = None, source_totals: Optional["SourceTotalResult"] = None) -> DifferenceResult:
        master_service = master_service or MasterDataService()
        source = source_totals or cls.compute_source_total(company_id, page, accounting_data=accounting_data, master_service=master_service)
        effective_model = model
        effective_field = total_field_name
        if effective_model is None or effective_field is None:
            cfg = STATEMENT_PAGES_CONFIG.get(page, {})
            effective_model = effective_model or cfg.get('model')
            effective_field = effective_field or cfg.get('total_field', 'amount')
        breakdown_total = cls.compute_breakdown_total(company_id, page, effective_model, effective_field)
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
    def compute_skip_total(cls, company_id: int, page: str, accounting_data=None, master_service: Optional[MasterDataService] = None, source_totals: Optional["SourceTotalResult"] = None) -> int:
        """Return the numeric source total used to determine skip."""
        source = source_totals or cls.compute_source_total(company_id, page, accounting_data=accounting_data, master_service=master_service)
        if page == 'borrowings':
            return (source.get('bs_total', 0) + source.get('pl_interest_total', 0))
        return source.get('source_total', 0)

    @classmethod
    def evaluate_page(cls, company_id: int, page: str, accounting_data=None) -> SoAPageEvaluation:
        """差分・スキップ判定・完了状態をまとめた結果を返す。"""
        master_service = MasterDataService()
        source_totals = cls.compute_source_total(
            company_id,
            page,
            accounting_data=accounting_data,
            master_service=master_service,
        )
        difference = cls.compute_difference(
            company_id,
            page,
            None,
            None,
            accounting_data=accounting_data,
            master_service=master_service,
            source_totals=source_totals,
        )
        skip_total = cls.compute_skip_total(
            company_id,
            page,
            accounting_data=accounting_data,
            master_service=master_service,
            source_totals=source_totals,
        )
        is_balanced = difference.get('difference', 0) == 0
        should_skip = skip_total == 0
        return SoAPageEvaluation(
            difference=difference,
            skip_total=skip_total,
            is_balanced=is_balanced,
            should_skip=should_skip,
        )

    @staticmethod
    def _extract_targets(df, *, breakdown: Optional[str] = None, names: Optional[List[str]] = None) -> tuple[List[int], List[str]]:
        if df is None or not hasattr(df, 'index'):
            return [], []
        subset = None
        try:
            if breakdown and 'breakdown_document' in getattr(df, 'columns', []):
                subset = df[df['breakdown_document'] == breakdown]
            elif names:
                subset = df[df.index.isin(names)]
            else:
                subset = df.iloc[0:0]
        except Exception:
            subset = df.iloc[0:0]

        target_names: List[str] = []
        ids: List[int] = []
        try:
            target_names = [str(name) for name in subset.index.tolist()]
        except Exception:
            target_names = []
        if hasattr(subset, 'columns') and 'id' in getattr(subset, 'columns', []):
            for raw_id in subset['id'].tolist():
                try:
                    ids.append(int(raw_id))
                except (TypeError, ValueError):
                    continue
        return ids, target_names

    @staticmethod
    def _extract_account_balances(accounting_data) -> Dict[int, int]:
        try:
            payload = getattr(accounting_data, 'data', {}) or {}
            raw_balances = payload.get('account_balances')
        except Exception:
            raw_balances = None
        if not isinstance(raw_balances, dict):
            return {}
        balances: Dict[int, int] = {}
        for key, value in raw_balances.items():
            try:
                account_id = int(key)
                balances[account_id] = int(value)
            except (TypeError, ValueError):
                continue
        return balances

    @staticmethod
    def _sum_account_balances(account_balances: Dict[int, int], account_ids: List[int]) -> int:
        total = 0
        for account_id in account_ids:
            value = account_balances.get(account_id)
            if value is None:
                continue
            try:
                total += abs(int(value))
            except (TypeError, ValueError):
                continue
        return total

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

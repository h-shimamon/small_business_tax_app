"""Backward-compatible import for Statement of Accounts mappings."""
from app.services.soa_registry import PL_PAGE_ACCOUNTS, SUMMARY_PAGE_MAP

__all__ = ['SUMMARY_PAGE_MAP', 'PL_PAGE_ACCOUNTS']

"""Backward-compatible import for Statement of Accounts configuration."""
from app.services.soa_registry import STATEMENT_PAGES_CONFIG, StatementPageConfig

__all__ = ['STATEMENT_PAGES_CONFIG', 'StatementPageConfig']

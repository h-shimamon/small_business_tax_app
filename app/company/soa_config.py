"""Backward-compatible import for Statement of Accounts configuration."""
from app.services.soa_registry import (
    STATEMENT_MODEL_PATHS,
    STATEMENT_PAGES_CONFIG,
    STATEMENT_TOTAL_FIELDS,
    StatementPageConfig,
)

__all__ = [
    'STATEMENT_PAGES_CONFIG',
    'STATEMENT_TOTAL_FIELDS',
    'STATEMENT_MODEL_PATHS',
    'StatementPageConfig',
]

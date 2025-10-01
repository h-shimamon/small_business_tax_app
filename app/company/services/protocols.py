"""Service layer protocol definitions for company domain services."""
from __future__ import annotations

from collections.abc import Iterable
from typing import Protocol


class StatementOfAccountsServiceProtocol(Protocol):
    """Contract for Statement of Accounts service implementations."""

    def list_items(self, data_type: str) -> Iterable[object]:
        ...

    def calculate_total(self, data_type: str, items: Iterable[object] | None = None) -> int:
        ...

    def get_item_by_id(self, data_type: str, item_id: int):
        ...

    def create_item(self, data_type: str, form) -> tuple[bool, object | None, str | None]:
        ...

    def update_item(self, data_type: str, item, form) -> tuple[bool, object | None, str | None]:
        ...

    def delete_item(self, data_type: str, item_id: int) -> tuple[bool, str | None]:
        ...


class ShareholderServiceProtocol(Protocol):
    """Contract for shareholder-related service operations."""

    def get_shareholders_by_company(self, company_id: int, user_id: int | None = None):
        ...

    def get_main_shareholders(self, company_id: int, user_id: int | None = None):
        ...

    def get_shareholder_by_id(self, shareholder_id: int, user_id: int | None = None):
        ...

    def add_shareholder(self, company_id: int, form, parent_id: int | None = None, user_id: int | None = None):
        ...

    def get_related_shareholders(self, main_shareholder_id: int, user_id: int | None = None):
        ...

    def update_shareholder(self, shareholder_id: int, form, user_id: int | None = None):
        ...

    def delete_shareholder(self, shareholder_id: int, user_id: int | None = None):
        ...

    def get_shareholder_form(self, shareholder):
        ...

    def is_same_address(self, a, b) -> bool:
        ...

    def get_main_shareholder_group_number(self, company_id: int, main_shareholder_id: int, user_id: int | None = None) -> int:
        ...

    def compute_company_total(self, company_id: int, user_id: int | None = None) -> int:
        ...

    def compute_group_total(self, company_id: int, main_shareholder_id: int, user_id: int | None = None) -> int:
        ...

    def compute_group_totals_map(self, company_id: int, user_id: int | None = None) -> dict[int, int]:
        ...

    def compute_group_totals_both_map(self, company_id: int, user_id: int | None = None) -> dict[int, dict[str, int]]:
        ...


class FilingsServiceProtocol(Protocol):
    def get_title(self, page: str) -> str | None:
        ...

    def get_template(self, page: str) -> str | None:
        ...

    def get_preview_pdf(self, page: str) -> str | None:
        ...

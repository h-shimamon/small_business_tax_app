"""Registry for Statement of Accounts PDF generators."""
from dataclasses import dataclass
from typing import Callable
@dataclass(frozen=True)
class StatementPDFConfig:
    generator: Callable[[int, str, str], str]
    filename_pattern: str
    download_name_pattern: str
STATEMENT_PDF_GENERATORS: dict[str, StatementPDFConfig] = {}
def register_statement_pdf(page_key: str, *, generator: Callable[[int, str, str], str],
                            filename_pattern: str, download_name_pattern: str | None = None) -> None:
    if download_name_pattern is None:
        download_name_pattern = filename_pattern
    STATEMENT_PDF_GENERATORS[page_key] = StatementPDFConfig(
        generator=generator,
        filename_pattern=filename_pattern,
        download_name_pattern=download_name_pattern,
    )
def get_statement_pdf_config(page_key: str) -> StatementPDFConfig | None:
    return STATEMENT_PDF_GENERATORS.get(page_key)

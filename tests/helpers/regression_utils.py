from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Protocol


class PdfGenerator(Protocol):
    def __call__(self, company_id: int | None, *, year: str, output_path: str) -> str:
        ...


def assert_pdf_smoke(generator: PdfGenerator, *, company_id: int | None = None, year: str = "2025") -> None:
    """Minimal regression helper for PDF generators.

    Usage::

        from tests.helpers.regression_utils import assert_pdf_smoke
        assert_pdf_smoke(generate_uchiwakesyo_urikakekin, company_id=example_company.id)

    The helper ensures the generator writes a PDF file at the requested path and
    returns that path. Temporary files are cleaned up automatically.
    """

    with TemporaryDirectory() as tmp_dir:
        output_path = Path(tmp_dir, "out.pdf")
        result = generator(company_id, year=year, output_path=str(output_path))
        assert Path(result).exists(), f"PDF not created: {result}"

from __future__ import annotations

"""Populate PDF registry with existing statement generators."""

from app.pdf.borrowings_two_tier import generate_borrowings_two_tier
from app.pdf.uchiwakesyo_kaikakekin import generate_uchiwakesyo_kaikakekin
from app.pdf.uchiwakesyo_uketoritegata import generate_uchiwakesyo_uketoritegata
from app.pdf.uchiwakesyo_karibaraikin_kashitukekin import generate_uchiwakesyo_karibaraikin_kashitukekin
from app.pdf.uchiwakesyo_urikakekin import generate_uchiwakesyo_urikakekin
from app.pdf.uchiwakesyo_shiharaitegata import generate_uchiwakesyo_shiharaitegata
from app.pdf.uchiwakesyo_yocyokin import generate_uchiwakesyo_yocyokin
from .pdf_registry import register_statement_pdf

register_statement_pdf(
    'deposits',
    generator=generate_uchiwakesyo_yocyokin,
    filename_pattern='uchiwakesyo_yocyokin_{company_id}_{timestamp}.pdf',
    download_name_pattern='uchiwakesyo_yocyokin_{year}.pdf',
)
register_statement_pdf(
    'accounts_receivable',
    generator=generate_uchiwakesyo_urikakekin,
    filename_pattern='uchiwakesyo_urikakekin_{company_id}_{timestamp}.pdf',
    download_name_pattern='uchiwakesyo_urikakekin_{year}.pdf',
)
register_statement_pdf(
    'notes_receivable',
    generator=generate_uchiwakesyo_uketoritegata,
    filename_pattern='uchiwakesyo_uketoritegata_{company_id}_{timestamp}.pdf',
    download_name_pattern='uchiwakesyo_uketoritegata_{year}.pdf',
)
register_statement_pdf(
    'temporary_payments',
    generator=generate_uchiwakesyo_karibaraikin_kashitukekin,
    filename_pattern='uchiwakesyo_karibaraikin-kashitukekin_{company_id}_{timestamp}.pdf',
    download_name_pattern='uchiwakesyo_karibaraikin-kashitukekin_{year}.pdf',
)
register_statement_pdf(
    'loans_receivable',
    generator=generate_uchiwakesyo_karibaraikin_kashitukekin,
    filename_pattern='uchiwakesyo_karibaraikin-kashitukekin_{company_id}_{timestamp}.pdf',
    download_name_pattern='uchiwakesyo_karibaraikin-kashitukekin_{year}.pdf',
)
register_statement_pdf(
    'notes_payable',
    generator=generate_uchiwakesyo_shiharaitegata,
    filename_pattern='uchiwakesyo_shiharaitegata_{company_id}_{timestamp}.pdf',
    download_name_pattern='uchiwakesyo_shiharaitegata_{year}.pdf',
)
register_statement_pdf(
    'accounts_payable',
    generator=generate_uchiwakesyo_kaikakekin,
    filename_pattern='uchiwakesyo_kaikakekin_{company_id}_{timestamp}.pdf',
    download_name_pattern='uchiwakesyo_kaikakekin_{year}.pdf',
)
register_statement_pdf(
    'borrowings',
    generator=generate_borrowings_two_tier,
    filename_pattern='borrowings_two_tier_{company_id}_{timestamp}.pdf',
    download_name_pattern='borrowings_two_tier_{year}.pdf',
)

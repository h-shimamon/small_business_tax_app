from app.services.pdf_registry import (
    STATEMENT_PDF_GENERATORS,
    get_statement_pdf_config,
    register_statement_pdf,
)


def test_register_and_get_pdf_config():
    STATEMENT_PDF_GENERATORS.clear()
    register_statement_pdf(
        'sample',
        generator=lambda company_id, year, output_path: None,
        filename_pattern='sample_{company_id}_{timestamp}.pdf',
        download_name_pattern='sample_{year}.pdf',
    )

    config = get_statement_pdf_config('sample')

    assert config is not None
    assert config.filename_pattern == 'sample_{company_id}_{timestamp}.pdf'
    assert config.download_name_pattern == 'sample_{year}.pdf'


def test_get_pdf_config_returns_none_when_missing():
    STATEMENT_PDF_GENERATORS.clear()
    assert get_statement_pdf_config('missing') is None

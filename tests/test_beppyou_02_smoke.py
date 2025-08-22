from pathlib import Path

from app import db
from app.company.models import Company, Shareholder
from app.pdf.beppyou_02 import generate_beppyou_02


def test_beppyou_02_generate_smoke(app, init_database):
    """Smoke: PDF generation runs without exceptions (geometry defaults/overrides)."""
    with app.app_context():
        # Arrange: ensure company has period strings to exercise wareki rendering
        company = Company.query.first()
        company.accounting_period_start = "2025-01-01"
        company.accounting_period_end = "2025-12-31"
        db.session.commit()

        # Ensure we have some main and related shareholders for top3 totals
        main2 = Shareholder(company_id=company.id, last_name="主2", shares_held=100)
        rel21 = Shareholder(company_id=company.id, last_name="関2-1", parent=main2, shares_held=50)
        main3 = Shareholder(company_id=company.id, last_name="主3", shares_held=200)
        db.session.add_all([main2, rel21, main3])
        db.session.commit()

        out_dir = Path("temporary/filled")
        out_dir.mkdir(parents=True, exist_ok=True)
        out = out_dir / "beppyou_02_smoke.pdf"

        # Act: generate PDF
        path = generate_beppyou_02(company_id=company.id, year="2025", output_path=str(out))

        # Assert: file exists and non-empty
        p = Path(path)
        assert p.exists(), "Output PDF should be created"
        assert p.stat().st_size > 0, "Output PDF should not be empty"


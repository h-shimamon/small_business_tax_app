from pathlib import Path

from app.pdf.uchiwakesyo_urikakekin import generate_uchiwakesyo_urikakekin
from app.company.models import Company


def test_uchiwakesyo_urikakekin_generate_smoke(app, init_database):
    """Smoke: PDF generation runs without exceptions and creates a non-empty file."""
    with app.app_context():
        company = Company.query.first()
        out_dir = Path("temporary/filled")
        out_dir.mkdir(parents=True, exist_ok=True)
        out = out_dir / "uchiwakesyo_urikakekin_smoke.pdf"

        path = generate_uchiwakesyo_urikakekin(company_id=company.id, year="2025", output_path=str(out))

        p = Path(path)
        assert p.exists(), "Output PDF should be created"
        assert p.stat().st_size > 0, "Output PDF should not be empty"


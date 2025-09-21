from __future__ import annotations

import csv
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Dict, Iterable

from app import create_app, db
from app.company.models import CorporateTaxMaster

DATA_PATH = Path(__file__).resolve().parents[1] / 'resources' / 'masters' / 'corporate_tax_master.csv'


def _parse_date(value: str):
    return datetime.strptime(value.strip(), '%Y-%m-%d').date()


def _parse_int(value: str) -> int:
    return int(value.strip())


def _parse_decimal(value: str) -> Decimal:
    try:
        return Decimal(value.strip())
    except (InvalidOperation, AttributeError):
        return Decimal('0')


def _load_rows() -> Iterable[Dict[str, object]]:
    if not DATA_PATH.exists():
        raise FileNotFoundError(f'Data file not found: {DATA_PATH}')
    with DATA_PATH.open(newline='', encoding='utf-8') as fh:
        reader = csv.DictReader(fh)
        for raw in reader:
            if not raw.get('fiscal_start_date'):
                continue
            yield {
                'fiscal_start_date': _parse_date(raw['fiscal_start_date']),
                'fiscal_end_date': _parse_date(raw['fiscal_end_date']),
                'months_standard': _parse_int(raw['months_standard']),
                'months_truncated': _parse_int(raw['months_truncated']),
                'corporate_tax_rate_u8m': _parse_decimal(raw['corporate_tax_rate_u8m']),
                'corporate_tax_rate_o8m': _parse_decimal(raw['corporate_tax_rate_o8m']),
                'local_corporate_tax_rate': _parse_decimal(raw['local_corporate_tax_rate']),
                'enterprise_tax_rate_u4m': _parse_decimal(raw['enterprise_tax_rate_u4m']),
                'enterprise_tax_rate_4m_8m': _parse_decimal(raw['enterprise_tax_rate_4m_8m']),
                'enterprise_tax_rate_o8m': _parse_decimal(raw['enterprise_tax_rate_o8m']),
                'local_special_tax_rate': _parse_decimal(raw['local_special_tax_rate']),
                'prefectural_corporate_tax_rate': _parse_decimal(raw['prefectural_corporate_tax_rate']),
                'prefectural_equalization_amount': _parse_int(raw['prefectural_equalization_amount']),
                'municipal_corporate_tax_rate': _parse_decimal(raw['municipal_corporate_tax_rate']),
                'municipal_equalization_amount': _parse_int(raw['municipal_equalization_amount']),
            }


def _upsert_row(payload: Dict[str, object]) -> None:
    record = CorporateTaxMaster.query.filter_by(fiscal_start_date=payload['fiscal_start_date']).first()
    if record:
        for key, value in payload.items():
            setattr(record, key, value)
    else:
        record = CorporateTaxMaster(**payload)
        db.session.add(record)


def main() -> None:
    app = create_app()
    with app.app_context():
        rows = list(_load_rows())
        if not rows:
            print('[seed-corporate-tax] No rows found in CSV. Aborting.')
            return
        for row in rows:
            _upsert_row(row)
        db.session.commit()
        print(f"[seed-corporate-tax] Upserted {len(rows)} rows into corporate_tax_master.")


if __name__ == '__main__':
    main()

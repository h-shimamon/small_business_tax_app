from datetime import date, datetime
from pathlib import Path
import csv
from decimal import Decimal

import pytest

from app import db
from app.company.models import AccountingData, Company, CorporateTaxMaster
from app.company.services.corporate_tax_service import CorporateTaxCalculationService



BASE_MANUAL_INPUTS = {
    'fiscal_start_date': '20240401',
    'fiscal_end_date': '20250331',
    'months_in_period': '12',
    'months_truncated': '12',
    'pre_tax_income': '0',
    'corporate_tax_rate_low': '15',
    'corporate_tax_rate_high': '23.2',
    'local_corporate_tax_rate': '10.3',
    'enterprise_tax_rate_u4m': '3.5',
    'enterprise_tax_rate_4m_8m': '5.3',
    'enterprise_tax_rate_o8m': '7',
    'local_special_tax_rate': '43.2',
    'prefectural_corporate_tax_rate': '1',
    'prefectural_equalization_amount': '20000',
    'municipal_corporate_tax_rate': '6',
    'municipal_equalization_amount': '50000',
}


def _build_manual_result(overrides: dict):
    service = CorporateTaxCalculationService()
    inputs_payload = BASE_MANUAL_INPUTS.copy()
    for key, value in overrides.items():
        if value is None:
            inputs_payload[key] = ''
        elif isinstance(value, str):
            inputs_payload[key] = value
        else:
            inputs_payload[key] = str(value)
    return service.build_from_manual(inputs_payload)


def _load_case_rows():
    path = Path(__file__).parent / "data" / "corporate_tax_cases.csv"
    if not path.exists():
        return []
    with path.open(encoding='utf-8') as fp:
        return list(csv.DictReader(fp))


CASE_ROWS = _load_case_rows()

def test_corporate_tax_calculation_service_builds_context(app, init_database):
    with app.app_context():
        company = Company.query.first()
        company.accounting_period_start_date = date(2024, 4, 1)
        company.accounting_period_end_date = date(2025, 3, 31)
        db.session.add(company)

        db.session.add(CorporateTaxMaster(
            fiscal_start_date=date(2024, 4, 1),
            fiscal_end_date=date(2025, 3, 31),
            months_standard=12,
            months_truncated=12,
            corporate_tax_rate_u8m=15.00,
            corporate_tax_rate_o8m=23.20,
            local_corporate_tax_rate=10.30,
            enterprise_tax_rate_u4m=3.50,
            enterprise_tax_rate_4m_8m=5.30,
            enterprise_tax_rate_o8m=7.00,
            local_special_tax_rate=43.20,
            prefectural_corporate_tax_rate=1.00,
            prefectural_equalization_amount=20000,
            municipal_corporate_tax_rate=6.00,
            municipal_equalization_amount=50000,
        ))

        data = {
            'profit_loss_statement': {
                '利益計算': {
                    '税引前当期純利益': {'total': 12_000_000},
                }
            }
        }
        db.session.add(AccountingData(
            company_id=company.id,
            period_start=date(2024, 4, 1),
            period_end=date(2025, 3, 31),
            data=data,
        ))
        db.session.commit()

        service = CorporateTaxCalculationService()
        inputs, results, breakdown = service.build(company.id)

        assert inputs['fiscal_start_date'] == '20240401'
        assert inputs['fiscal_end_date'] == '20250331'
        assert inputs['months_in_period'] == 12
        assert inputs['months_truncated'] == 12
        assert inputs['pre_tax_income'] == 12_000_000
        assert inputs['corporate_tax_rate_low'] == '15%'
        assert inputs['corporate_tax_rate_high'] == '23.2%'
        assert inputs['local_corporate_tax_rate'] == '10.3%'
        assert inputs['enterprise_tax_rate_u4m'] == '3.5%'
        assert inputs['enterprise_tax_rate_4m_8m'] == '5.3%'
        assert inputs['enterprise_tax_rate_o8m'] == '7%'
        assert inputs['local_special_tax_rate'] == '43.2%'
        assert inputs['prefectural_corporate_tax_rate'] == '1%'
        assert inputs['prefectural_equalization_amount'] == 20_000
        assert inputs['municipal_corporate_tax_rate'] == '6%'
        assert inputs['municipal_equalization_amount'] == 50_000
        assert results['corporate_tax'] == 2_128_000
        assert results['local_tax'] == 1_342_900
        assert results['total_tax'] == 3_470_900
        assert results['payment_rate'] == '28.9%'
        assert results['effective_rate'] == '26.9%'
        assert results['enterprise_tax_total'] == 905_000
        assert results['pref_tax_total'] == 41_200
        assert results['local_corporate_tax'] == 219_100
        assert results['municipal_tax_total'] == 177_600
        assert breakdown['corporate_tax_low_rate'] == 1_200_000
        assert breakdown['corporate_tax_high_rate'] == 928_000
        assert breakdown['enterprise_tax_base'] == 12_000_000
        assert breakdown['enterprise_income_u4m'] == 4_000_000
        assert breakdown['enterprise_base_u4m'] == 4_000_000
        assert breakdown['enterprise_income_4m_8m'] == 8_000_000
        assert breakdown['enterprise_base_4m_8m'] == 4_000_000
        assert breakdown['enterprise_income_o8m'] == 4_000_000
        assert breakdown['enterprise_base_o8m'] == 4_000_000
        assert breakdown['enterprise_tax_u4m'] == 140_000
        assert breakdown['enterprise_tax_4m_8m'] == 212_000
        assert breakdown['enterprise_tax_o8m'] == 280_000
        assert breakdown['pref_tax_base'] == 2_128_000
        assert breakdown['municipal_tax_base'] == 2_128_000


@pytest.mark.parametrize(
    "pre_tax_income, expected_corporate_tax, expected_local_corporate_tax",
    [
        (1_000_000, 150_000, 15_400),
        (986_900, 148_000, 15_200),
        (9_000_000, 1_432_000, 147_400),
    ],
    ids=["one_million", "rounding_down", "exceeds_eight_million"],
)
def test_manual_calculation_rounding(pre_tax_income, expected_corporate_tax, expected_local_corporate_tax):
    _, results, _ = _build_manual_result({'pre_tax_income': pre_tax_income})
    assert results['corporate_tax'] == expected_corporate_tax
    assert results['local_corporate_tax'] == expected_local_corporate_tax


def test_manual_calculation_infers_months_from_dates():
    inputs, results, _ = _build_manual_result(
        {
            'fiscal_start_date': '20220401',
            'fiscal_end_date': '20230131',
            'months_in_period': '',
            'months_truncated': '',
            'pre_tax_income': 2_000_000,
        }
    )
    assert inputs['months_in_period'] == 10
    assert inputs['months_truncated'] == 10
    # monthsが推定されても法人税(国)と地方法人税が一貫して算出されることを確認
    assert results['corporate_tax'] == 300_000
    assert results['local_corporate_tax'] == 30_900


def test_manual_calculation_handles_non_positive_income():
    _, results, breakdown = _build_manual_result({'pre_tax_income': -1000})
    assert results['corporate_tax'] == 0
    assert results['local_corporate_tax'] == 0
    assert results['local_tax'] == 70_000
    assert breakdown['enterprise_tax_base'] == 0


@pytest.mark.parametrize('case_row', CASE_ROWS, ids=lambda row: row['case_id'])
def test_manual_cases_from_csv(case_row):
    if not case_row:
        pytest.skip('corporate tax case data is not available')
    overrides = {
        'pre_tax_income': case_row['pre_tax_income'],
        'fiscal_start_date': case_row['fiscal_start_date'],
        'fiscal_end_date': case_row['fiscal_end_date'],
        'months_in_period': case_row['months_in_period'],
        'months_truncated': case_row['months_truncated'],
    }
    _, results, _ = _build_manual_result(overrides)

    assert results['corporate_tax'] == int(case_row['expected_corporate_tax'])
    assert results['local_corporate_tax'] == int(case_row['expected_local_corporate_tax'])
    assert results['local_tax'] == int(case_row['expected_local_tax'])
    assert results['total_tax'] == int(case_row['expected_total_tax'])
    assert results['payment_rate'] == case_row['expected_payment_rate']
    assert results['effective_rate'] == case_row['expected_effective_rate']


def test_corporate_tax_master_csv_alignment(app, init_database):
    csv_path = Path(__file__).resolve().parents[1] / "resources/masters/corporate_tax_master.csv"
    with csv_path.open(encoding='utf-8') as fp:
        reader = csv.DictReader(fp)
        rows = list(reader)

    assert rows, "corporate_tax_master.csv に行が存在しません"

    with app.app_context():
        # テーブルを初期化して CSV の内容のみを検証する
        CorporateTaxMaster.query.delete()
        db.session.commit()

        for row in rows:
            master = CorporateTaxMaster(
                fiscal_start_date=datetime.strptime(row['fiscal_start_date'], '%Y-%m-%d').date(),
                fiscal_end_date=datetime.strptime(row['fiscal_end_date'], '%Y-%m-%d').date(),
                months_standard=int(row['months_standard']),
                months_truncated=int(row['months_truncated']),
                corporate_tax_rate_u8m=Decimal(row['corporate_tax_rate_u8m']),
                corporate_tax_rate_o8m=Decimal(row['corporate_tax_rate_o8m']),
                local_corporate_tax_rate=Decimal(row['local_corporate_tax_rate']),
                enterprise_tax_rate_u4m=Decimal(row['enterprise_tax_rate_u4m']),
                enterprise_tax_rate_4m_8m=Decimal(row['enterprise_tax_rate_4m_8m']),
                enterprise_tax_rate_o8m=Decimal(row['enterprise_tax_rate_o8m']),
                local_special_tax_rate=Decimal(row['local_special_tax_rate']),
                prefectural_corporate_tax_rate=Decimal(row['prefectural_corporate_tax_rate']),
                prefectural_equalization_amount=int(row['prefectural_equalization_amount']),
                municipal_corporate_tax_rate=Decimal(row['municipal_corporate_tax_rate']),
                municipal_equalization_amount=int(row['municipal_equalization_amount']),
            )
            db.session.add(master)
        db.session.commit()

        stored_rows = CorporateTaxMaster.query.order_by(CorporateTaxMaster.fiscal_start_date).all()
        assert len(stored_rows) == len(rows)

        for stored, row in zip(stored_rows, rows):
            assert stored.fiscal_start_date == datetime.strptime(row['fiscal_start_date'], '%Y-%m-%d').date()
            assert stored.fiscal_end_date == datetime.strptime(row['fiscal_end_date'], '%Y-%m-%d').date()
            assert stored.months_standard == int(row['months_standard'])
            assert stored.months_truncated == int(row['months_truncated'])
            assert stored.corporate_tax_rate_u8m == Decimal(row['corporate_tax_rate_u8m'])
            assert stored.corporate_tax_rate_o8m == Decimal(row['corporate_tax_rate_o8m'])
            assert stored.local_corporate_tax_rate == Decimal(row['local_corporate_tax_rate'])
            assert stored.enterprise_tax_rate_u4m == Decimal(row['enterprise_tax_rate_u4m'])
            assert stored.enterprise_tax_rate_4m_8m == Decimal(row['enterprise_tax_rate_4m_8m'])
            assert stored.enterprise_tax_rate_o8m == Decimal(row['enterprise_tax_rate_o8m'])
            assert stored.local_special_tax_rate == Decimal(row['local_special_tax_rate'])
            assert stored.prefectural_corporate_tax_rate == Decimal(row['prefectural_corporate_tax_rate'])
            assert stored.prefectural_equalization_amount == int(row['prefectural_equalization_amount'])
            assert stored.municipal_corporate_tax_rate == Decimal(row['municipal_corporate_tax_rate'])
            assert stored.municipal_equalization_amount == int(row['municipal_equalization_amount'])

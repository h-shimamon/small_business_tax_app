from datetime import date

from datetime import date

from app import db
from app.company.models import AccountingData, Company, CorporateTaxMaster
from app.company.services.corporate_tax_service import CorporateTaxCalculationService


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
            prefectural_equalization_amount=21000,
            municipal_corporate_tax_rate=3.00,
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
        assert inputs['prefectural_equalization_amount'] == 21_000
        assert inputs['municipal_corporate_tax_rate'] == '3%'
        assert inputs['municipal_equalization_amount'] == 50_000
        assert results['corporate_tax'] == 2_128_000
        assert results['local_tax'] == 1_280_100
        assert results['total_tax'] == 3_408_100
        assert results['payment_rate'] == '28.4%'
        assert results['effective_rate'] == '26.4%'
        assert results['enterprise_tax_total'] == 905_000
        assert results['pref_tax_total'] == 42_200
        assert results['local_corporate_tax'] == 101_500
        assert results['municipal_tax_total'] == 113_800
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
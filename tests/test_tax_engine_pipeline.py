from decimal import Decimal

import pytest

from app.tax_engine.models import TaxPeriod
from app.tax_engine.pipeline import TaxComputationPipeline


class DummyMaster:
    def __init__(self):
        self.corporate_tax_rate_u8m = '15.0'
        self.corporate_tax_rate_o8m = '23.2'
        self.local_corporate_tax_rate = '10.3'
        self.enterprise_tax_rate_u4m = '3.5'
        self.enterprise_tax_rate_4m_8m = '5.3'
        self.enterprise_tax_rate_o8m = '7.0'
        self.local_special_tax_rate = '37.0'
        self.prefectural_corporate_tax_rate = '1.0'
        self.prefectural_equalization_amount = 20000
        self.municipal_corporate_tax_rate = '6.0'
        self.municipal_equalization_amount = 50000


@pytest.fixture
def tax_period():
    return TaxPeriod(
        fiscal_start=None,
        fiscal_end=None,
        months_in_period=12,
        months_truncated=12,
    )


def test_pipeline_requires_master(tax_period):
    pipeline = TaxComputationPipeline(lambda: None)
    with pytest.raises(ValueError):
        pipeline.compute(taxable_income=Decimal('1000000'), period=tax_period)


def test_pipeline_computes_with_master(tax_period):
    master = DummyMaster()
    pipeline = TaxComputationPipeline(lambda: master)
    result = pipeline.compute(taxable_income=Decimal('1000000'), period=tax_period)
    assert result.components.corporate_total > 0

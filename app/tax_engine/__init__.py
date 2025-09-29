"""Tax computation engine package."""
from __future__ import annotations

from .engine import calculate_tax
from .models import (
    EqualizationAmounts,
    IncomeBands,
    TaxBreakdown,
    TaxCalculation,
    TaxComponents,
    TaxInput,
    TaxPeriod,
    TaxRates,
)
from .pipeline import TaxComputationPipeline
from .rates import (
    DEFAULT_EQUALIZATION_DEFAULTS,
    DEFAULT_RATE_DEFAULTS,
    build_equalization_amounts,
    build_tax_rates,
)

__all__ = [
    'calculate_tax',
    'EqualizationAmounts',
    'IncomeBands',
    'TaxBreakdown',
    'TaxCalculation',
    'TaxComponents',
    'TaxInput',
    'TaxPeriod',
    'TaxRates',
    'TaxComputationPipeline',
    'DEFAULT_EQUALIZATION_DEFAULTS',
    'DEFAULT_RATE_DEFAULTS',
    'build_equalization_amounts',
    'build_tax_rates',
]

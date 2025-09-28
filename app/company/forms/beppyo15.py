from __future__ import annotations

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Length

from app.company.beppyo15.constants import BEPPYO15_FIELD_DEFINITIONS
from .base_fields import MoneyField, MemoField


_FIELD_DEFINITION_MAP = {definition.key: definition for definition in BEPPYO15_FIELD_DEFINITIONS}


def _placeholder(key: str) -> str | None:
    definition = _FIELD_DEFINITION_MAP.get(key)
    return definition.placeholder if definition else None


class Beppyo15BreakdownForm(FlaskForm):
    subject = StringField(
        '科目',
        validators=[DataRequired(message='科目は必須です。'), Length(max=100)],
        render_kw={'placeholder': _placeholder('subject')},
    )
    expense_amount = MoneyField(
        '支出額',
        required=True,
        min_value=0,
    )
    deductible_amount = MoneyField(
        '交際費等の額から控除される費用の額',
        required=False,
        min_value=0,
    )
    net_amount_display_field = StringField(
        '差引交際費等の額(A)',
        render_kw={'readonly': True},
    )
    hospitality_amount = MoneyField(
        '(A)のうち接待飲食費の額',
        required=False,
        min_value=0,
    )
    remarks = MemoField('備考', max_length=200)
    submit = SubmitField('保存する')

    @property
    def net_amount_display(self) -> int:
        expense = self.expense_amount.data or 0
        deductible = self.deductible_amount.data or 0
        try:
            return expense - deductible
        except TypeError:
            return 0

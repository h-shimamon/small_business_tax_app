from __future__ import annotations

from wtforms import IntegerField, StringField
from wtforms.validators import DataRequired, Length, NumberRange, Regexp
from wtforms.validators import Optional as Opt


class AddressMixin:
    """共通住所フィールド（任意入力・長さ上限のみ）"""
    zip_code = StringField('郵便番号', validators=[Opt(), Length(min=0, max=7)])
    prefecture_city = StringField('都道府県・市区町村', validators=[Opt(), Length(max=100)])
    address = StringField('番地以降の住所', validators=[Opt(), Length(max=200)])


def _strip_hyphens_spaces(value: str | None) -> str | None:
    if value is None:
        return value
    return value.replace('-', '').replace(' ', '').strip()


def CorporateNumberField(label: str = "法人番号", required: bool = False, max_len: int = 13):
    """
    法人番号（13桁）: ハイフン・空白を入力時に除去。ソフトバリデーション（API照会なし）。
    required=True の場合は DataRequired を付与。
    """
    validators = [Length(min=max_len, max=max_len), Regexp(r"^\d{13}$", message="13桁の数字で入力してください。")]
    if not required:
        validators = [Opt()] + validators
    else:
        validators = [DataRequired()] + validators
    return StringField(label, validators=validators, filters=[_strip_hyphens_spaces])


def _strip_thousand_sep(value: str | None) -> str | None:
    if value is None:
        return value
    if isinstance(value, (int, float)):
        return value
    return value.replace(',', '').replace(' ', '').strip()


def MoneyField(label: str = "金額", required: bool = True, min_value: int = 0):
    """
    金額: 千区切り許容。DB互換のため IntegerField を採用（Decimal未導入）。
    将来 Decimal 化する際はここだけを変更する。
    """
    validators = [NumberRange(min=min_value)]
    if required:
        validators = [DataRequired()] + validators
    else:
        validators = [Opt()] + validators
    return IntegerField(label, validators=validators, filters=[_strip_thousand_sep])


def MemoField(label: str = "摘要", max_length: int = 200):
    """摘要: 任意・長さ上限のみ"""
    return StringField(label, validators=[Opt(), Length(max=max_length)])

# スキーマ整合チェックメモ

## 概要
- `app/company/model_parts` に再配置した ORM モデルを基準に、フォーム・テンプレート・設定ファイルの項目名を棚卸。
- `tests/test_soa_config_integrity.py` で `STATEMENT_PAGES_CONFIG` とフォーム定義の整合性を常時検証。
- DB カラムとフォーム入力名称が乖離する箇所は、以下の `観測点` で補足対応。

## 観測点
| モデル | カラム | フォーム項目 | 備考 |
| --- | --- | --- | --- |
| `Company` | `office_count` (`String`) | `DeclarationForm.office_count` (`RadioField`) | ラジオ選択肢をコードとして保存する想定。将来的に `Enum` 化を検討。 |
| `LoansReceivable` | `interest_rate` (`Float`) | `LoansReceivableForm.interest_rate` | テキスト入力だが数値として受理。`MoneyField` 等を使わず正規化する。 |
| `Borrowing` | `paid_interest` (`Integer`) | `BorrowingForm.paid_interest` | タイプ整合済み。ただし千円単位入力への誘導が未実装。 |
| `Miscellaneous` | `account_name` | `MiscellaneousIncomeForm.account_name` | HiddenField 固定値で整合。 |

## 今後の指針
1. `Enum`／`HybridProperty` の活用で、コード値と表示用ラベルを分離する。
2. マイグレーションが必要な型変更は、影響調査の上で段階的に実施。現状は互換性維持のためプロパティレベルで吸収する。
3. ドキュメント更新とテスト強化（本書＋`tests/test_soa_config_integrity.py`）をセットで運用する。
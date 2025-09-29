# データモデル / フィールド命名規約

本ドキュメントは会計データと税計算ドメインの主要キーを統一するための指針を示します。UI実装やAPIでは本規約に従ってください。

## 1. 勘定科目マスタ

| 項目 | 説明 | 対応ファイル | 備考 |
| --- | --- | --- | --- |
| `number` | 勘定科目コード (整数) | `resources/masters/*` | CSV上は `No.` |
| `name` | 勘定科目名 (日本語) | `resources/masters/*` | CSV上は `勘定科目名` |
| `statement_name` | 決算書上表記 | `resources/masters/*` | 省略可 |
| `major_category` / `middle_category` / `minor_category` | 階層カテゴリ | `resources/masters/*` | 省略可 |
| `breakdown_document` | 対応内訳書 | `resources/masters/balance_sheet.csv` | 省略可 |

## 2. 仕訳データ正規化キー

`app/company/parsers/normalizers.py` を利用し、外部CSV列を以下のキーへ写像します。

| 正規化キー | 意味 | 主な外部列例 |
| --- | --- | --- |
| `txn_id` | 取引番号 | `取引No.` |
| `date` | 取引日 (datetime) | `取引日`, `日付` |
| `debit_account` / `credit_account` | 勘定科目 (借方/貸方) | `借方勘定科目`, `貸方勘定科目` |
| `debit_amount` / `credit_amount` | 金額 (int) | `借方金額`, `貸方金額` |
| `tax_code` | 税区分識別子 | 会計ソフト固有列 |

正規化後も元の列名は保持されます。内部処理は正規化キーを参照してください。

## 3. 税計算ドメイン

`app/tax_engine/models.py` に定義されたデータクラスを唯一のソースとし、既存の `app/domain/tax/*` は互換レイヤとして扱います。

| モデル | 用途 |
| --- | --- |
| `TaxInput` | 税額計算の入力値 (課税所得、期間、税率等) |
| `TaxCalculation` | 中間結果 (内訳/課税基準/構成要素) |
| `TaxBreakdown` | UIおよびPDFへの出力ペイロード |

## 4. 命名ルール

- 物理名 (CSV/DB列) は `snake_case`、UIの `name` 属性は `.` 区切り (`beppyo4.plus.non_deductible`) を推奨。
- いずれかの層で新しい列を追加する場合は、本書に追記し、該当CSV/モデル/テンプレートの対応を明記してください。

## 5. ドキュメント更新フロー

1. 新しい列・キーを追加する際は、本ファイルにエントリを追加
2. `resources/masters/README.md` で物理列の仕様を追記
3. 変更がDBへ及ぶ場合はマイグレーション方針を `docs/` 配下で共有

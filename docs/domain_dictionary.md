# ドメイン逆引き辞書

| ビジネス用語 | テーブル / モデル | 主なカラム例 | 主な画面やサービス |
| --- | --- | --- | --- |
| 会社情報 | `company` / `Company` | `company_name`, `corporate_number`, `accounting_period_start_date`, `is_excluded_business` | `/company/info` (`CompanyService`), `company/company_info_form.html` |
| 株主 | `shareholder` / `Shareholder` | `last_name`, `entity_type`, `shares_held`, `parent_id` | `/company/shareholder_list`, `/company/register_shareholder` (`shareholders.py`) |
| 関連株主 | `shareholder` / `Shareholder` （`parent_id` 付き） | `parent_id`, `is_controlled_company`, `relationship` | `/company/register_related_shareholder`, `ShareholderService` |
| 事業所 | `office` / `Office` | `name`, `zip_code`, `employee_count`, `opening_date` | `/company/office_form`, `/company/office_list` |
| 勘定科目内訳書 | `soa_*` 系モデル群 | 各帳票ごとの金額・補足情報列 | `/company/statement_of_accounts` (`statement_of_accounts_service.py`) |
| 会計データ取込 | `accounting_data` / `AccountingData` | `schema_version`, `source_hash`, `created_at` | `/company/upload_data` (`import_data.py`) |
| 申告書レジストリ | `corporate_tax_master` / `CorporateTaxMaster` | `fiscal_start_date`, `fiscal_end_date`, 各種税率列 | `/company/filings` (`filings.py`, `corporate_tax_service.py`) |

## 命名指針メモ
- 株主機能では "Shareholder" が正式名称です。旧来の "Employee" という呼称は置き換え済みで、残存していないことを `rg "Employee"` で検証済みです。
- 追加のドメイン用語が増えた場合は、本ファイルにテーブル/モデル/画面の対応を追記してください。

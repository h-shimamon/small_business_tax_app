# マスターファイル仕様

本ディレクトリには会計マスターデータのCSVが格納されています。列名は日本語表記ですが、取り込み時には以下のキー設計に基づき正規化されます。

## 共通ルール

- 文字コード: UTF-8 (BOM付き)
- 先頭行: 列名ヘッダー
- 空行のみのレコードは無視されます
- 主要列は `app/services/master_data_loader.load_master_dataframe` でトリム（前後の空白除去）されます

| CSV | 物理列名 | 内部キー | 説明 |
| --- | --- | --- | --- |
| balance_sheet.csv | `No.` | `number` | 勘定科目コード（整数） |
| balance_sheet.csv | `勘定科目名` | `name` | 科目名称（BS） |
| balance_sheet.csv | `決算書名` | `statement_name` | 決算書上の表記 |
| balance_sheet.csv | `大分類` / `中分類` / `小分類` | `major_category` / `middle_category` / `minor_category` | 階層カテゴリ |
| balance_sheet.csv | `内訳書` | `breakdown_document` | 対応する内訳書 |
| profit_and_loss.csv | `No.` | `number` | 勘定科目コード（整数） |
| profit_and_loss.csv | `勘定科目名` | `name` | 科目名称（PL） |
| profit_and_loss.csv | `決算書名` ほか分類列 | `statement_name` など | BSと同様 |

## SQLAlchemy モデルとの対応

`app/company/model_parts/master_entities.py` の `AccountTitleMaster` に以下の形でマッピングされます。

- `number` → `AccountTitleMaster.number`
- `name` → `AccountTitleMaster.name`
- `statement_name` → `AccountTitleMaster.statement_name`
- `major_category` / `middle_category` / `minor_category`
- `breakdown_document`
- `master_type` は読込元（BS or PL）で補完

## バージョン管理

- `_version.txt` にマスターファイル群のハッシュ値を保存します
- `app/company/services/master_data_service.py` が起動時にファイルとDBを比較し、不一致時は同期を実行します
- 同期後は `clear_master_dataframe_cache()` を呼び出し、CSV読込キャッシュを無効化します

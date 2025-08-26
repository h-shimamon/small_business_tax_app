# Repository Index: small_business_tax_app (2025-08-25)

## 概要
- フレームワーク: Flask 構成（`run.py`, `app/__init__.py`, `config.py`）
- ドメイン: 会社情報・会計期間・株主・各種帳票（PDF生成・申告書・総勘定など）
- データ: Alembic マイグレーション、CSV マスタ、PDF テンプレート

## ディレクトリ構成
- `app/`: アプリ本体（拡張・UI・ドメインロジック）
- `migrations/`: Alembic マイグレーション
- `resources/`: PDF テンプレ JSON、フォーム PDF、フォント、マスタ CSV
- `tests/`: Pytest 単体テスト・Playwright E2E
- `docs/`: ハンドオーバー、要件メモ
- ルート: `run.py`, `config.py`, `pyproject.toml`, `requirements.txt`

## 主要モジュール（app）
- 基盤: `app/__init__.py`, `app/extensions.py`, `app/utils.py`, `app/constants.py`
- ナビゲーション: `app/navigation.py`, `app/navigation_builder.py`, `app/navigation_models.py`, `app/navigation_completion.py`
- コマンド: `app/commands.py`
- UI 資産: `app/static/*`, `app/templates/*`
- プリミティブ: `app/primitives/{dates, wareki, reporting}.py`
- モデルユーティリティ: `app/models_utils/{date_readers.py, date_sync.py}`
- PDF 生成: `app/pdf/{pdf_fill.py, layout_utils.py, beppyou_02.py, uchiwakesyo_*.py, date_jp.py, fonts.py, geom.py}`
- 会社ドメイン: `app/company/*`
  - モデル/フォーム: `models.py`, `forms.py`, `utils.py`
  - サービス: `services/{auth_service, shareholder_service, master_data_service, financial_statement_service, company_classification_service, import_consistency_service, company_service, declaration_service, statement_of_accounts_service, data_mapping_service, soa_summary_service}.py`
  - 帳票/集計: `statement_of_accounts.py`, `financial_statements.py`, `soa_config.py`, `soa_mappings.py`
  - インポート: `import_data.py`, `parser_factory.py`, `parsers/{base_parser, yayoi_parser, moneyforward_parser, freee_parser, other_parser}.py`
  - その他: `core.py`, `shareholders.py`, `offices.py`, `auth.py`

## エントリ/設定
- `run.py`: アプリ起動エントリ
- `config.py`: 設定
- `pyproject.toml` / `requirements.txt`: 依存管理
- `.github/workflows/quality.yml`: CI 品質チェック

## テスト/CI
- 単体: `tests/test_*.py`（SOA, 幾何検証, テナント, サマリ等）
- E2E: `tests/e2e/*.spec.ts`（ログイン, ハッピーパス, 状態遷移, 破損アップロード等）
- Playwright: `playwright.config.ts`, `tsconfig.json`, `package.json`

## リソース
- フォーム PDF: `resources/pdf_forms/.../2025/source.pdf`
- 幾何/テンプレ: `resources/pdf_templates/.../*.json`
- マスタ: `resources/masters/{balance_sheet.csv, profit_and_loss.csv}`
- フォント: `resources/fonts/NotoSansJP-*.ttf`

## 次アクション候補
- `run.py` と `app/__init__.py` の起動・Blueprint 構成精査
- サービス間依存関係の可視化
- PDF 出力フロー（入力→マッピング→描画）のデータフロー整理
- 任意モジュールの関数/クラス一覧（シンボル索引）


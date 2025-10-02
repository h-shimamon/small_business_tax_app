# 日付カラム統一マイグレーション仕様（ドラフト）

## フェーズ構成

1. **フェーズA: 命名整理・Date優先化**
   - 目的: Date 列を正式名称へリネームし、旧 String 列/プロパティは互換層に退避。
   - Alembic Revision 例: `20250901_rename_date_columns.py`

2. **フェーズB: 旧要素の削除**
   - 目的: 互換期間後、不要になった旧 String 列やビューを削除。
   - Alembic Revision 例: `20251001_drop_legacy_date_strings.py`

---

## フェーズA 詳細

### 対象テーブル

- `company`
  - `accounting_period_start_date` → `accounting_period_start`
  - `accounting_period_end_date` → `accounting_period_end`
  - `closing_date_date` → `closing_date`

- `notes_receivable`
  - `issue_date_date` → `issue_date`
  - `due_date_date` → `due_date`
  - 既存 String 列は `*_legacy` にリネームして一定期間保持

### 作業内容

1. Alembic で以下を実施
   - `company`: rename column (`batch_alter_table`) と NOT NULL/DEFAULT は現行維持。
   - `notes_receivable`: Date 列をリネーム、String 列を `issue_date_legacy` 等へリネーム。

2. データ移行
   - `notes_receivable`: 新しい Date 列が NULL の場合、旧 String から `fromisoformat` でバックフィル。
   - バックフィル後、String 列は読み取り専用として残存。

3. アプリ改修範囲
   - モデル: Date 列の参照名変更、互換プロパティ追加。
   - フォーム/seed/PDF/CLI: Date 列を直接利用するようリネーム。
   - テスト: 既存ケース更新、日付項目が Date オブジェクトで維持されることを保証。

4. 互換措置
   - API/内部呼び出しで文字列名を期待する箇所にはプロパティでフォールバック（例: `@property def issue_date_string`）。
   - `scripts/generate_soa_config.py` などが文字列名を期待しないか確認。

### エラーハンドリング

- マイグレーションで不正な日付文字列が見つかった場合は `SAWarning` ログを出して `NULL` にする（要ログ出力）。

---

## フェーズB 詳細

### 対象

- `notes_receivable.issue_date_legacy`
- `notes_receivable.due_date_legacy`
- 互換プロパティ/ビュー

### 作業内容

1. 事前条件
   - アプリ側で旧プロパティ参照が完全に排除されていること。
   - 本番データの健全性チェック（`COALESCE(issue_date, issue_date_legacy)` 全件一致）。

2. Alembic 処理
   - 旧 String 列を削除。
   - 互換ビューやトリガーがあれば同時に撤去。

3. 検証
   - `pytest tests/test_statement_of_accounts_service_defaults.py`
   - `flask report-date-health --format json` で String 列依存がないことを確認。

---

## ロールバック指針

- フェーズAで問題が発生した場合
  - Alembic downgrade で旧カラム名に戻す。
  - バックフィル済み Date データは残るため、再適用で復旧可能。

- フェーズBで問題が発生した場合
  - 旧 String 列削除を取り消すためのバックアップ（`ALTER TABLE ADD COLUMN ...` + 再インポート）が必要。
  - フェーズBの適用前に DB バックアップを取得推奨。

---

## タイムライン案

- スプリント1: フェーズA マイグレーション + アプリ差分 + テスト
- 社内環境で検証完了後、スプリント2でフェーズB適用

---

レビュー後、具体的な Alembic スクリプトとコード改修のタスクリストを作成します。

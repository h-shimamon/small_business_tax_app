# 日付カラム統一事前メモ

## 1. 対象テーブルとカラム

- `company`
  - `accounting_period_start_date` (Date)
  - `accounting_period_end_date` (Date)
  - `closing_date_date` (Date)
  - 旧文字列プロパティ: `accounting_period_start`, `accounting_period_end`, `closing_date` （プロパティ経由でISO文字列を返す）

- `notes_receivable`
  - `issue_date` (String(10), nullable=False)
  - `issue_date_date` (Date)
  - `due_date` (String(10), nullable=False)
  - `due_date_date` (Date)

## 2. 参照コードと依存モジュール

- UI/フォーム
  - `app/company/forms/declaration.py`: 日付入力フィールドでISO文字列を扱い、内部的には Date 型へ正規化。
  - `app/company/forms/soa/metadata.py`: SoA フォームメタデータで `issue_date`/`due_date` を指定。

- サービス/ユーティリティ
  - `app/models_utils/date_readers.py`: `company_accounting_period_start` など、まず Date 列を参照しなければ String を `ensure_date` で変換。
  - `app/models_utils/date_sync.py`: `attach_date_string_sync` で String ↔ Date を同期。
  - `scripts/seed_notes_direct.py`, `app/commands.py`: 両カラムを利用してデータ投入や診断を実施。

- PDF/帳票
  - `app/pdf/uchiwakesyo_uketoritegata.py`: `getattr(..., 'issue_date_date', ...)` で Date 先行。

## 3. 既存マイグレーション履歴

- `migrations/versions/f123456789ab_phase1_schema_cleanup.py`: 旧文字列カラムから Date カラムへバックフィルし、旧列を削除。
- `migrations/versions/0b1e4d5c6f70_office_city_and_notes_date_cleanup.py`: `notes_receivable` の String 列を削除し Date 列にリネームする案（未適用状態）。

## 4. 課題ポイント

1. `company` では旧文字列列自体は既に削除済みだが、カラム名に `_date` が二重に残っている（例: `closing_date_date`）。
2. `notes_receivable` は String 列と Date 列の二重管理が続いており、フォームやシードが両方を参照。
3. PDF や CLI で Date 列が無い場合に String 列へフォールバックしており、先に Date 列の存在保証が必要。

## 5. 今後の設計方針（要レビュー）

1. 命名整理フェーズ
   - `company` の Date 列を `closing_date` など単純な名前へリネーム。
   - `notes_receivable` の Date 列を正式列とし、String 列は互換プロパティ化またはビュー提供。

2. バックフィルと互換期間
   - Alembic マイグレーションで既存値を Date 列へ `COALESCE(parse(legacy), new)` で移行。
   - マイグレーション適用後、コードは Date 列のみ参照するよう更新。

3. 旧列削除フェーズ
   - 移行完了とテスト検証後、不要になった String 列を削除。

---

このメモは設計レビュー用ドラフトです。問題なければマイグレーション仕様書案を続けて作成します。

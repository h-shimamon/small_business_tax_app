# 日付カラム統一 フェーズB計画（旧 legacy 列削除）

## 1. 適用前提
- フェーズA（`a54c3d2e1f98`）が適用済みで、`company`/`notes_receivable` の Date カラムが新命名へ統一されている。
- アプリコードが `issue_date_legacy` / `due_date_legacy` を参照していない（フォールバック用途を除く）。
- `flask report-date-health --format json` で legacy 列と Date 列の差異が 0 であること。
- 本番 DB のバックアップ（Dump）取得済み。

## 2. 手順概要
1. **整合チェック**
   - `flask report-date-health --format json` を本番とステージングで実行し、`str_only` と `mismatch` が 0 であることを確認。
   - 受取手形 UI/PDF/CSV を実データでスポットチェック。

2. **マイグレーション適用（フェーズB）**
   - Alembic Revision 例: `b74d1c3e0abc_drop_legacy_date_columns.py`。
   - 内容: `notes_receivable.issue_date_legacy` / `due_date_legacy` の削除、`company_closing_date` 等 legacy プロパティのクリーンアップ。
   - SQLite の場合は `batch_alter_table` で一時テーブルが残らないよう注意。

3. **テストとバリデーション**
   - `pytest tests/test_statement_of_accounts_service_defaults.py`。
   - `flask report-date-health --format json`（削除後、legacy 指標が 0 で動作すること）。

4. **リリース後フォロー**
   - 特定期間（1〜2週間）で受取手形関連のユーザー問合せ監視。

## 3. スケジュール案
- スプリントX: フェーズBマイグレーション実装 → ステージング適用 → QA。
- スプリントX+1: 本番適用 → 監視 → レビュー完了。

## 4. リスクと緩和策
- **不整合データが見つかった場合**: マイグレーションを保留し、該当レコードを CSV へ抽出 → 手動修正後に再計画。
- **PDF/帳票への影響**: フォールバックが無くなるため、社内で数パターンを事前印刷確認。

---

レビュー後、具体的なフェーズBスクリプトとチェックリストを作成します。

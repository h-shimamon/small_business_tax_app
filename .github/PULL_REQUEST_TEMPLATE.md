## 目的（何を達成する？）
- 例：内部の読み取りのみを共通プリミティブへ寄せ、UI/外部I/Fは不変

## 変更概要（要点）
- 例：navigation/import_data/core/beppyou_02 を primitives 経由に置換（最小差分）

## エビデンス（壊していない証拠）
- [ ] `flask report-date-health --format json` の結果を貼付（mismatch=0）
- [ ] UI差分なし（スクショ/テキスト比較など、必要時のみ）
- [ ] 主要フローのSmoke確認（必要時のみ）

## 影響範囲・リスク
- 例：内部読取のみ。警告/リダイレクト/出力フォーマットは従来どおり

## ロールバック方法（1行）
- 例：`git revert <このPRのマージコミット>`

---

### チェックリスト（DoD）
- [ ] **primitives**（`app/primitives/*`）を使用（直 `strptime(` なし）
- [ ] 健全性レポの結果を添付（`mismatch=0`）
- [ ] **1テーマ=1PR**（スキーマ変更とUI変更は混在させない）

# CSP Inline Audit（現状棚卸し）

目的: `unsafe-inline` を外しやすくするため、残存する inline `<style>` / `style="..."` を棚卸し。

## 残存箇所（確認日: 現在）
- app/templates/base.html
  - `<style>` ブロック: flatpickrの年セレクト微調整（`.flatpickr-current-month .dp-year-select {...}`）
  - 対応案: components CSSへ移管（影響軽微）
- app/templates/company/filings/business_overview_1.html
  - `style="text-align:center;"`（合計セルの表示）
  - 対応案: `.text-center` 等のユーティリティクラスに差し替え

## 既に外部化済み
- 日付初期化の inline `<script>` は外部JSへ移管済み（`app/static/js/date_picker_init.js`）
- プレビュー枠の iframe スタイルはCSSへ移管済み

## 推奨ポリシー（将来）
- `Content-Security-Policy:
  script-src 'self' https://cdn.jsdelivr.net;
  style-src 'self';
  object-src 'none'; base-uri 'self'`
  - 注: 上記を適用する前に、base.html の `<style>` とテンプレの `style="..."` を完全撤去する必要あり

## 次手順（段階）
1) base.html の `<style>` を components CSS へ移管
2) BO1 の `style="text-align:center;"` をユーティリティクラスへ置換
3) grep で残存 inline を確認し、0件を確認
4) ステージングで CSP適用→Lighthouse/コンソール警告が無いことを確認

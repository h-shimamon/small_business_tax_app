# HANDOVER 2025-09-06 (SERENA V18)

目的: 事業概況説明書1（以下「事業概況①」）の専用UIを新設し、既存フォームの初期フォーカス/placeholder整備、ナビに「申告書」セクションを追加。PDFプレビュー連携の雛形を実装。以降の作業者が、最小差分・2カラム不変・フォント不変更を厳守して安全に継続できるようにする。

---

## 1. 現状サマリ（本番に影響なし）
- 事業概況①の画面は「保存なしの入力UI」として稼働。右ペインでPDFプレビューを表示（iframe、ツールバー/サムネイル非表示）。
- 左ペインは fieldset を2つに分割:
  1) 支店の状況
     - 行1: 国内支店（総数）｜右=空欄
     - 行2: 海外支店（総数）｜右=空欄
     - 行3: 海外支店の所在地国1｜所在地国1の従業員数
     - 行4: 海外支店の所在地国2｜所在地国2の従業員数
  2) 子会社の状況
     - 行1: 国内子会社の数｜海外子会社の数
     - 行2: うち出資割合が50%以上の海外子会社（数）｜右=空欄
     - 行3: 子会社の名（1）｜出資割合（1）
     - 行4: 子会社の名（2）｜出資割合（2）
- フォントは共通の .form-label/.form-control を使用（ページCSSでフォント変更なし）。
- 申告書ナビをサイドバー/グローバルナビに導入（別表2/16(2)は除外）。グローバルナビ「申告書データ」→ beppyo_15 に遷移。

---

## 2. 重要なUI/実装ルール（厳守）
- 変則2カラム固定: ページ専用CSS（.bo-grid）で column-gap=24px, row-gap=0。縦の行間は .form-group の 1.5rem のみ。
- 右欄空欄の保持: 右列を空にする行には必ず `<div class="bo-empty">` を置く（CSSで grid-column: 2）。
- 行頭固定: 次の行を左列から開始するときは `<div class="form-group bo-col-1">` を用いて grid-column:1 を明示。
- fieldset間の間隔: 本ページ限定で `.bo-pane-left form > fieldset + fieldset { margin-top: 1.5rem !important; }`。
- フォント: ページCSSで font-family/font-synthesis を追加しない（共通スタイルのまま）。
- 最小差分: 広域正規表現置換を禁止。1箇所ずつピンポイント編集→動作確認の順で。

---

## 3. ルーティング/プレビュー
追記(2025-09-14): 下記の通り仕様を更新しました。
- 画面: `GET /filings?page=<page>` → 登録表(REGISTRY)からタイトル/テンプレートを解決。`business_overview_1` は専用テンプレ登録済み。未登録は共通テンプレにフォールバック。
- プレビュー: `GET /filings/preview?page=<page>` → 登録表の `preview_pdf` を相対パスで解決。未登録は404。`business_overview_1` は `resources/pdf_forms/jigyogaikyo/2025/source.pdf`。
- 実装: `app/company/filings_registry.py` を追加し、`app/company/filings.py` は同登録表を参照（UI変更なし）。

- 画面: `GET /filings?page=business_overview_1`
  - business_overview_1 のみ専用テンプレを返す。それ以外は仮置きの一覧テンプレを使う。
- PDFプレビュー: `GET /filings/preview?page=business_overview_1`
  - `resources/pdf_forms/jigyogaikyo/2025/source.pdf` を `send_file` で返す。
  - iframe には `#toolbar=0&navpanes=0&view=FitH` を付与してツールバー/サムネイル抑制。

---

## 4. 変更ファイル一覧
追記(2025-09-14): 以下を最小差分で更新/追加しました（UI変更なし）。
- 更新: `app/company/filings.py`（登録表参照化、PDFパス基準を `current_app.root_path/..` に統一）
- 追加: `app/company/filings_registry.py`（タイトル/テンプレ/プレビューの単一情報源）
- 更新: `app/templates/company/filings/business_overview_1.html`（インラインJS撤去、外部JS読込に置換）
- 追加: `app/static/js/pages/filings_business_overview.js`（従来の挙動を外部化、`defer` 読込）
- 更新: `app/static/css/pages/filings_business_overview.css`（重複/相反指定を統合。見た目同等）

新規
- app/company/filings.py（ルート: `/filings`, `/filings/preview`）
- app/templates/company/filings/business_overview_1.html（事業概況①専用画面）
- app/static/css/pages/filings_business_overview.css（事業概況①ページ専用CSS）

更新
- app/navigation_builder.py（申告書セクション追加/並び順調整/別表2,16(2)除外）
- app/templates/base.html（グローバルナビ「申告書データ」→ filings beppyo_15）
- app/static/css/components/forms.css（`.form-grid-2col` 行間統一、`.form-grid-2-col` 吸収）
- SoAフォーム各テンプレート（初期フォーカス・placeholder・預貯金の摘要幅）
  - deposit_form.html / notes_receivable_form.html / accounts_receivable_form.html
  - temporary_payment_form.html / loans_receivable_form.html / notes_payable_form.html
  - accounts_payable_form.html / temporary_receipts_form.html / borrowings_form.html
  - executive_compensations_form.html / land_rents_form.html

---

## 5. 既知の課題 / 推奨修正
1) PDFプレビューのパス固定
- 現状: 絶対パス。環境非依存化が必要。
- 推奨: `base_dir = os.path.join(current_app.root_path, '..', 'resources', 'pdf_forms', 'jigyogaikyo', '2025')` で相対組立。例外時は 404。

2) 申告書の他ページ（別表群・概況②/③など）
- まだ仮置き表示。各ページのテンプレ/入力項目の仕様化が必要。

3) レイアウト保守
- 右空欄/列開始を崩しやすい。`bo-empty`/`bo-col-1` を削除・移動しないこと。

4) 作業手順
- 以前、広域regex置換により `$1` や `\"` などのゴミが混入しテンプレが破損した。以後は **1差分ずつ** の編集のみ。

---

## 6. 次の具体的タスク（安全順）
A. 事業概況①（この画面）
- ラベル最終確認（依頼者指示どおりか）：国内/海外支店、所在地国1/2、従業員数の文言。
- プレビューの環境非依存化（上記3行の修正）。
- 軽微QA: fieldset間1.5rem、行間1.5rem、1行目右=空、2行目右=空の維持。

B. 申告書ナビ/デフォルト
- `filings()` のデフォルト page を beppyo_15 に合わせる（必要なら）。

C. 事業概況②/③
- 本ページ構成を踏襲（専用テンプレ＋右プレビュー）し、段階的に実装。

---

## 7. 確認チェックリスト（作業前/後）
- [ ] 変更は1箇所のみか（最小差分）
- [ ] `.bo-grid row-gap` は 0 のままか
- [ ] 右空欄行に `.bo-empty` があるか
- [ ] 左列開始が必要な行は `.bo-col-1` を付けているか
- [ ] fieldset間の余白が 1.5rem あるか
- [ ] フォント関連のCSSを **追加していない** か

---

## 8. コミット（未実施。参考メッセージ）
```
feat(filings): 事業概況① UI + PDFプレビュー追加、申告書ナビ導入
fix(ui): 行間統一（row-gap=0/1.5rem）、SoAフォームの初期フォーカス/placeholder整備、預貯金の摘要幅調整
```

---

## 9. 参考: 画面ファイル抜粋
- business_overview_1.html のレイアウト要（編集時に確認）
  - bo-empty: 右列空欄用ダミーセル
  - bo-col-1: 次行左列開始強制
  - fieldset + fieldset の余白: 1.5rem（ページ限定CSS）

---

## 10. 反省/再発防止
- 広域置換によるテンプレ破壊を発生させた。以後、**ID/クラス指定のピンポイント編集**のみに限定し、毎回表示確認を行う。
- フォント差はCSSではなく壊れたDOMが原因だった事例あり。まず DOM/Computed Styles で事実確認→必要最小の変更のみ。

以上。以後の作業も「最小差分・2カラム不変・フォント不変更」を厳守してください。

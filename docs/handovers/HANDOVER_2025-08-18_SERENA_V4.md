# 開発引き継ぎメモ（SERENA V4）

日付: 2025-08-18  
対象: small_business_tax_app（Flask）  
スコープ: 別表二（beppyou_02）PDF印字の本番運用化・座標基準の中心化・上位3グルー
プ制御・株主住所チェックUX修正

—  
**概要**
- 目的: 官公庁様式の印字を安定化（座標の上下中央基準・年更新に強い設計）し、株主
/社員情報画面からブラウザ表示で即印字できるようにする。
- 方針: 既存UI/テンプレ/クラス名は不変。印字はユーティリティ＋サービス層で完結。
年版差異はテンプレ/リソースに集約。

**本日の成果（要点）**
- 別表二 beppyou_02 の生成器を新設し、行ごとの上下中央揃えに切替（微調整不要の安
定配置）。
- 行センター値を定数化: 行1=387.0pt、以降は−24.5pt間隔で配置（1:387.0、2:362.5、
3:338.0…）。
- 住所欄は1/2行ブロック高さを計算し中央配置（同上1行にも対応、住所フォントは8pt→
最小7pt）。
- 上位3グループ制限を有効化（議決権/出資金の合計で降順ソート）。
- 株主/社員情報画面に「PDF出力（別表二）」ボタンを最小追加（新規タブでブラウザ表
示→印刷）。
- 特殊関係人編集のUX改善: 主たる株主と住所が一致していれば編集画面でチェック初期
ON、保存時チェックONなら住所コピー→印字は「同上」。

—  
**変更ファイル一覧（抜粋）**
- 追加
  - `app/pdf/pdf_fill.py`: PDFオーバーレイ基盤（pypdf+reportlab、アンカー解決はP
yMuPDF対応）
  - `app/pdf/beppyou_02.py`: 別表二の印字ロジック（上下中央揃え、上位3グループ、
住所「同上」、座標定数）
  - `resources/pdf_templates/beppyou_02/2025.json`: テンプレ雛形（フォント/差し
込み例）
  - `resources/pdf_forms/beppyou_02/README.md`, `resources/pdf_forms/beppyou_02/
2025/.gitkeep`
- 変更
  - `app/company/shareholders.py`: PDF出力ルート追加（`/shareholders/pdf/beppyou
_02`）、編集画面での住所一致チェック初期ON、出力先パスを絶対化
  - `app/templates/company/shareholder_list.html`: 「PDF出力（別表二）」ボタンを
最小追加（target=_blank）
  - `app/company/services/shareholder_service.py`: 
    - `update_shareholder`: 編集時チェックONで住所コピーを反映
    - 集計ユーティリティ（会社合計/グループ合計/マップ）
  - `app/pdf/beppyou_02.py`: 行センター方式、絶対パス参照、上位3グループ制御、住
所・氏名・関係・株数の中央揃え
  - `requirements.txt`: `pypdf`, `reportlab`, `cryptography>=3.1`, `PyMuPDF` を
追加
- リソース命名整理
  - 旧 `houjin_beppyou_2` → 新 `beppyou_02` へ移行
  - 旧 `02` 配下テンプレ整理（必要PDFは `resources/pdf_forms/beppyou_02/<year>/s
ource.pdf` へ）

—  
**実装詳細（別表二 beppyou_02）**
- 行センター方式
  - `ROW1_CENTER = 387.0`、`ROW_STEP = 24.5` とし、行nのセンターは `387.0 - 24.5
*(n-1)`。
  - 単行項目（番号/氏名/関係/株数）は `center_y - font_size/2` でベースライン決
定。
  - 住所は行数（1/2）と実フォントサイズ（8→7pt）＋行間2ptからブロック高さを算出
し中央配置。
- 住所「同上」ロジック
  - 特殊関係人が主たる株主と住所完全一致なら1行目に「同上」、2行目は空。
  - 保存時チェックON→住所コピー→一致→印字は「同上」。チェックフラグのDB保存は行
わず、住所一致を根拠とする（影響最小）。
- 上位3グループ制限
  - `shareholder_service.compute_group_totals_map(company_id)` を利用し、グルー
プ合計（株式会社/有限会社→議決権、持分会社→出資金）で降順ソート→上位3グループの
み印字対象。
- 座標・フォント
  - 住所フォント: 開始 8pt、最小 7pt。はみ出す場合は省略記号…。
  - 住所行間: 2pt（2行時）。
- パス解決
  - `app/pdf/beppyou_02.py` は `app/pdf/` からプロジェクトルートを解決し、`resou
rces` や `fonts` のパスを絶対で参照。

—  
**動作確認手順**
1) 依存導入: `pip install -r requirements.txt`
2) リソース配置:
   - 元PDF: `resources/pdf_forms/beppyou_02/2025/source.pdf`
   - フォント: `resources/fonts/NotoSansJP-Regular.ttf`
3) 画面から実行:
   - 株主/社員情報 → 「PDF出力（別表二）」 → 新規タブでPDF表示（ブラウザ印刷可）
4) REPL（任意）:
   - `from app.pdf.beppyou_02 import generate_beppyou_02`
   - `generate_beppyou_02(company_id=<ID>, year='2025', output_path='temporary/f
illed/beppyou_02_test.pdf')`

—  
**既知の注意点/修正候補**
- アンカー解決（PyMuPDF）をテンプレ側で使う場合、年度でラベル表記が微妙に変わる
と一致率に影響。年版テンプレの`anchor.text`を安定した文言で定義推奨。
- 住所の超長文で2行でも収まらない場合、…省略位置は末尾固定。要件に応じて中間省略
等に拡張可。
- `ROW1_CENTER`/`ROW_STEP` は現在コード内定数。年版差異が頻出するならテンプレJSO
N側へ移すと運用が軽くなる（次の改善候補）。
- 別表二の列追加/他項目（例: 関係コードや備考等）が必要なら、同じセンター方式の
計算枠を拡張して対応。

—  
**次スレのTODO（明日の作業）**
1) 別表二（beppyou_02）の印字続き
- 対象: 残り項目の差し込み（もし未印字欄があれば）、列ごとの微調整（±0.5〜1pt単
位）
- 方針: センター方式維持。行間（住所2pt）やフォント（住所7〜8pt, 他10pt）で吸収
- テンプレ化: 将来的に `ROW1_CENTER/ROW_STEP` をテンプレに移して年版差異を外出し

2) 持分会社の確認/対応
- 判定: 現在は会社名の文字列（合同/合名/合資）でmetricを `investment_amount` に
切替。会社種別の型を別途持つならそこに切替検討
- 表示/印字: UIの文言は変更不可。必要ならバックエンドのみで出資金と議決権の扱い
を分岐

3) UI修正（最小差分）
- ルートやボタンのラベルはそのまま。必要に応じて PDF 表示の文言や year パラメー
タの自動化（会計期間からの導出）を検討（影響範囲が広い場合は先に提案）

—  
**参考**
- 既存引き継ぎ: `docs/handovers/HANDOVER_2025-08-17_SERENA_V3.md`
- 指令書: `開発指令書.txt`（UIの原則、CSS配置、原則A〜D）

以上。座標はセンター基準で安定化済み、上位3グループも有効化しました。明日は「別
表2の印字の続き」と「持分会社の対応」、そして「UI（IU）修正の最小差分」に進んで
ください。

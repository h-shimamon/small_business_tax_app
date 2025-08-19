— 引継書（SERENA V5）—

開発引き継ぎメモ（SERENA V5）
日付: 2025-08-19
対象: small_business_tax_app（Flask）
スコープ: 株主カードの整列最適化（Apple原則に基づく余白補正）/ PDF（別表二 beppy
ou_02）ヘッダ指標と会計期間（和暦）出力の高度化（分割・座標厳密化）/ ヘッダーア
クション配置・表示制御

概要
- 目的:
  - 株主/社員情報（カード表示）の視覚重心と整列を維持しつつ、余白の“質”を高める
（Appleならどう作るか）。
  - 別表二PDFのヘッダ領域に、株式合計/上位3合計/割合の安定表示を導入し、会社区分
に応じた枠描画と、会計期間（開始/終了）の和暦を厳密な座標・基準線（ベースライン
）で出力可能にする。
- 方針: UIの構造・既存クラス・テンプレ骨格は不変。ページ限定CSSと最小JSで揃え・
余白を調整。PDFはユーティリティ＋サービス層で完結。

今回の成果（要点）
1) 株主/社員情報（カード）の整列と余白の最適化（UI構造不変）
- 主たる株主サマリーを二行（1行目=関係人を含む総数／2行目=本人）でレイアウト、主
と特殊関係人の「株式数/議決権」の文字頭を一致。
- 3カラムGrid（情報|サマリー|アクション）を維持しつつ、リズムを整備:
  - 中列の最小幅（minmax）維持と、ラベル幅の共有で行内整列を安定化。
  - サマリー左にpadding-left、アクションのmargin-left最適化（視覚重心の中央化）
。
  - 編集/削除アイコン位置の復元・安定化。
- PDF出力ボタンをヘッダ右の「セカンダリ」ボタンとして近接配置（新規グループ登録
の直下）。
- PDF出力ボタンは主たる株主が1件以上ある場合のみ表示（条件付き描画）。

2) 別表二 beppyou_02 のヘッダ指標の追加
- 指定矩形に以下を右寄せ・上下中央で描画（NotoSansJPで統一）:
  - （1）全株主の保有株式数合計（“株”付）
  - （2）上位3グループの合計（“株”付）
  - （3）(2)/(1)の割合（%なし）
  - （4）(3)に%を付与
- 4項目のX位置は共通右端に揃えてぶれを解消。
- 区分枠（同族/非同族）を指定矩形に枠線のみ描画。

3) 会計期間（和暦）出力の高度化（開始/終了）
- 和暦変換（令和/平成/昭和）＋2桁（YY,MM,DD）生成を追加。
- 会計期間「開始」
  - 年号（6pt, 左寄せ）/ YY・MM・DD（9pt, 右寄せ）を個別座標に描画。
  - ベースライン（下揃え）はDDのY座標を基準に統一。
  - DDのXは基準からさらに−10pt補正（ユーザ指示どおり）。
- 会計期間「終了」
  - X座標は「開始」と同一、ベースラインは「終了DD」のY座標を基準に統一。
  - 同様に年号=6pt、YY/MM/DD=9ptで描画、DDのXは開始と同様に−10pt補正。
- 「矩形幅は重要ではない」要件に合わせ、フィット/省略（…）は無効化し、位置優先で
描画。

主な変更ファイル
- 追加/更新（PDF基盤）
  - app/pdf/pdf_fill.py:
    - overlay_pdf(..., rectangles=...) 追加（枠線描画に対応）。
  - app/pdf/beppyou_02.py:
    - ヘッダ指標（(1)〜(4)）の描画・右端揃え、枠描画（(5)(6)）。
    - 和暦変換（年号抽出/2桁変換）、開始/終了の分割描画（ERA, YY, MM, DD）を実装
。
    - 位置優先描画ヘルパー（_place_at_left, _place_at_right）と中央寄せ版（_plac
e_center_left_fit, _place_center_right_fit）を整備。
    - フォントを NotoSansJP に統一。
- 追加/更新（UIページ）
  - app/templates/company/shareholder_list.html:
    - サマリー二行化（主=合計/本人）、グループ合計表示の追加（サービスから受け取
り）。
    - PDF出力ボタンをヘッダ内「セカンダリ」ボタンとして表示（secondary_first=Tru
eで順序制御）。
    - PDFボタンを主たる株主が無いとき非表示（条件付き）。
  - app/templates/company/_layout_helpers.html:
    - ヘッダマクロにsecondary_href/secondary_text/secondary_firstを追加（既存画
面への影響なし）。
  - app/company/shareholders.py:
    - テンプレへgroup_totals_both_mapを供給。
  - app/company/services/shareholder_service.py:
    - compute_group_totals_both_map(company_id) 追加（主グループごとの総株式数/
総議決権を一括算出）。
- ページ限定CSS（位置・余白の最適化）
  - app/static/css/pages/shareholder_list.css:
    - .accordion-header, .related-row（3カラムGrid）: 列幅/列間の整備（中列minma
x維持）。
    - .accordion-summary, .related-summary: 左に少量のpadding-left（“ひと呼吸”の
余白）。
    - .accordion-actions, .related-actions: margin-leftを抑制し、サマリー→アイコ
ンの距離を最適化。

更新されたファイル一覧（今回セッション）
- app/pdf/pdf_fill.py
- app/pdf/beppyou_02.py
- app/templates/company/shareholder_list.html
- app/templates/company/_layout_helpers.html
- app/company/shareholders.py
- app/company/services/shareholder_service.py
- app/static/css/pages/shareholder_list.css

実装詳細（抜粋）
- PDF（beppyou_02）
  - ヘッダ数値の右端共通化: 4つの矩形の右端を算出し、最小の右端に合わせて右寄せ
描画。
  - 分類枠: rectangles パラメータで枠線のみ描画（pypdf+reportlab）。
  - 和暦:
    - _wareki_era_name（年号）、_wareki_numeric_parts（yy,mm,dd 2桁）
    - 「開始」「終了」それぞれ、ERA(6pt, 左), YY/MM/DD(9pt, 右)を個別座標で描画
。
    - ベースラインはDDのyを共有（下揃え統一）。
    - 「開始DD」はXを−10pt補正（ユーザ指定）。
  - 省略記号防止: フィット/省略を無効化し、位置優先描画ヘルパーで表示（箱幅無視
要件）。
- 株主/社員情報ページ（Apple原則の反映）
  - サマリー二行とラベル幅の共有により、主と特殊関係人で文字頭を完全一致。
  - 視覚重心を中央寄りにするため、左右余白を再配分（列間の等間隔＋要素内余白）。
  - アクションを詰めてサマリーとの距離を最適化。
  - PDF出力ボタンをヘッダアクションに内包（近接配置・整列の美観）

既知の注意点 / 次の改善候補
- CSSの微細な重複: .accordion-summary, .related-summary に padding-left の重複指
定が残っている可能性あり。実効値は後出が優先。値の一本化で意図の明確化可（スタイ
ルの“事実の一本化”）。
- JS computeDimensions はカード単位で幅を計測しCSS変数に設定。将来的に測定回数の
削減やリサイズ頻度の最適化（ResizeObserver 化）が有効。
- PDFテンプレ外出し: 行センター/オフセット・矩形座標をJSON化してテンプレ管理へ移
管すると、年度差分や将来調整が容易。
- フォント設定の一元化: PDF内のサイズ・フォント名をマクロ化して統制（サイズ指定
の表出を減らす）。
- 「終了」側のDD X補正は開始に合わせ−10ptで実装済み。将来、ユーザ調整オプション
化（引数や設定）も可。

動作確認手順（要点）
1) UI
- 株主/社員情報ページで、主/特殊関係人のサマリーが2行になり、各カードで「株式数/
議決権」の文字頭が揃っていること。
- PDF出力（別表二）ボタンがヘッダ右で「新規グループ登録」の直下に近接配置、主た
る株主が0件のとき非表示。

2) PDF（別表二）
- ヘッダ4数値が右端の共通ラインで綺麗に揃うこと（“株”や%の文字化けなし）。
- 区分枠（同族/非同族）の枠線が該当位置に描画されること。
- 会計期間（開始/終了）の年号・YY・MM・DDが指定座標に描画され、ベースライン（DD
のy）で下揃え統一になっていること。開始DDはXが−10pt補正。

参考
- 既存引き継ぎ: docs/handovers/HANDOVER_2025-08-18_SERENA_V4.md
- 指令書: 開発指令書.txt（UI原則、CSS配置、原則A〜D）

以上。UIは構造不変のまま視覚重心と整列を最適化。PDFはヘッダ数値と会計期間を正確
に配置できるよう拡張済みです。次はCSSの重複指定整理と、PDFテンプレ外出しによる年
度差分対応の検討を推奨します。

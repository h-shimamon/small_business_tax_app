# UIスタンダード（最小差分・段階導入）

本ドキュメントは、アプリ全体の UI を統一し、保守性と開発速度を高めるための実装規約です。既存画面を壊さない「opt-in（任意適用）」を基本に、段階的に導入します。

---

## 1. デザイントークン（foundation/tokens.css）
- 高さ/行間/余白の基準値を CSS 変数で定義
- 既に base.html から読み込み済み（UIへの直接影響はなし）

定義例:
- `--control-height: 44px`（入力/ラジオ/チェックの標準高さ）
- `--control-padding-y: 11px`, `--control-line-height: 1.25`
- `--row-gap-tight: .5rem`, `--row-gap-base: 1.5rem`
- `--legend-mb: .75rem`（fieldset 見出し下の余白）

原則:
- 数値はトークンを使用（独自数値の直書きは禁止、やむを得ない場合はコメントで理由を明記）

---

## 2. 標準クラス（components/forms.css）
- 全体適用: `<main class="main-content ui-ctrl-44">` を base.html に付与済み（全画面 44px の高さに統一）
- 個別適用（opt-in）: 必要に応じて以下を併用
  - `form-control--std`: 単一入力の標準化（高さ/パディング）
  - `segmented--std`: segmented control の標準化（ラジオ/チェック）
  - `legend--std`: fieldset 見出しの下余白を標準化
- 全画面統一: `fieldset > legend { margin-bottom: var(--legend-mb); }` を追加済み

---

## 3. 標準マクロ（templates/ui/_form_macros.html）
- 中立的なフォームマクロ。既存ページ固有マクロと併用可能
- `std=True` でトークン準拠（高さ/余白）を opt-in

使用例:
```
{% import 'ui/_form_macros.html' as ui %}

{% call ui.grid(2) %}
  {{ ui.field('名称', type='text', placeholder='例：〇〇', name='example.name', std=True) }}
  {{ ui.select('区分', [('a','A'),('b','B')], name='example.type', std=True) }}
{% endcall %}

{{ ui.segmented('種別', 'example.kind', 'radio', options=[('yes','有'),('no','無')], span_all=True, std=True) }}
```

---

## 4. 共通JS（static/js/ui/*.js）
- base.html で defer 読込済み（自動実行なし）
- ページ側は必要に応じて関数を呼び出すだけ

関数一覧:
- segmented（チェックボックス系）
  - `UI.segmented.syncCheckboxLabelStateByName(name)`
  - `UI.segmented.enableLabelToggleByForPrefix(prefix)`
- radios（ラジオ再クリックで解除）
  - `UI.radiosToggle.enableUncheckOnReclickByName(name)`
- totalizer（数値合計）
  - `UI.totalizer.bind({ container: '.js-workers-count', source: 'input[type="number"]', target: '.js-total' })`
- sticky aside（右ペイン固定）
  - `UI.stickyAside.bind({ split: '.bo-split-pane', aside: '.bo-pane-right', left: '.bo-pane-left', leftCard: '.bo-pane-left .card', gapTop: 16, gapRight: 24 })`

---

## 5. ページ適用の手順（推奨）
1) マークアップは変更せず、まず見出し余白/高さの統一を確認（base.html の一括適用で反映済み）
2) ラジオ/チェック: `ui.segmented(..., std=True)`（または既存マクロに `segmented--std` を付与）
3) 入力: ラジオと横並びになる入力に `form-control--std` を優先適用
4) 行間: grid の row-gap は `.5rem`（tight）か `1.5rem`（base）を使用
5) JS: 既存ページのインラインJSは共通JSの呼び出しに置換（挙動は同一）

---

## 6. チェックリスト
- [ ] 入力/ラジオ/チェックが 44px で統一
- [ ] fieldset 見出し下の余白が一定（legend 標準）
- [ ] 行間は `.5rem` or `1.5rem` のみ
- [ ] インラインJSなし（共通JS呼び出しのみ）
- [ ] マジックナンバーなし（トークン使用）

---

## 7. よくある質問（FAQ）
- Q: セレクト矢印の位置が気になる
  - A: `background-position` は相対配置。ズレる場合は 1px 単位の微調整を forms.css に限定して加える
- Q: 日付入力のアイコン位置がわずかにズレる
  - A: `.nr-date-picker .calendar-icon` の `top` を ±1px 調整（全体へ波及しないよう限定的に）

---

## 8. 運用方針
- 新規画面は原則トークン/標準マクロ/共通JSを使用
- 既存画面は段階移行（表示差ゼロを前提に小さく適用）
- 例外はコメントで理由を必ず明記

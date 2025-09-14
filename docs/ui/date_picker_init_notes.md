# Date Picker Init 外部化メモ（UI不変/CSP対応）

目的: base.html の inline 初期化を撤去し、外部JSとして安定・再入可能な初期化パスを確立する。画面の見た目・動作は一切変更しない。

## 現状と変更点の棚卸し
- 変更済:
  - app/templates/base.html
    - 旧: inline `<script>…flatpickr 初期化…</script>`
    - 新: 外部JS `app/static/js/date_picker_init.js` を `defer` で読込
  - app/static/js/date_picker_init.js
    - DOMContentLoaded で `window.flatpickr` を検出→初期化
  - 依存関係（ベンダー）
    - flatpickr 本体: `https://cdn.jsdelivr.net/npm/flatpickr`
    - ロケール: `https://cdn.jsdelivr.net/npm/flatpickr/dist/l10n/ja.js`
- UIは不変（フォーマット/ロケール/挙動は旧実装と同一）。

## 依存順序の保証（設計）
- 期待順: 1) flatpickr 本体 → 2) locale(ja) → 3) date_picker_init.js
- 実装根拠:
  - すべて `defer` 属性を付与し、HTML に記述された順で実行される（同一ドキュメント・同一オリジン評価）。
  - 初期化側は `if (!window.flatpickr) return;` の no-op で安全（ロード順逆転・CDN遅延時でも落ちない）。
- 破壊的事象への備え:
  - いずれかのCDNが失敗した場合は、初期化は実行されず（no-op）、画面はテキスト入力として動作（回避不能だがクラッシュはしない）。

## セレクタ方針（将来互換を含む）
- 方針: `[data-role="date-picker"]` を唯一の公式フックとする。
- 現状（互換維持）:
  - 既存構造 `div.nr-date-picker[data-wrap]`（アイコンとwrap）と `.js-date` をサポート。
  - 将来的にテンプレを段階置換し、`[data-role="date-picker"]` のみに統一予定。
- ガイド:
  - wrapモード: `div.nr-date-picker[data-wrap]` 内に入力→ flatpickr({ wrap:true })
  - 直接入力: `.js-date` に直接適用（wrapではない）
  - 新規は原則 `[data-role="date-picker"]` を使用（wrap/直接いずれも可）。

## 初期化の idempotent 要件
- 要件: 複数回実行されても重複初期化しない（再実行OK）。
- 現状: DOMContentLoaded で1回実行し、flatpickr未ロード時は no-op。重複バインドを避けるため、段階導入時は以下のいずれかで保護できる：
  - `data-fp-initialized="1"` などのフラグ属性をセットし、再走でスキップ。
  - 既に `._flatpickr` プロパティが存在する要素をスキップ。
- 例外ハンドリング:
  - try/catch で個別要素の失敗を握りつぶし、他要素への初期化は継続。
  - ベンダー未ロード時/DOM未検出時は即 return（no-op）。

### 参照実装（抜粋・方針説明用）
```js
// Pseudo (現行挙動 + 将来の二重起動対策コメント)
document.addEventListener('DOMContentLoaded', function(){
  if (!window.flatpickr) return; // no-op if vendor missing
  var opts = {/* 旧実装と同一 */};
  document.querySelectorAll('.nr-date-picker').forEach(function(el){
    // if (el.dataset.fpInitialized) return; // 将来: 二重起動防止
    flatpickr(el, Object.assign({ wrap: true }, opts));
    // el.dataset.fpInitialized = '1';
  });
  document.querySelectorAll('.js-date').forEach(function(input){
    if (input.closest('.nr-date-picker')) return;
    // if (input._flatpickr) return; // 将来: 二重起動防止
    flatpickr(input, opts);
  });
});
```

## CSP（Content Security Policy）
- script:
  - 旧: inline 初期化のため `script-src 'unsafe-inline'` が必要
  - 新: 外部JS化により `unsafe-inline` は不要（ベンダーCDNとselfの許可のみ）
  - 推奨例:
    - `Content-Security-Policy: script-src 'self' https://cdn.jsdelivr.net; object-src 'none'; base-uri 'self';`
- style:
  - base.html には最小の inline `<style>` が残存（flatpickr年セレクト調整）。
  - 将来的に外部CSSへ移管すると `style-src 'unsafe-inline'` も不要化できる。

## 検証項目（コード不要の手順書）
1) Lighthouse/LCP
   - Before/After のLCP・TBTが悪化していない（△差は測定誤差内）。
2) E2E（Playwright想定）
   - 日付入力フィールドをクリック→カレンダーから任意日選択→表示が `YYYY-MM-DD` に変わる→送信でサーバ受理（200）
3) ロード順逆転耐性
   - init.js のみ先に読み込んだ疑似条件（DevToolsのネットワークスロットリングで flatpickr を遅延）でも例外が出ず no-op（入力は通常テキストとして機能）。
4) 再実行耐性
   - DevTools コンソールから初期化関数に相当する処理を再実行しても例外が出ない（重複初期化なし）。

## 回帰テスト項目リスト（手順）
- 描画
  - 画面ロード時にコンソールエラーが無い
  - 日付入力の placeholder/altInput が旧実装と一致
- 入力
  - カレンダー操作で日付確定→ altInput に日本語表示、hidden/実値は `YYYY-MM-DD`
- フォーカス/アクセシビリティ
  - アイコンボタン（wrap）のクリックでピッカーが開閉
  - Tab移動で不自然なフォーカス移動が起きない
- エッジ
  - DOMの `.nr-date-picker` の無い画面でも例外が出ない
  - ベンダー読み込み失敗時でもクラッシュせずテキスト入力として送信可能

## 推奨コミット粒度
1) docs: 本メモ（docs/ui/date_picker_init_notes.md）追加
2) tests(e2e): Playwright の最小シナリオを1本追加（後日）
3) docs/README: CSP例（script-src から unsafe-inline の削除可）を短く追記

## 変更ファイル一覧（今回）
- app/templates/base.html（inline 初期化撤去・defer外部化）
- app/static/js/date_picker_init.js（初期化ロジック・旧挙動同等）
- docs/ui/date_picker_init_notes.md（本書）

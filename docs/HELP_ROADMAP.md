# ヘルプチャット埋め込みロードマップ（v1）

目的: 専門用語の壁を下げ、画面文脈に寄り添い、短く親切な案内を提供。まずは申告アプリを完成させ、同時進行でヘルプに必要な「土台」を仕込む。

---

## 結論（方針）
- 申告フローとデータ/文言/画面構造を先に固める。
- 今の段階ではヘルプ用の「用語集/FAQ・文脈API・イベント計測・UIフック」だけを仕込む。
- サブエージェント常駐（受動観察で学習）は不要。RAG＋文脈APIの方が品質・運用性が高い。

---

## 今すぐやること（ToDo）
1) 用語/FAQ の雛形作成
- `resources/help/glossary.yml` と `resources/help/faq.yml` を追加。
- まず 5〜10 項目だけ登録（定義・例・出典URL）。

2) 文脈APIの雛形
- `app/help/` Blueprint を作成：
  - `GET /help/context`（今の page/year/company_type を返す）
  - `GET /help/suggest?page=...`（ページ別サジェストをYAMLから返す）

3) UIフックの占位
- `base.html` に右下「？ヘルプ」ボタンとモーダル（非活性）を追加。
- 環境フラグ `HELP_ENABLED=false` で非表示制御。

4) イベント計測（匿名）
- 1〜2 画面で「バリデーション失敗/離脱/滞在>60秒」を記録。
- 個人情報は送らない（フィールド名のみ・数値は丸め/マスク）。

5) 命名規約の明文化
- 画面キー（page）/年版（year）/会社種別の取得を統一。docs/に短い規約を追加。

---

## ロードマップ（段階導入）
- フェーズ0（同時進行・1日）
  - ルール/命名の単一化、フラグ `HELP_ENABLED`, `HELP_CHAT_MVP`, `HELP_RAG_ENABLED` を `config.py` に追加。
- フェーズ1（1〜2週間・MVP/LLMなし）
  - `GET /help/suggest` と `GET /help/glossary` で回答（YAML参照）。
  - UI: モーダルにサジェスト3件＋用語検索。回答は1〜3行＋出典リンク。
- フェーズ2（2〜3週間・RAG）
  - docs/handovers、画面仕様、アプリ内ヘルプを索引化（ローカルDB or Faiss）。
  - `POST /help/chat` で文脈（page/year/差額状態）を付与→抽出→要約。出典断片を必ず表示。
- フェーズ3（+1週間・タスク指向）
  - 「この画面の必須だけ」「差額の原因候補」などをボタン化。

---

## API（最小仕様）
- `GET /help/context` → `{ "page":"deposits", "year":"2025", "company_type":"KK" }`
- `GET /help/suggest?page=deposits` → `{ "suggestions":[ {"q":"預金種類とは？","id":"dep_type"}, ... ] }`
- `GET /help/glossary?q=期末現在高` → `{ "term":"期末現在高", "desc":"決算日時点の残高…", "links":[{"title":"国税庁","url":"https://…"}] }`

---

## YAML雛形
- `resources/help/glossary.yml`
```yaml
- term: 期末現在高
  alias: [残高]
  desc: 決算日時点の残高。通帳残高等を基に入力します。差額があれば調整科目を確認します。
  example: 通帳残高が1,000,000円の場合は「1,000,000」
  links:
    - title: 国税庁タックスアンサー（参考）
      url: https://www.nta.go.jp/taxes/shiraberu/taxanswer/
```
- `resources/help/faq.yml`
```yaml
- page: deposits
  q: 預金種類の選び方は？
  a: 銀行の種別欄に合わせて「普通/当座/定期」等を選びます。迷ったら通帳の表記を確認してください。
  links:
    - title: 国税庁（勘定科目内訳書）
      url: https://www.nta.go.jp/
```

---

## イベント計測（匿名）
- クライアント→`POST /metrics/event`（バッチ/デバウンス）
```json
{"page":"deposits","event":"validation_error","field":"account_number","ts":1690000000}
```
- サーバはPII排除・集計のみ（週次レビュー）。

---

## リスク/対策
- 幻覚対策: フェーズ1はLLMなし。フェーズ2もRAG＋出典必須。
- PII対策: 送信前にマスク、サーバ側でもスキーマチェック。
- 年版差: 回答に必ず year を明記（例: 「令和7年版」）。

---

## 完成の定義（MVP）
- `HELP_ENABLED=true` でヘルプUIが表示、サジェスト/用語検索が応答。
- `GET /help/context` が正しい page/year を返す。
- 5〜10 用語・FAQに1〜3行回答＋出典を表示。
- 1画面で匿名イベントが記録される。

---

## 次アクション（あなた）
- 1) glossary.yml / faq.yml に5〜10項目を記入
- 2) `app/help/` のBlueprintと2つのGETエンドポイントを作成
- 3) base.html にヘルプFABとモーダル（非活性）を配置
- 4) 預貯金等画面に匿名イベントログを仕込む
- 5) 命名規約（page/year/会社種別）をdocs化

---

## 備考
- このロードマップをベースに、RAG導入時は docs/handovers の要点を索引化。画面キーと年版をクエリ条件にする。
- 監修が必要な回答（税務判断）は「一般情報・根拠提示・専門家相談の促し」にとどめる。

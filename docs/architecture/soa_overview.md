# Statement of Accounts アーキテクチャ概要

## 全体像
```
+---------------------------+       +----------------------------+
| STATEMENT_PAGES_CONFIG    |       | app/domain/soa/evaluation  |
| (resources/config & code) | --->  | SoAPageEvaluation          |
+---------------------------+       +----------------------------+
              |                                   ^
              v                                   |
+---------------------------+       +----------------------------+
| StatementOfAccountsFlow   | <---- | SoADifferenceBatch         |
| (app/company/services)    |       | (request-scoped cache)     |
+---------------------------+       +----------------------------+
              |                                   ^
              v                                   |
+---------------------------+       +----------------------------+
| Templates / Controllers   |       | SoASummaryService          |
+---------------------------+       |  - source totals           |
                                    |  - breakdown totals        |
                                    +----------------------------+
```

## 主要コンポーネント
- **STATEMENT_PAGES_CONFIG**: `resources/config/soa_pages.json` と `app/services/soa_registry.py` で合成。フォーム・PDF・ナビ情報の単一ソース。
- **SoAPageEvaluation**: `difference`（BS/PLとの差額）、`skip_total`（スキップ判定値）等を保持する集約データ。
- **SoADifferenceBatch**: リクエスト中のページ評価をキャッシュし、複数ビューからの参照を最小化。
- **StatementOfAccountsFlow**: 評価結果をテンプレート向けに変換し、進捗や CTA 判定を担当。

## データフロー
1. フローがページ表示を要求 → `SoADifferenceBatch.get(page)` を呼び出し。
2. バッチは `SoASummaryService.evaluate_page` を通じて差分／スキップを計算し `SoAPageEvaluation` を返却。
3. フローは結果を基にナビゲーション状態とサマリーを整形、テンプレートへ渡す。

## 拡張ポイント
- **フォーム定義**: `app/company/forms/metadata.py` で WTForms から自動抽出したメタデータを `STATEMENT_PAGES_CONFIG` に反映。カスタム設定は上書きで維持。
- **PDF/外部入出力**: `app/services/pdf_registry.py` と `app/domain/tax` を連携させる際は `SoAPageEvaluation` を参照することで整合性を保持。

## 運用メモ
- 新規ページ追加時は `soa_pages.json` にキーを定義 → 該当フォーム／モデルを用意 → `tests/test_soa_config_integrity.py` で整合性を確認。
- ナビゲーション順は `SOA_NAV_ORDER` で管理。フォームとモデルの同期は自動化されたため、重複定義が必要な場合のみ差分記述する。
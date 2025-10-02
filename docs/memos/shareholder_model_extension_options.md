# Shareholderモデル拡張オプション比較

## 1. 現状のテーブル構造

- `shareholder`
  - 共通情報: `last_name`, `entity_type`, `shares_held`, `voting_rights`, `is_controlled_company` など。
  - 個別情報: `relationship` (個人専用), `prefecture_city`, `investment_amount` など。
  - 親子関係: `parent_id` により関連株主を表現。

- 課題
  - 個人・法人・自社の属性が混在し、カラム追加のたびに共通テーブルが肥大化。
  - フォーム (`app/company/forms/shareholders.py`) や PDF が `entity_type` で分岐しつつ個別カラムを参照。

## 2. オプション比較

### A. タイプ別詳細テーブル方式（推奨）
- 構成
  - 共通テーブル: `shareholder`
  - 1:1 詳細テーブル: `shareholder_individual_detail`, `shareholder_corporate_detail`, `shareholder_self_company_detail`
  - ORM: `Shareholder.individual_detail` などで eager load
- メリット
  - SQL 制約（NOT NULL, FK）がタイプ別に適用でき、整合性管理が容易。
  - 追加属性が各詳細テーブルに閉じるため、共通テーブルが肥大化しない。
  - フォームやサービスで型ごとのロジックが明確化。
- デメリット
  - テーブル数が増え、マイグレーションと JOIN の設計が必要。

### B. `extra_attributes` JSONB 方式
- 構成
  - 共通テーブルに `extra_attributes` JSONB カラムを追加。
  - タイプ別属性を JSON に格納。
- メリット
  - スキーマ変更が不要、柔軟性が高い。
  - 軽微な属性追加入力に素早く対応可能。
- デメリット
  - 型チェック/バリデーションをアプリ側に委ねる必要がある。
  - 集計や検索で JSON 演算子に依存し、パフォーマンス・保守性が低下。
  - マイグレーションでのフィールド名変換が難解。

## 3. 推奨方針

- タイプ別詳細テーブル方式を採用。税務関連データは型と制約が明確である方が保守しやすく、UI/帳票の条件分岐も簡潔になる。
- 旧カラムは移行後に段階的に廃止し、サービス層で互換アクセサを提供（例: `ShareholderService` が `shareholder.individual_detail.relationship` を返す）。

## 4. 次のステップ（案）

1. 詳細テーブルごとの必須/任意フィールドを事業サイドと確定。
2. Alembic マイグレーション草案: 新テーブル作成、既存データのバックフィル。
3. ShareholderService とフォームを詳細テーブル対応にリファクタ。
4. テスト追加: 個人・法人・自社株主それぞれの CRUD と帳票出力を網羅。

---

この文書は比較用ドラフトです。レビュー後、マイグレーション仕様と実装計画を詳細化します。

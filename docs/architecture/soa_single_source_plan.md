# SoA 単一ソース化 設計メモ

## 目的
- SoA（勘定科目内訳明細書）のモデル、フォーム、テンプレート、PDF の定義を**単一のデータソース**で管理する。
- LoansReceivable の列追加など、変更が一箇所で済むようにし、差分を pytest で自動検知する。
- 将来的に PDF レイアウトや外部連携が拡張されてもドリフトを防ぐ基盤を用意する。

## 新ファイル案
- `resources/config/soa_schema_map.yaml`
  - **構成イメージ**
    ```yaml
    pages:
      deposits:
        model: app.company.models.Deposit
        form: app.company.forms.DepositForm
        template: company/deposit_form.html
        pdf_key: deposits
        order: 10
        total_field: balance
        fields:
          - name: financial_institution
            label: 法人名
            placeholder: 例：〇〇銀行
            type: string
            required: true
            pdf:
              key: deposits.financial_institution
          - name: balance
            label: 期末残高
            type: money
            required: true
            pdf:
              key: deposits.balance
      ...
    meta:
      generated_at: "{{ build timestamp }}"
      version: 1
    ```
  - **fields セクションの属性例**
    - `label` / `placeholder` / `type` / `required`
    - `render`: `select` / `checkbox` 等、フォーム特有の設定
    - `pdf.key`: PDF 座標マッピング用のキー
    - `choices`: セレクトオプション（必要な場合）

## 生成＆検証フロー
1. **ビルド時の生成スクリプト（新規）**
   - 入力: `soa_schema_map.yaml`
   - 出力:
     - `resources/config/soa_pages.json`（既存互換）
     - `app/company/forms/soa/metadata.py` のプレースホルダ差し替え
     - `app/company/forms/soa/definitions.py` のフィールド定義をテンプレ生成（既存の lambda 定義を置換予定）
   - 必要に応じて Jinja テンプレートやコード生成ユーティリティを用意。

2. **pytest による検証タスク**
   - `tests/test_soa_schema_map.py`（新規）で以下をチェック:
     - YAML → JSON 生成結果とリポジトリ内ファイルが一致するか（逸脱時は再生成を促す）。
     - YAML に記載された `fields` がフォームクラス・テンプレート・PDF 定義にすべて存在するか。
     - PDF キー（`pdf.key`）が `resources/pdf_templates/*` の JSON に存在するか。
   - 既存テスト `tests/test_soa_config_integrity.py` は徐々に削減し、新テストに統合。

3. **差分検知**
   - LoansReceivable など列追加時は `soa_schema_map.yaml` を更新。生成スクリプトを実行すると関連ファイルが自動更新される。
   - `pytest` が YAML と生成物のズレを検知して失敗するため、ヒューマンエラーを防止。

## リファクタ段階（推奨順）
1. `soa_schema_map.yaml` を導入し、現行設定を移植。生成スクリプト・pytest を整備。
2. `soa_registry.py` を YAML ベースに切り替え、旧 JSON を生成物として保持する（互換目的）。
3. `forms/soa/definitions.py` と `metadata.py` を自動生成化。手書きの lambda / metadata を撤廃。
4. テンプレートの `render_field` 呼び出しを YAML 情報と突き合わせる検証を追加。
5. 最終的に旧 API や互換レイヤを削除（提案②の流れと統合）。

## 既存コードへの影響
- `app/services/soa_registry.py` が読み込むデータソースを切り替える必要あり。
- `app/company/forms/soa/` 配下のフォームクラスは動的生成へ移行するため、テストの import パスに注意。
- PDF テンプレートのキーを YAML に明記することで、テンプレ側も整合性チェック対象となる。

## TODO リスト（チケット化推奨）
- [ ] `soa_schema_map.yaml` の初期投入・移植スクリプト作成
- [ ] 生成スクリプト（CLI or invoke タスク）の実装
- [ ] pytest による生成物の整合チェック追加
- [ ] PDF キー整合チェックの追加
- [ ] 既存 JSON / metadata ファイルの自動生成化と旧コードの削除
- [ ] ドキュメント整備（開発手順、再生成方法）

---
本メモは設計指針と TODO の整理目的です。実装時は小さな PR に分割し、生成スクリプトとテストを優先して整備してください。
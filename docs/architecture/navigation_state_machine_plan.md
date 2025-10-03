# Navigation State Machine 設計メモ

## 現状整理

- `app/navigation.py` 内でナビゲーション状態（完了ステップ・スキップステップ）を都度計算。
  - セッションの `wizard_completed_steps` に直接アクセスしつつ、SoA のスキップ判定・進捗確認を個別関数で組み合わせている。
  - `compute_skipped_steps_for_company()` が AccountingData を直接問い合わせ、SoA 項目ごとに判定。
  - 例外処理が散発的 (`_log_navigation_issue`) で、複数の `try/except` が点在。
- ステップ完了記録は `mark_step_as_completed` / `unmark_step_as_completed` でセッションを書き換えるのみ。
- `statement_of_accounts.py` など複数のビューが `get_navigation_state()` を呼び、それぞれで skipped を上書きするケースがある。
- ナビゲーション構造自体は `navigation_builder` / `navigation_models` を通じて組み立てられているが、状態管理と結合していない。

### 課題
1. 状態の計算と副作用が単一関数で混在し、拡張しづらい。
2. セッション直接参照のためテストが書きにくい。
3. SoA 進捗・スキップ判定がフリーファンクションで散乱。
4. ナビゲーション構造に紐づくルール（例: filing_group の調整）が散発的に出現。

## 目標
- ナビゲーション状態計算を状態機械（ステートマシン）として切り出し、入力（ユーザ・会社・セッション・オプション）から一貫した出力（ナビゲーションツリー + メタ）を生成する。
- 進捗・スキップなどのルール更新を専用クラスに閉じ込め、ユニットテストしやすくする。
- セッション更新はステートマシン経由で行い、副作用を明示。

## 提案アーキテクチャ

### 1. `NavigationState` データモデル
```python
@dataclass
class NavigationState:
    items: list[NavigationNodeState]
    skipped_keys: set[str]
    completed_keys: set[str]
```
`NavigationNodeState` は既存 `NavigationNode` から派生する描画用データを保持。

### 2. `NavigationStateMachine`
責務:
- 初期化時に `user`, `session`, `current_page`、任意でプリセット skipped/completed を受け取る。
- `compute()` で以下のステップを順序立てて実施:
  1. セッション情報・ウィザード進捗をロード
  2. SoA 進捗（`SoAProgressEvaluator`）・スキップ（`SoASummaryService`）の計算
  3. ナビゲーションツリーへ状態付与 (`NavigationNode#to_dict` を代替するメソッド)
  4. フィルタリングルール適用（例: filing_group prune）
- セッションを書き換える必要がある場合は `mutations` をキューにため、最終的に `apply(session)` で実施。

#### インタフェース案
```python
class NavigationStateMachine:
    def __init__(self, user, session, current_page: str, *, preset_skip: set[str] | None = None):
        ...

    def compute(self) -> NavigationState:
        ...

    def mark_completed(self, step_key: str) -> None:
        ...

    def unmark_completed(self, step_key: str) -> None:
        ...

    def apply_mutations(self, session) -> None:
        ...
```

### 3. SoA 進捗 / スキップの再配置
- `_fetch_latest_accounting_data` などはステートマシン内部のヘルパーとして集約。
- 外部から `compute_skipped_steps_for_company` が必要なケースは薄いので、ステートマシンのメソッド `get_skipped_keys()` を提供。

### 4. ビュー側の変更
- `get_navigation_state` 関数をステートマシンにラップし、暫定的な互換関数として `NavigationStateMachine.current_state()` を呼ぶよう差し替える。
- 既存の `mark_step_as_completed` / `unmark_step_as_completed` はステートマシンを通す形で実装し直し、旧関数は互換用薄ラップにする。

## 遷移ルールの整理
- 各ナビゲーションノード `NavigationNode` が `key`, `children`, `params` を持つ。ステートマシンでは以下を注入:
  - `is_active`: `current_page` と一致するか
  - `is_completed`: `completed_keys` に含まれるか
  - `is_skipped`: `skipped_keys` に含まれるか
- SoA 子ノードの特別処理（`SoAProgressEvaluator`）は `append_progress_completion` 相当をステートマシンの `_augment_completed_keys()` に統合。
- Filing グループの除外は `_apply_post_filters()` で定義。

## 実装段階案
1. ステートマシン・データモデルを追加し、既存関数を内部で呼び出すようにリファクタ（動作互換を維持）。
2. ビュー側 (`statement_of_accounts`, `import_data`, その他) が `get_navigation_state` を直接呼ぶ箇所を置換。
3. 旧関数 `_determine_skipped_steps` などを段階的に削除し、ユニットテスト (`tests/test_navigation_state_machine.py` など) を追加。

## テスト戦略
- モック可能な `NavigationStateMachine` 単体テスト
  - `preset_skip` を与えた場合
  - SoA データが存在しない場合（最初の子を skip ）
  - Filing グループ除外ロジック
- 既存ナビゲーション関連テスト (`tests/test_sidebar_skip_on_form_pages.py` など) でリグレッション確認。

## 次ステップ
- `NavigationStateMachine` の骨格クラスとデータモデルを作成して差し替え実装開始。
- ユニットテスト雛形 (`tests/test_navigation_state_machine.py`) を作り、現状動作の追従テストを追加。

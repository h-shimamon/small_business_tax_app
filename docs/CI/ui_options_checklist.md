# UI Options: 直書き検出と運用チェックリスト

目的: テンプレやビューに散在する選択肢の直書きを防ぎ、`ui_options` のSSOTからのみ参照させる。

## PRチェックリスト（レビュアー向け）
- [ ] 新規/変更テンプレで `ui_options.*` を参照している（`OPTIONS_` 定義や配列直書きが無い）
- [ ] ビュー/サービスは `ui_options` を生成しない（サーバは SSOT を汚染しない）
- [ ] `get_ui_options()` の呼び出しはテンプレフォールバックとしてのみ使用（原則はDI）
- [ ] `ui_options` のキーは既存セットのみ（未知キーは追加議論）
- [ ] 並び順やラベル変更が無い（UI不変方針）

## 直書き検出（ローカル/CIでの推奨ワンライナー）
```bash
# 1) テンプレ直書き配列 (例: options=[('a','A'), ...])
rg -n "options=\[" app/templates | rg -v "ui_options"

# 2) 旧スタイルのプレースホルダ/定数（例: OPTIONS_ や set ... = [...]）
rg -n "OPTIONS_|\{\% set .*?= \[" app/templates

# 3) 直書き参照（ui_optionsを経由しない segmented/select の options指定）
rg -n "segmented\(|select\(" app/templates | rg -v "ui_options\.|ui/|_bo_grid_macros\..*"
```

CI導入メモ:
- 上記1〜3のいずれかがヒットしたら失敗（fail-on-found）
- 一時的な例外は `# CI-ALLOW:` コメントを近傍に入れ、`rg -v` で除外

## 運用ルール（開発者向け）
- 選択肢は `app/constants/ui_options.py` へ追加（profile差分は `PROFILES` へ）
- テンプレでは `ui_options.*` のみ参照（`get_ui_options()` は緊急フォールバック）
- ラベル/順序変更は "UI不変" の範囲外。変更時は関係者承認の上で別PRに分ける

## 参考
- SSOT: `app/constants/ui_options.py`
- DI: `app/ui/context.py`（`build_ui_context()` / `attach_app_ui_context()`）
- 設定: `app/config/schema.py`（`UI_PROFILE`, `ENABLE_UI_OPTIONS_DI` ほか）

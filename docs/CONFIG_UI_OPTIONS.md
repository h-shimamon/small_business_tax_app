# UI Options DI 経路（設定 → コンテキスト）

目的: テンプレ内の選択肢を SSOT 化し、設定 → DI → context → template の流れで供給する。

## 構成
- 設定: `app/config/schema.py` の `AppSettings`
- 定義: `app/constants/ui_options.py` の `get_ui_options(profile)`
- DI: `app/ui/context.py`
  - `build_ui_context(settings)` → `{ 'ui_options': {...} }`
  - `attach_company_ui_context(company_bp)` で Blueprint に context_processor を登録
- 登録: `create_app()` で `app.extensions['settings'] = AppSettings()`

## 環境変数（既定）
- `APP_LOCALE: str = 'ja_JP'`
- `APP_UI_PROFILE: str = 'default'`
- `APP_ENABLE_UI_OPTIONS_DI: bool = 1`
- `FEATURE_FLAGS: dict[str,bool]`（pydantic-settings 使用時のみ。envから dict 直読みは推奨しないため未マップ）

## テンプレでの使い方
```
{{ ui_options.pc_os }}           {# [('win','Windows'),('mac','Mac'),...] #}
{{ ui_options.staff_roles }}     {# [('nonexec','非常勤役員'), ...] #}
```
既存の `{% set OPTIONS_* = [...] %}` は不要（撤去済み）。

## 代表画面（適用済み）
- `app/templates/company/filings/business_overview_1.html`
  - `OPTIONS_*` を `ui_options.*` に差し替え

## 型
- `UIOptions` (TypedDict): `staff_roles`, `pc_os`, `pc_usage`, `ecommerce`, `data_storage`
- `Option = tuple[str, str]`

## テスト方針（概略）
- Unit: `build_ui_context` が `{'ui_options': ...}` を返す
- E2E: 代表画面で `ui_options` がレンダリングに到達していること（DOM検査）


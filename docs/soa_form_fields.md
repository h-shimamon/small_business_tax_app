# Statement of Accounts Form Field Configuration

`STATEMENT_PAGES_CONFIG` (located in `app/company/soa_config.py`) is the single source of truth for Statement of Accounts (SoA) form rendering.

## Config Keys

Each entry may define:

- `model`: ORM model for persistence.
- `form`: WTForms class generated dynamically (`app/company/forms/soa_definitions.py`).
- `title`: Display name in the UI.
- `total_field`: Column used for SoA totals.
- `template`: Template path used by SoA views.
- `query_filter` *(optional)*: Callable to restrict queries (e.g. miscellaneous income/loss split).
- `form_fields`: Ordered metadata for rendering fields. Items are either:
  - `"field_name"` (string) — default rendering.
  - Mapping with keys:
    - `name` *(required)*
    - `placeholder`
    - `type` (input type override, e.g. `number`)
    - `class` (additional CSS classes)
    - `rows` (for text areas)
    - `autofocus` (boolean)
    - `render` (`checkbox` to use checkbox helper)

## Render Flow

1. `StatementOfAccountsService` loads data for requested page keys.
2. `statement_of_accounts.py` passes the matching `form_fields` into the template context.
3. `app/templates/company/_soa_form_macros.html::render_soa_form` iterates through `form_fields`, handling placeholders, CSS classes, and special widget rendering.

## Workflow

- **Adding/Updating a page**
  1. Extend `STATEMENT_PAGES_CONFIG` with the new `form_fields` metadata.
  2. Ensure routes/services reference the same key.
  3. Templates automatically pick up the configuration—manual field edits are unnecessary.

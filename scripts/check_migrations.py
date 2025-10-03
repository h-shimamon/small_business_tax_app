#!/usr/bin/env python3
"""Static checks for Alembic migrations.

- 突合: revision / down_revision の整合性と欠番の検出
- コメント: 各マイグレーションのモジュール docstring が空でないことを確認

CI で実行し、基準を満たさない場合はエラーで終了する。
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path
from typing import Any, Iterable

REPO_ROOT = Path(__file__).resolve().parent.parent
MIGRATIONS_DIR = REPO_ROOT / "migrations" / "versions"


def _iter_migration_paths() -> Iterable[Path]:
    for path in sorted(MIGRATIONS_DIR.glob("*.py")):
        if path.name == "__init__.py":
            continue
        yield path


def _load_module_ast(path: Path) -> ast.Module:
    source = path.read_text(encoding="utf-8")
    return ast.parse(source, filename=str(path))


def _extract_assign(module: ast.Module, name: str) -> Any:
    for node in module.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == name:
                    return ast.literal_eval(node.value)
    raise ValueError(f"Missing '{name}' assignment")


def _ensure_docstring(path: Path, module: ast.Module, issues: list[str]) -> None:
    doc = ast.get_docstring(module)
    if not doc:
        issues.append(f"{path.name}: module docstring is missing")
        return
    if not doc.strip():
        issues.append(f"{path.name}: module docstring is empty")


def _flatten_down_revision(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        result: list[str] = []
        for item in value:
            result.extend(_flatten_down_revision(item))
        return result
    if isinstance(value, str):
        return [value]
    raise TypeError(f"Unsupported down_revision type: {type(value)!r}")


def main() -> int:
    issues: list[str] = []
    revision_map: dict[str, Path] = {}
    down_references: set[str] = set()

    for path in _iter_migration_paths():
        module = _load_module_ast(path)
        _ensure_docstring(path, module, issues)

        revision = _extract_assign(module, "revision")
        if not isinstance(revision, str) or not revision.strip():
            issues.append(f"{path.name}: invalid revision identifier")
            continue
        if revision in revision_map:
            issues.append(
                f"Duplicate revision '{revision}' in {path.name} (already defined in {revision_map[revision].name})"
            )
        else:
            revision_map[revision] = path

        down_revision = _extract_assign(module, "down_revision")
        try:
            for ref in _flatten_down_revision(down_revision):
                if not ref:
                    continue
                down_references.add(ref)
        except TypeError as exc:  # pragma: no cover - defensive
            issues.append(f"{path.name}: {exc}")

    # 欠番チェック: 参照されている down_revision に対応するファイルが存在するか
    for ref in sorted(down_references):
        if ref not in revision_map and ref is not None:
            issues.append(f"Missing migration file for down_revision '{ref}'")

    if issues:
        print("Migration checks failed:\n" + "\n".join(f" - {msg}" for msg in issues))
        return 1

    print("All migration checks passed.")
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entrypoint
    sys.exit(main())

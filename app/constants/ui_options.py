# app/constants/ui_options.py
from __future__ import annotations

from typing import TypedDict

Option = tuple[str, str]
Options = list[Option]

class UIOptions(TypedDict, total=False):
    # primary option keys
    staff_roles: Options
    pc_os: Options
    pc_usage: Options
    ecommerce: Options
    data_storage: Options
    # meta (optional)
    version: str
    profile: str

# ---- Base (default) profile ----
VERSION = "v1"

BASE: dict[str, Options] = {
    'staff_roles': [
        ("nonexec", "非常勤役員"),
        ("worker", "工員"),
        ("clerk", "事務員"),
        ("engineer", "技術者"),
        ("sales", "販売員"),
        ("labor", "労務者"),
        ("cook", "料理人"),
        ("hostess", "ホステス"),
        ("other", "その他"),
    ],
    'pc_os': [
        ("win", "Windows"),
        ("mac", "Mac"),
        ("linux", "Linux"),
        ("other", "その他"),
    ],
    'pc_usage': [
        ("payroll", "給与管理"),
        ("inventory", "在庫・販売管理"),
        ("production", "生産管理"),
        ("accounting", "財務管理"),
    ],
    'ecommerce': [
        ("sales", "有・売上"),
        ("purchase", "有・仕入"),
        ("expense", "有・経費"),
        ("none", "無"),
    ],
    'data_storage': [
        ("cloud", "クラウド"),
        ("external", "外部記録媒体"),
        ("server", "PCサーバ"),
    ],
}

# Profile diffs (future use). Keys must exist in BASE; labels/order must be identical unless explicitly allowed.
PROFILES: dict[str, dict[str, Options]] = {
    'default': {},  # no diffs; use BASE
    # 'jp_smb': { 'pc_os': BASE['pc_os'] },  # example
}


def _merge_profile(base: dict[str, Options], diff: dict[str, Options]) -> UIOptions:
    out: UIOptions = {}
    # copy base keys only (guard against unknown keys)
    for k, v in base.items():
        if k in diff and isinstance(diff[k], list):
            out[k] = diff[k]  # type: ignore
        else:
            out[k] = v  # type: ignore
    return out


def get_ui_options(profile: str = "default") -> UIOptions:
    """Return UI options for the given profile with version metadata.
    Unknown profiles fall back to 'default'. UI is unchanged; metadata is additive.
    """
    base = BASE
    diffs = PROFILES.get(profile) or {}
    merged = _merge_profile(base, diffs)
    merged['version'] = VERSION
    merged['profile'] = profile if profile in PROFILES else 'default'
    return merged

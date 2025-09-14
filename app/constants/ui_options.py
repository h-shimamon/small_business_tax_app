# app/constants/ui_options.py
from __future__ import annotations
from typing import List, Tuple, TypedDict, Dict

Option = Tuple[str, str]
Options = List[Option]

class UIOptions(TypedDict):
    staff_roles: Options
    pc_os: Options
    pc_usage: Options
    ecommerce: Options
    data_storage: Options

# Note: labels and order follow existing templates; do not change here.
STAFF_ROLES: Options = [
    ("nonexec", "非常勤役員"),
    ("worker", "工員"),
    ("clerk", "事務員"),
    ("engineer", "技術者"),
    ("sales", "販売員"),
    ("labor", "労務者"),
    ("cook", "料理人"),
    ("hostess", "ホステス"),
    ("other", "その他"),
]

PC_OS: Options = [
    ("win", "Windows"),
    ("mac", "Mac"),
    ("linux", "Linux"),
    ("other", "その他"),
]

PC_USAGE: Options = [
    ("payroll", "給与管理"),
    ("inventory", "在庫・販売管理"),
    ("production", "生産管理"),
    ("accounting", "財務管理"),
]

ECOMMERCE: Options = [
    ("sales", "有・売上"),
    ("purchase", "有・仕入"),
    ("expense", "有・経費"),
    ("none", "無"),
]

DATA_STORAGE: Options = [
    ("cloud", "クラウド"),
    ("external", "外部記録媒体"),
    ("server", "PCサーバ"),
]


def get_ui_options(profile: str = "default") -> UIOptions:
    """Return UI options for the given profile.
    Currently a single profile; hook for future variants.
    """
    return UIOptions(
        staff_roles=STAFF_ROLES,
        pc_os=PC_OS,
        pc_usage=PC_USAGE,
        ecommerce=ECOMMERCE,
        data_storage=DATA_STORAGE,
    )

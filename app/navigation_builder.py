# app/navigation_builder.py
from .navigation_models import NavigationNode
from app.services.app_registry import get_navigation_structure

NAVIGATION_STRUCTURE_DATA = get_navigation_structure()

def build_navigation_tree():
    """
    データ定義に基づき、NavigationNodeのツリーを構築して返す
    """
    return [NavigationNode(**data) for data in NAVIGATION_STRUCTURE_DATA]

# アプリケーション起動時に一度だけツリーを構築
navigation_tree = build_navigation_tree()

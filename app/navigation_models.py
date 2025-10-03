from __future__ import annotations

from flask import url_for


class NavigationNode:
    """ナビゲーションの各項目を表すクラス"""

    def __init__(self, key, name, endpoint=None, params=None, children=None, node_type='menu'):
        self.key = key
        self.name = name
        self.endpoint = endpoint
        self.params = params or {}
        self.node_type = node_type
        self.parent = None
        self.children = []
        if children:
            for child_data in children:
                self.add_child(NavigationNode(**child_data))

    def add_child(self, child_node):
        """子ノードを追加し、親子関係を設定する"""
        child_node.parent = self
        self.children.append(child_node)

    def get_url(self):
        """ノードに対応するURLを生成する"""
        if not self.endpoint:
            return '#'
        return url_for(self.endpoint, **self.params)

    def is_active(self, current_page_key):
        """現在のページキーに基づき、自身または子孫がアクティブかどうかを判定する"""
        if self.key == current_page_key:
            return True
        if self.params and self.params.get('page') == current_page_key:
            return True
        return any(child.is_active(current_page_key) for child in self.children)

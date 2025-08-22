# app/navigation_models.py
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
        """
        現在のページキーに基づき、自身または子孫がアクティブかどうかを判定する
        """
        if self.key == current_page_key:
            return True
        # statement_of_accounts のような特殊ケースに対応
        if self.params and self.params.get('page') == current_page_key:
            return True
        
        # 子孫がアクティブかどうかも再帰的にチェック
        return any(child.is_active(current_page_key) for child in self.children)

    def to_dict(self, current_page_key, completed_steps, skipped_steps=None):
        """
        テンプレートに渡すための辞書形式に変換する
        """
        skipped_steps = skipped_steps or set()
        # 親がアクティブかどうかを計算
        is_parent_active = self.is_active(current_page_key)

        children_states = []
        for child in self.children:
            # 子自身のキーまたはパラメータが一致するかで子のis_activeを決定
            is_child_active = (child.key == current_page_key) or \
                              (child.params and child.params.get('page') == current_page_key)
            
            # SoA以外のグループではスキップ概念を適用しない（堅牢化）
            is_child_skipped = (self.key == 'statement_of_accounts_group') and (child.key in skipped_steps)

            children_states.append({
                'name': child.name,
                'url': child.get_url(),
                'is_active': is_child_active,
                'is_completed': child.key in skipped_steps and False or child.key in completed_steps,
                'is_skipped': is_child_skipped,
                'key': child.key
            })

        return {
            'key': self.key,
            'name': self.name,
            'type': self.node_type,
            'is_active': is_parent_active,
            'children': children_states
        }

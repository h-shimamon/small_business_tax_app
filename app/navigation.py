# app/navigation.py
from flask import session
from .navigation_builder import navigation_tree

def get_navigation_state(current_page_key):
    """
    現在のページキーに基づき、ナビゲーション全体のUI状態を計算して返す。
    計算ロジックはNavigationNodeクラスに委譲する。
    """
    completed_steps = session.get('wizard_completed_steps', [])
    
    nav_state = [
        node.to_dict(current_page_key, completed_steps)
        for node in navigation_tree
    ]
    
    return nav_state

def mark_step_as_completed(step_key):
    """
    指定されたステップを完了済みとしてセッションに記録する。
    """
    completed_steps = session.get('wizard_completed_steps', [])
    if step_key not in completed_steps:
        completed_steps.append(step_key)
        session['wizard_completed_steps'] = completed_steps

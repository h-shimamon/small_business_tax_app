# app/navigation.py
from flask import session
from .navigation_builder import navigation_tree

def get_navigation_state(current_page_key, skipped_steps=None):
    """
    現在のページキーに基づき、ナビゲーション全体のUI状態を計算して返す。
    計算ロジックはNavigationNodeクラスに委譲する。
    """
    completed_steps = session.get('wizard_completed_steps', [])
    skipped_steps = skipped_steps or set()
    
    nav_state = [
        node.to_dict(current_page_key, completed_steps, skipped_steps)
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

def unmark_step_as_completed(step_key):
    """
    指定されたステップの完了状態を解除する（存在する場合のみ削除）。
    """
    completed_steps = session.get('wizard_completed_steps', [])
    if step_key in completed_steps:
        completed_steps = [s for s in completed_steps if s != step_key]
        session['wizard_completed_steps'] = completed_steps

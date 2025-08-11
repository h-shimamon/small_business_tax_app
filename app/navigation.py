# app/navigation.py
from flask import url_for, session

# --- ナビゲーション構造の定義 ---
# アプリケーション全体のナビゲーションを階層構造で定義します。
# type: 'wizard' は進捗インジケーター形式、'menu' は通常のリンク形式のサイドメニューを表します。
NAVIGATION_STRUCTURE = [
    {
        'key': 'company_info_group',
        'name': '基本情報登録',
        'type': 'menu',
        'children': [
            {'key': 'company_info', 'name': '基本情報', 'endpoint': 'company.show'},
            {'key': 'shareholders', 'name': '株主/社員情報', 'endpoint': 'company.shareholders'},
            {'key': 'declaration', 'name': '申告情報', 'endpoint': 'company.declaration'},
            {'key': 'office_list', 'name': '事業所一覧', 'endpoint': 'company.office_list'},
        ]
    },
    {
        'key': 'import_data_group',
        'name': '会計データ選択',
        'type': 'wizard',
        'children': [
            {'key': 'select_software', 'name': '会計ソフト選択', 'endpoint': 'company.select_software'},
            {'key': 'chart_of_accounts', 'name': '勘定科目データ取込', 'endpoint': 'company.upload_data', 'params': {'datatype': 'chart_of_accounts'}},
            {'key': 'data_mapping', 'name': '勘定科目マッピング', 'endpoint': 'company.data_mapping'},
            {'key': 'journals', 'name': '仕訳帳データ取込', 'endpoint': 'company.upload_data', 'params': {'datatype': 'journals'}},
            {'key': 'fixed_assets', 'name': '固定資産データ取込', 'endpoint': 'company.upload_data', 'params': {'datatype': 'fixed_assets'}},
            #{'key': 'balance_sheet', 'name': '貸借対照表/損益計算書確認', 'endpoint': 'company.balance_sheet'},
        ]
    },
    {
        'key': 'statement_of_accounts_group',
        'name': '勘定科目内訳書',
        'type': 'menu',
        'children': [
            {'key': 'deposits', 'name': '預貯金等', 'endpoint': 'company.statement_of_accounts', 'params': {'page': 'deposits'}},
            {'key': 'notes_receivable', 'name': '受取手形', 'endpoint': 'company.statement_of_accounts', 'params': {'page': 'notes_receivable'}},
            {'key': 'accounts_receivable', 'name': '売掛金（未収入金）', 'endpoint': 'company.statement_of_accounts', 'params': {'page': 'accounts_receivable'}},
            {'key': 'temporary_payments', 'name': '仮払金（前渡金）', 'endpoint': 'company.statement_of_accounts', 'params': {'page': 'temporary_payments'}},
            {'key': 'loans_receivable', 'name': '貸付金・受取利息', 'endpoint': 'company.statement_of_accounts', 'params': {'page': 'loans_receivable'}},
            {'key': 'inventories', 'name': '棚卸資産', 'endpoint': 'company.statement_of_accounts', 'params': {'page': 'inventories'}},
            {'key': 'securities', 'name': '有価証券', 'endpoint': 'company.statement_of_accounts', 'params': {'page': 'securities'}},
            {'key': 'fixed_assets', 'name': '固定資産（土地等）', 'endpoint': 'company.statement_of_accounts', 'params': {'page': 'fixed_assets'}},
            {'key': 'notes_payable', 'name': '支払手形', 'endpoint': 'company.statement_of_accounts', 'params': {'page': 'notes_payable'}},
            {'key': 'accounts_payable', 'name': '買掛金（未払金・未払費用）', 'endpoint': 'company.statement_of_accounts', 'params': {'page': 'accounts_payable'}},
            {'key': 'temporary_receipts', 'name': '仮受金（前受金・預り金）', 'endpoint': 'company.statement_of_accounts', 'params': {'page': 'temporary_receipts'}},
            {'key': 'borrowings', 'name': '借入金及び支払利子', 'endpoint': 'company.statement_of_accounts', 'params': {'page': 'borrowings'}},
            {'key': 'executive_compensations', 'name': '役員給与等', 'endpoint': 'company.statement_of_accounts', 'params': {'page': 'executive_compensations'}},
            {'key': 'land_rents', 'name': '地代家賃等', 'endpoint': 'company.statement_of_accounts', 'params': {'page': 'land_rents'}},
            {'key': 'miscellaneous', 'name': '雑益・雑損失等', 'endpoint': 'company.statement_of_accounts', 'params': {'page': 'miscellaneous'}},
        ]
    },
    # 他のトップレベルメニューもここに追加できます
    # {'key': 'fixed_assets_group', 'name': '固定資産台帳', 'type': 'menu', 'children': [...]},
    # {'key': 'tax_return_group', 'name': '申告書データ', 'type': 'menu', 'children': [...]},
]

def get_navigation_state(current_page_key):
    """
    現在のページキーに基づき、ナビゲーション全体のUI状態を計算して返す。
    """
    completed_steps = session.get('wizard_completed_steps', [])
    nav_state = []

    for parent in NAVIGATION_STRUCTURE:
        parent_state = {
            'name': parent['name'],
            'type': parent['type'],
            'is_active': False,
            'children': []
        }
        
        # 親がアクティブかどうかを判定するためのフラグ
        parent_is_active_flag = False

        for child in parent['children']:
            is_child_active = False
            # 子のキーが現在のページキーと直接一致する場合
            if child['key'] == current_page_key:
                is_child_active = True
            # 勘定科目内訳書グループの場合、params['page']で判定
            elif parent['key'] == 'statement_of_accounts_group' and child.get('params') and child['params'].get('page') == current_page_key:
                is_child_active = True

            if is_child_active:
                parent_is_active_flag = True

            # URLを生成
            params = child.get('params', {})
            url = url_for(child['endpoint'], **params) if child.get('endpoint') else '#'

            child_state = {
                'name': child['name'],
                'url': url,
                'is_active': is_child_active,
                'is_completed': child['key'] in completed_steps
            }
            parent_state['children'].append(child_state)
        
        parent_state['is_active'] = parent_is_active_flag
        nav_state.append(parent_state)

    return nav_state

def mark_step_as_completed(step_key):
    """
    指定されたステップを完了済みとしてセッションに記録する。
    """
    completed_steps = session.get('wizard_completed_steps', [])
    if step_key not in completed_steps:
        completed_steps.append(step_key)
        session['wizard_completed_steps'] = completed_steps

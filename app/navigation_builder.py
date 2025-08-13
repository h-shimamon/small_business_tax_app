# app/navigation_builder.py
from .navigation_models import NavigationNode

# 元のnavigation.pyから構造定義を移設
NAVIGATION_STRUCTURE_DATA = [
    {
        'key': 'company_info_group',
        'name': '基本情報登録',
        'node_type': 'menu',
        'children': [
            {'key': 'company_info', 'name': '基本情報', 'endpoint': 'company.info'},
            {'key': 'shareholders', 'name': '株主/社員情報', 'endpoint': 'company.shareholders'},
            {'key': 'declaration', 'name': '申告情報', 'endpoint': 'company.declaration'},
            {'key': 'office_list', 'name': '事業所一覧', 'endpoint': 'company.office_list'},
        ]
    },
    {
        'key': 'import_data_group',
        'name': '会計データ選択',
        'node_type': 'wizard',
        'children': [
            {'key': 'select_software', 'name': '会計ソフト選択', 'endpoint': 'company.select_software'},
            {'key': 'chart_of_accounts', 'name': '勘定科目データ取込', 'endpoint': 'company.upload_data', 'params': {'datatype': 'chart_of_accounts'}},
            {'key': 'data_mapping', 'name': '勘定科目マッピング', 'endpoint': 'company.data_mapping'},
            {'key': 'journals', 'name': '仕訳帳データ取込', 'endpoint': 'company.upload_data', 'params': {'datatype': 'journals'}},
            {'key': 'fixed_assets', 'name': '固定資産データ取込', 'endpoint': 'company.upload_data', 'params': {'datatype': 'fixed_assets'}},
        ]
    },
    {
        'key': 'statement_of_accounts_group',
        'name': '勘定科目内訳書',
        'node_type': 'menu',
        'children': [
            {'key': 'deposits', 'name': '預貯金等', 'endpoint': 'company.statement_of_accounts', 'params': {'page': 'deposits'}},
            {'key': 'notes_receivable', 'name': '受取手形', 'endpoint': 'company.statement_of_accounts', 'params': {'page': 'notes_receivable'}},
            {'key': 'accounts_receivable', 'name': '売掛金（未収入金）', 'endpoint': 'company.statement_of_accounts', 'params': {'page': 'accounts_receivable'}},
            {'key': 'temporary_payments', 'name': '仮払金（前渡金）', 'endpoint': 'company.statement_of_accounts', 'params': {'page': 'temporary_payments'}},
            {'key': 'loans_receivable', 'name': '貸付金・受取利息', 'endpoint': 'company.statement_of_accounts', 'params': {'page': 'loans_receivable'}},
            {'key': 'inventories', 'name': '棚卸資産', 'endpoint': 'company.statement_of_accounts', 'params': {'page': 'inventories'}},
            {'key': 'securities', 'name': '有価証券', 'endpoint': 'company.statement_of_accounts', 'params': {'page': 'securities'}},
            {'key': 'fixed_assets_soa', 'name': '固定資産（土地等）', 'endpoint': 'company.statement_of_accounts', 'params': {'page': 'fixed_assets'}}, # キーの重複を避ける
            {'key': 'notes_payable', 'name': '支払手形', 'endpoint': 'company.statement_of_accounts', 'params': {'page': 'notes_payable'}},
            {'key': 'accounts_payable', 'name': '買掛金（未払金・未払費用）', 'endpoint': 'company.statement_of_accounts', 'params': {'page': 'accounts_payable'}},
            {'key': 'temporary_receipts', 'name': '仮受金（前受金・預り金）', 'endpoint': 'company.statement_of_accounts', 'params': {'page': 'temporary_receipts'}},
            {'key': 'borrowings', 'name': '借入金及び支払利子', 'endpoint': 'company.statement_of_accounts', 'params': {'page': 'borrowings'}},
            {'key': 'executive_compensations', 'name': '役員給与等', 'endpoint': 'company.statement_of_accounts', 'params': {'page': 'executive_compensations'}},
            {'key': 'land_rents', 'name': '地代家賃等', 'endpoint': 'company.statement_of_accounts', 'params': {'page': 'land_rents'}},
            {'key': 'miscellaneous', 'name': '雑益・雑損失等', 'endpoint': 'company.statement_of_accounts', 'params': {'page': 'miscellaneous'}},
        ]
    },
]

def build_navigation_tree():
    """
    データ定義に基づき、NavigationNodeのツリーを構築して返す
    """
    return [NavigationNode(**data) for data in NAVIGATION_STRUCTURE_DATA]

# アプリケーション起動時に一度だけツリーを構築
navigation_tree = build_navigation_tree()

# app/company/routes.py

from flask import render_template, request, redirect, url_for, Blueprint
from app.company.models import Company
from app import db

# Blueprintを定義。このファイル内のルートは全て /company が先頭に付く
company_bp = Blueprint(
    'company', 
    __name__, 
    template_folder='templates', 
    url_prefix='/company'
)


@company_bp.route('/')
def show():
    """
    基本情報ページのトップ。
    データベースから会社情報を取得し、フォームに表示する。
    GETリクエスト用。
    """
    # データベースから最初の1件の会社情報を取得（将来的にはログインユーザーに紐づく会社）
    company = Company.query.first()
    
    # company/register.html を表示する。取得したcompanyデータを渡す。
    # データがなければ company は None になる。
    return render_template('company/register.html', company=company)


@company_bp.route('/save', methods=['POST'])
def save():
    """
    フォームから送信されたデータを保存（新規登録または更新）する。
    POSTリクエスト用。
    """
    # 既存の会社情報を取得。なければ新規にCompanyオブジェクトを作成。
    company = Company.query.first()
    if not company:
        company = Company()

    # フォームから送信されたデータで、companyオブジェクトの各属性を上書き
    company.corporate_number = request.form.get('corporate_number')
    company.company_name = request.form.get('company_name')
    company.company_name_kana = request.form.get('company_name_kana')
    company.zip_code = request.form.get('zip_code')
    company.prefecture = request.form.get('prefecture')
    company.city = request.form.get('city')
    company.address = request.form.get('address')
    company.phone_number = request.form.get('phone_number')
    company.homepage = request.form.get('homepage')
    company.establishment_date = request.form.get('establishment_date')
    company.fiscal_period_is_one_year = 'fiscal_period_is_one_year' in request.form
    company.capital_limit = 'capital_limit' in request.form
    company.is_supported_industry = 'is_supported_industry' in request.form
    company.is_not_excluded_business = 'is_not_excluded_business' in request.form    
    company.capital_limit = 'capital_limit' in request.form
    company.industry_type = request.form.get('industry_type')
    company.industry_code = request.form.get('industry_code')
    company.reference_number = request.form.get('reference_number')

    # データベースに変更をセッションに追加（新規 or 更新）
    db.session.add(company)
    # 変更をデータベースにコミット（書き込みを確定）
    db.session.commit()

    # 保存後は、基本情報トップページにリダイレクトして結果を表示
    return redirect(url_for('company.show'))
 # app/company/routes.py (一番下に追記)

@company_bp.route('/employees')
def employees():
    """
    社員名簿ページ。
    データベースから社員の一覧を取得して表示する。
    """
    # 会社の情報を取得（将来的にはログインユーザーの会社）
    company = Company.query.first()
    
    # 会社に紐づく社員のリストを取得
    employee_list = []
    if company:
        employee_list = company.employees

    return render_template(
        'company/employee_list.html', 
        employees=employee_list
    )   
# app/company/routes.py (一番下に追記)

@company_bp.route('/declaration', methods=['GET', 'POST'])
def declaration():
    """
    GET: 申告情報ページを表示
    POST: 入力された申告情報を保存
    """
    company = Company.query.first()
    if not company:
        # 会社情報が未登録の場合は、まず基本情報登録へ
        return redirect(url_for('company.show'))

    if request.method == 'POST':
        # --- 保存処理 ---
        # (この部分は後で実装します)
        pass 
    
    return render_template('company/declaration_form.html', company=company)    
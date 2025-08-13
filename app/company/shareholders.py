# app/company/shareholders.py
from flask import render_template, request, redirect, url_for, flash
from app.company import company_bp
from app.company.forms import MainShareholderForm, RelatedShareholderForm
from app.company.utils import get_officer_choices
from app.company.services import shareholder_service, company_classification_service
from app.navigation import get_navigation_state
from .auth import company_required

def get_page_title_and_check_redirect(company_name):
    """法人名に応じて動的なページタイトルを決定し、リダイレクトが必要か判定する"""
    if '株式会社' in company_name or '有限会社' in company_name:
        return '株主情報', None
    elif any(corp_type in company_name for corp_type in ['合同会社', '合名会社', '合資会社']):
        return '社員情報', None
    else:
        return None, redirect(url_for('company.declaration'))

@company_bp.route('/shareholders')
@company_required
def shareholders(company):
    """株主/社員情報の一覧ページ"""
    page_title, response = get_page_title_and_check_redirect(company.company_name)
    if response:
        return response
    
    shareholder_list = shareholder_service.get_shareholders_by_company(company.id)
    classification_result = company_classification_service.classify_company(company.id)
    navigation_state = get_navigation_state('shareholders')
    
    return render_template(
        'company/shareholder_list.html', 
        shareholders=shareholder_list, 
        classification_result=classification_result,
        navigation_state=navigation_state,
        page_title=page_title
    )

@company_bp.route('/shareholder/register/main', methods=['GET', 'POST'])
@company_required
def register_main_shareholder(company):
    """主たる株主の新規登録"""
    page_title, response = get_page_title_and_check_redirect(company.company_name)
    if response:
        return response

    

    form = MainShareholderForm(request.form)
    form.officer_position.choices = get_officer_choices(page_title)

    if form.validate_on_submit():
        new_shareholder, error = shareholder_service.add_main_shareholder(company.id, form)
        if error:
            flash(error, 'warning')
            return redirect(url_for('company.shareholders'))
        
        return redirect(url_for('company.confirm_related_shareholder', main_shareholder_id=new_shareholder.id, is_new_group=True))
    
    main_shareholders = shareholder_service.get_main_shareholders(company.id)
    group_number = len(main_shareholders) + 1
    navigation_state = get_navigation_state('shareholders')
    
    return render_template(
        'company/register_shareholder.html', 
        form=form, 
        navigation_state=navigation_state,
        page_title=page_title,
        group_number=group_number
    )

@company_bp.route('/shareholder/register/related/<int:main_shareholder_id>', methods=['GET', 'POST'])
@company_required
def register_related_shareholder(company, main_shareholder_id):
    """特殊関係人の新規登録"""
    page_title, response = get_page_title_and_check_redirect(company.company_name)
    if response:
        return response
        
    main_shareholder = shareholder_service.get_shareholder_by_id(main_shareholder_id)
    related_shareholders = shareholder_service.get_related_shareholders(main_shareholder_id)

    form = RelatedShareholderForm(request.form)
    form.officer_position.choices = get_officer_choices(page_title)

    if form.validate_on_submit():
        shareholder_service.add_related_shareholder(company.id, main_shareholder_id, form)
        return redirect(url_for('company.confirm_related_shareholder', main_shareholder_id=main_shareholder_id))

    main_shareholders = shareholder_service.get_main_shareholders(company.id)
    group_number = -1
    for i, shareholder in enumerate(main_shareholders):
        if shareholder.id == main_shareholder_id:
            group_number = i + 1
            break

    navigation_state = get_navigation_state('shareholders')
    return render_template(
        'company/register_related_shareholder.html', 
        form=form, 
        navigation_state=navigation_state,
        page_title=page_title,
        main_shareholder=main_shareholder,
        related_shareholders=related_shareholders,
        group_number=group_number
    )

@company_bp.route('/shareholder/edit/<int:shareholder_id>', methods=['GET', 'POST'])
@company_required
def edit_shareholder(company, shareholder_id):
    """株主情報の編集"""
    page_title, response = get_page_title_and_check_redirect(company.company_name)
    if response:
        return response

    # サービス層でテナントチェックが行われるため、ここでのcompany_idチェックは不要
    shareholder = shareholder_service.get_shareholder_by_id(shareholder_id)
    
    form_class = MainShareholderForm if shareholder.parent_id is None else RelatedShareholderForm
    form = form_class(request.form, obj=shareholder)
    form.officer_position.choices = get_officer_choices(page_title)

    if form.validate_on_submit():
        # サービス層のupdate_shareholderは引数としてcompany.idを不要とする
        shareholder_service.update_shareholder(shareholder_id, form)
        flash(f'{page_title}を更新しました。', 'success')
        return redirect(url_for('company.shareholders'))

    template = 'company/edit_shareholder.html'
    if shareholder.parent_id is not None:
        template = 'company/edit_related_shareholder.html'

    return render_template(
        template,
        form=form,
        shareholder=shareholder,
        page_title=page_title
    )

@company_bp.route('/shareholder/delete/<int:shareholder_id>', methods=['POST'])
@company_required
def delete_shareholder(company, shareholder_id):
    """株主/社員の削除"""
    page_title, _ = get_page_title_and_check_redirect(company.company_name)
    # サービス層のdelete_shareholderは引数としてcompany.idを不要とする
    shareholder_service.delete_shareholder(shareholder_id)
    flash(f'{page_title}を削除しました。', 'success')
    return redirect(url_for('company.shareholders'))

@company_bp.route('/shareholder/confirm/related/<int:main_shareholder_id>')
@company_required
def confirm_related_shareholder(company, main_shareholder_id):
    """【中間ページ】特殊関係人の登録意思を確認する"""
    main_shareholder = shareholder_service.get_shareholder_by_id(main_shareholder_id)
    if main_shareholder.company_id != company.id:
        flash('権限がありません。', 'danger')
        return redirect(url_for('company.shareholders'))

    is_new_group = request.args.get('is_new_group', default=False, type=bool)
    if is_new_group:
        title = "登録が完了しました"
        message = f"{main_shareholder.last_name} 様の株式情報を登録しました。<br>{main_shareholder.last_name}様のご家族・ご親族などの特殊関係人で株式をお持ちの方はいらっしゃいますか？"
    else:
        title = "特殊関係人を登録しました"
        message = f"その他に、{main_shareholder.last_name} 様のご家族・ご親族などの特殊関係人で株式をお持ちの方はいらっしゃいますか？"

    return render_template(
        'company/confirm_related_shareholder.html',
        main_shareholder=main_shareholder,
        title=title,
        message=message
    )

@company_bp.route('/shareholder/confirm/next_main/')
@company_required
def confirm_next_main_shareholder(company):
    """【中間ページ3】次の主たる株主グループの登録意思を確認する"""
    main_shareholders = shareholder_service.get_main_shareholders(company.id)
    return render_template(
        'company/next_main_shareholder.html',
        main_shareholders=main_shareholders
    )
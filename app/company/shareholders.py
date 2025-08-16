# app/company/shareholders.py
from flask import render_template, request, redirect, url_for, flash
from app.company import company_bp
from app.company.forms import MainShareholderForm, RelatedShareholderForm
from app.company.models import Shareholder
from app.company.utils import get_officer_choices, set_page_title_and_verify_company_type
from app.company.services import shareholder_service, company_classification_service
from app.navigation import get_navigation_state
from .auth import company_required

@company_bp.route('/shareholders')
@company_required
@set_page_title_and_verify_company_type
def shareholders(company, page_title):
    """株主/社員情報の一覧ページ"""
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
@set_page_title_and_verify_company_type
def register_main_shareholder(company, page_title):
    """主たる株主の新規登録"""
    form = MainShareholderForm(request.form)
    form.officer_position.choices = get_officer_choices(page_title)

    if form.validate_on_submit():
        new_shareholder, error = shareholder_service.add_shareholder(company.id, form)
        if error:
            flash(error, 'warning')
            return redirect(url_for('company.shareholders'))
        
        return redirect(url_for('company.confirm_related_shareholder', main_shareholder_id=new_shareholder.id, is_new_group=True))
    
    main_shareholders = shareholder_service.get_main_shareholders(company.id)
    group_number = len(main_shareholders) + 1
    navigation_state = get_navigation_state('shareholders')
    
    # 新規登録用に空のオブジェクトを渡す
    shareholder = Shareholder()

    return render_template(
        'company/shareholder_form.html', 
        form=form, 
        shareholder=shareholder,
        navigation_state=navigation_state,
        page_title=page_title,
        group_number=group_number
    )

@company_bp.route('/shareholder/register/related/<int:main_shareholder_id>', methods=['GET', 'POST'])
@company_required
@set_page_title_and_verify_company_type
def register_related_shareholder(company, main_shareholder_id, page_title):
    """特殊関係人の新規登録"""
    main_shareholder = shareholder_service.get_shareholder_by_id(main_shareholder_id)
    form = RelatedShareholderForm(request.form)
    form.officer_position.choices = get_officer_choices(page_title)

    if form.validate_on_submit():
        new_shareholder, error = shareholder_service.add_shareholder(company.id, form, parent_id=main_shareholder_id)
        if error:
            flash(error, 'warning')
            return redirect(url_for('company.shareholders'))
        return redirect(url_for('company.confirm_related_shareholder', main_shareholder_id=main_shareholder_id))

    # 新規登録用に空のオブジェクトを作成し、親を設定
    shareholder = Shareholder(parent_id=main_shareholder_id, parent=main_shareholder)
    
    group_number = shareholder_service.get_main_shareholder_group_number(company.id, main_shareholder_id)
    navigation_state = get_navigation_state('shareholders')
    
    return render_template(
        'company/shareholder_form.html', 
        form=form, 
        shareholder=shareholder,
        navigation_state=navigation_state,
        page_title=page_title,
        group_number=group_number
    )

@company_bp.route('/shareholder/edit/<int:shareholder_id>', methods=['GET', 'POST'])
@company_required
@set_page_title_and_verify_company_type
def edit_shareholder(company, shareholder_id, page_title):
    """株主情報の編集"""
    shareholder = shareholder_service.get_shareholder_by_id(shareholder_id)
    form_class = shareholder_service.get_shareholder_form(shareholder)
    template = 'company/shareholder_form.html'
    
    form = form_class(request.form, obj=shareholder)
    form.officer_position.choices = get_officer_choices(page_title)

    if form.validate_on_submit():
        shareholder_service.update_shareholder(shareholder_id, form)
        flash(f'{page_title}を更新しました。', 'success')
        return redirect(url_for('company.shareholders'))

    return render_template(
        template,
        form=form,
        shareholder=shareholder,
        page_title=page_title
    )

@company_bp.route('/shareholder/delete/<int:shareholder_id>', methods=['POST'])
@company_required
@set_page_title_and_verify_company_type
def delete_shareholder(company, shareholder_id, page_title):
    """株主/社員の削除"""
    shareholder_service.delete_shareholder(shareholder_id)
    flash(f'{page_title}を削除しました。', 'success')
    return redirect(url_for('company.shareholders'))

@company_bp.route('/shareholder/confirm/related/<int:main_shareholder_id>')
@company_required
@set_page_title_and_verify_company_type
def confirm_related_shareholder(company, main_shareholder_id, page_title):
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
        message=message,
        page_title=page_title
    )

@company_bp.route('/shareholder/confirm/next_main/')
@company_required
@set_page_title_and_verify_company_type
def confirm_next_main_shareholder(company, page_title):
    """【中間ページ3】次の主たる株主グループの登録意思を確認する"""
    main_shareholders = shareholder_service.get_main_shareholders(company.id)
    return render_template(
        'company/next_main_shareholder.html',
        main_shareholders=main_shareholders,
        page_title=page_title
    )

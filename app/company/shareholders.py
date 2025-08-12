# app/company/shareholders.py
from flask import render_template, request, redirect, url_for, flash
from app.company import company_bp
from app.company.models import Shareholder, Company
from app.company.forms import MainShareholderForm, RelatedShareholderForm
from app import db
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
    
    shareholder_list = Shareholder.query.filter_by(company_id=company.id).order_by(Shareholder.id).all()
    navigation_state = get_navigation_state('shareholders')
    return render_template(
        'company/shareholder_list.html', 
        shareholders=shareholder_list, 
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
    
    if page_title == '株主情報':
        form.officer_position.choices = [('代表取締役', '代表取締役'), ('取締役', '取締役'), ('会計参与', '会計参与'), ('監査役', '監査役'), ('その他', 'その他')]
    elif page_title == '社員情報':
        form.officer_position.choices = [('代表社員', '代表社員'), ('業務執行社員', '業務執行社員'), ('有限責任社員', '有限責任社員'), ('無限責任社員', '無限責任社員'), ('その他', 'その他')]

    if form.validate_on_submit():
        new_shareholder = Shareholder()
        form.populate_obj(new_shareholder)
        new_shareholder.company_id = company.id
        db.session.add(new_shareholder)
        db.session.commit()
        return redirect(url_for('company.confirm_related_shareholder', main_shareholder_id=new_shareholder.id))
    
    main_shareholders = Shareholder.query.filter_by(company_id=company.id, parent_id=None).order_by(Shareholder.id).all()
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
        
    main_shareholder = Shareholder.query.get_or_404(main_shareholder_id)
    related_shareholders = Shareholder.query.filter_by(parent_id=main_shareholder_id).all()

    form = RelatedShareholderForm(request.form)

    if page_title == '株主情報':
        form.officer_position.choices = [('代表取締役', '代表取締役'), ('取締役', '取締役'), ('会計参与', '会計参与'), ('監査役', '監査役'), ('その他', 'その他')]
    elif page_title == '社員情報':
        form.officer_position.choices = [('代表社員', '代表社員'), ('業務執行社員', '業務執行社員'), ('有限責任社員', '有限責任社員'), ('無限責任社員', '無限責任社員'), ('その他', 'その他')]

    if form.validate_on_submit():
        new_related_shareholder = Shareholder(
            company_id=company.id,
            parent_id=main_shareholder_id,
            last_name=form.last_name.data,
            relationship=form.relationship.data,
            officer_position=form.officer_position.data,
            investment_amount=form.investment_amount.data,
            shares_held=form.shares_held.data,
            voting_rights=form.voting_rights.data,
            is_controlled_company=form.is_controlled_company.data
        )
        
        if form.is_address_same_as_main.data:
            new_related_shareholder.zip_code = main_shareholder.zip_code
            new_related_shareholder.prefecture_city = main_shareholder.prefecture_city
            new_related_shareholder.address = main_shareholder.address
        else:
            new_related_shareholder.zip_code = form.zip_code.data
            new_related_shareholder.prefecture_city = form.prefecture_city.data
            new_related_shareholder.address = form.address.data

        db.session.add(new_related_shareholder)
        db.session.commit()
        return redirect(url_for('company.confirm_related_shareholder_again', main_shareholder_id=main_shareholder_id))

    main_shareholders = Shareholder.query.filter_by(company_id=company.id, parent_id=None).order_by(Shareholder.id).all()
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

    shareholder = Shareholder.query.get_or_404(shareholder_id)
    
    if shareholder.parent_id is None:
        # 主たる株主の編集
        form = MainShareholderForm(obj=shareholder)
    else:
        # 特殊関係人の編集
        form = RelatedShareholderForm(obj=shareholder)

    if page_title == '株主情報':
        form.officer_position.choices = [('代表取締役', '代表取締役'), ('取締役', '取締役'), ('会計参与', '会計参与'), ('監査役', '監査役'), ('その他', 'その他')]
    elif page_title == '社員情報':
        form.officer_position.choices = [('代表社員', '代表社員'), ('業務執行社員', '業務執行社員'), ('有限責任社員', '有限責任社員'), ('無限責任社員', '無限責任社員'), ('その他', 'その他')]

    if form.validate_on_submit():
        form.populate_obj(shareholder)
        db.session.commit()
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
    page_title, response = get_page_title_and_check_redirect(company.company_name)
    if response:
        return redirect(url_for('company.shareholders'))

    shareholder = Shareholder.query.filter_by(id=shareholder_id, company_id=company.id).first_or_404()
    db.session.delete(shareholder)
    db.session.commit()
    flash(f'{page_title}を削除しました。', 'success')
    return redirect(url_for('company.shareholders'))

@company_bp.route('/shareholder/confirm/related/<int:main_shareholder_id>')
@company_required
def confirm_related_shareholder(company, main_shareholder_id):
    """【中間ページ1】特殊関係人の登録意思を確認する"""
    main_shareholder = Shareholder.query.get_or_404(main_shareholder_id)
    return render_template(
        'company/confirm_related_shareholder.html',
        main_shareholder=main_shareholder
    )

@company_bp.route('/shareholder/confirm/related_again/<int:main_shareholder_id>')
@company_required
def confirm_related_shareholder_again(company, main_shareholder_id):
    """【中間ページ2】さらに特殊関係人を登録する意思を確認する"""
    main_shareholder = Shareholder.query.get_or_404(main_shareholder_id)
    return render_template(
        'company/confirm_related_shareholder2.html',
        main_shareholder=main_shareholder
    )

@company_bp.route('/shareholder/confirm/next_main/')
@company_required
def confirm_next_main_shareholder(company):
    """【中間ページ3】次の主たる株主グループの登録意思を確認する"""
    main_shareholders = Shareholder.query.filter_by(company_id=company.id, parent_id=None).all()
    return render_template(
        'company/next_main_shareholder.html',
        main_shareholders=main_shareholders
    )
# app/company/shareholders.py
import os
from datetime import datetime

from flask import (
    current_app,
    flash,
    redirect,
    render_template,
    request,
    send_file,
    url_for,
)

import app.company.services.company_classification_service as company_classification_service
from app.company import company_bp
from app.company.forms import MainShareholderForm, RelatedShareholderForm
from app.company.models import Shareholder
from app.company.services.protocols import ShareholderServiceProtocol
from app.company.services.shareholder_service import (
    get_shareholder_service_for,
    shareholder_service,
)
from app.company.utils import (
    get_officer_choices,
    set_page_title_and_verify_company_type,
)
from app.navigation import get_navigation_state
from app.pdf.beppyou_02 import generate_beppyou_02

from .auth import company_required

_shareholders: ShareholderServiceProtocol = shareholder_service


def _shareholders_with_scope(company):
    service, user_id = get_shareholder_service_for(company)
    return service, user_id

@company_bp.route('/shareholders')
@company_required
@set_page_title_and_verify_company_type
def shareholders(company, page_title):
    """株主/社員情報の一覧ページ"""
    service, user_id = _shareholders_with_scope(company)
    shareholder_list = service.get_shareholders_by_company(company.id, user_id=user_id)
    # 主たる株主（親がいない）を先に計算してテンプレートへ安全に引き渡す
    main_shareholders = [s for s in shareholder_list if s.parent_id is None]
    raw_totals_map = service.compute_group_totals_both_map(company.id, user_id=user_id)
    group_totals_both_map = {
        key: {
            'shares_held': vals.get('sum_shares', 0),
            'voting_rights': vals.get('sum_votes', 0),
        }
        for key, vals in raw_totals_map.items()
    }
    classification_result = company_classification_service.classify_company(company.id)
    navigation_state = get_navigation_state('shareholders')
    
    return render_template(
        'company/shareholder_list.html', 
        shareholders=shareholder_list, 
        main_shareholders=main_shareholders,
        classification_result=classification_result,
        navigation_state=navigation_state,
        page_title=page_title,
        group_totals_both_map=group_totals_both_map
    )

@company_bp.route('/shareholder/register/main', methods=['GET', 'POST'])
@company_required
@set_page_title_and_verify_company_type
def register_main_shareholder(company, page_title):
    """主たる株主の新規登録"""
    service, user_id = _shareholders_with_scope(company)
    form = MainShareholderForm(request.form)
    form.officer_position.choices = get_officer_choices(page_title)

    if form.validate_on_submit():
        new_shareholder, error = service.add_shareholder(company.id, form, user_id=user_id)
        if error:
            flash(error, 'warning')
            return redirect(url_for('company.shareholders'))
        
        return redirect(url_for('company.confirm_related_shareholder', main_shareholder_id=new_shareholder.id, is_new_group=True))
    
    main_shareholders = service.get_main_shareholders(company.id, user_id=user_id)
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
    service, user_id = _shareholders_with_scope(company)
    main_shareholder = service.get_shareholder_by_id(main_shareholder_id, user_id=user_id)
    form = RelatedShareholderForm(request.form)
    form.officer_position.choices = get_officer_choices(page_title)

    if form.validate_on_submit():
        new_shareholder, error = service.add_shareholder(company.id, form, parent_id=main_shareholder_id, user_id=user_id)
        if error:
            flash(error, 'warning')
            return redirect(url_for('company.shareholders'))
        return redirect(url_for('company.confirm_related_shareholder', main_shareholder_id=main_shareholder_id))

    # 新規登録用に空のオブジェクトを作成し、親を設定
    shareholder = Shareholder(parent_id=main_shareholder_id, parent=main_shareholder)
    
    group_number = service.get_main_shareholder_group_number(company.id, main_shareholder_id, user_id=user_id)
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
    service, user_id = _shareholders_with_scope(company)
    shareholder = service.get_shareholder_by_id(shareholder_id, user_id=user_id)
    form_class = service.get_shareholder_form(shareholder)
    template = 'company/shareholder_form.html'
    
    form = form_class(request.form, obj=shareholder)
    form.officer_position.choices = get_officer_choices(page_title)

    # UX: 特殊関係人の編集画面で、主たる株主と住所が同一ならチェック状態を初期表示で反映する
    if request.method == 'GET' and shareholder.parent_id is not None and hasattr(form, 'is_address_same_as_main'):
        # サービス層の共通ロジックで住所一致を判定（単一情報源化）
        same = service.is_same_address(shareholder, shareholder.parent) if shareholder.parent is not None else False
        form.is_address_same_as_main.data = same

    if form.validate_on_submit():
        service.update_shareholder(shareholder_id, form, user_id=user_id)
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
    service, user_id = _shareholders_with_scope(company)
    service.delete_shareholder(shareholder_id, user_id=user_id)
    flash(f'{page_title}を削除しました。', 'success')
    return redirect(url_for('company.shareholders'))

@company_bp.route('/shareholder/confirm/related/<int:main_shareholder_id>')
@company_required
@set_page_title_and_verify_company_type
def confirm_related_shareholder(company, main_shareholder_id, page_title):
    """【中間ページ】特殊関係人の登録意思を確認する"""
    service, user_id = _shareholders_with_scope(company)
    main_shareholder = service.get_shareholder_by_id(main_shareholder_id, user_id=user_id)
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
    service, user_id = _shareholders_with_scope(company)
    main_shareholders = service.get_main_shareholders(company.id, user_id=user_id)
    return render_template(
        'company/next_main_shareholder.html',
        main_shareholders=main_shareholders,
        page_title=page_title
    )


@company_bp.route('/shareholders/pdf/beppyou_02')
@company_required
def shareholders_pdf_beppyou_02(company):
    """別表二（beppyou_02）を生成し、ブラウザで表示（印刷可）する。"""
    year = request.args.get('year', '2025')
    base_dir = os.path.abspath(os.path.join(current_app.root_path, '..'))
    filled_dir = os.path.join(base_dir, 'temporary', 'filled')
    os.makedirs(filled_dir, exist_ok=True)
    ts = datetime.now().strftime('%Y%m%d%H%M%S')
    out_path = os.path.join(filled_dir, f"beppyou_02_{company.id}_{ts}.pdf")
    generate_beppyou_02(company_id=company.id, year=year, output_path=out_path)
    return send_file(
        out_path,
        mimetype='application/pdf',
        as_attachment=False,
        download_name=f"beppyou_02_{year}.pdf"
    )

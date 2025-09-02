from typing import Optional, List
from typing import Optional, List
import os

from flask import has_request_context, current_app, request
from app import db
from app.company.models import Company, Borrowing

from .pdf_fill import overlay_pdf, TextSpec
from .layout_utils import load_geometry
from .fonts import default_font_map, ensure_font_registered
from app.utils import format_number


def _fmt(n: Optional[int]) -> str:
    return format_number(n)


def generate_borrowings_two_tier(company_id: Optional[int], year: str = "2025", *, output_path: str) -> str:
    """
    借入金及び支払利子（上下二段）PDFを生成します。
    - 上段: 借入金合計（B/S）
    - 下段: 支払利子合計（P/L）
    片側にデータが無い場合は、その側は何も印字しません（枠のみ）。
    """
    # company解決
    if company_id is None:
        if not has_request_context():
            raise RuntimeError("company_id is required outside a request context")
        company = Company.query.filter_by(user_id=current_app.login_manager._load_user().id).first()
        if not company:
            raise RuntimeError("company not found for current user")
        company_id = company.id

    # リソース解決（年度は固定のダミーを渡し、常に最新年へフォールバック）
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    latest_year_hint = '2099'
    # base PDF: 専用テンプレが無い場合は仮払金・貸付金のベースを流用
    borrow_forms_dir = os.path.join(repo_root, 'resources/pdf_forms/borrowings_two_tier')
    if os.path.isdir(borrow_forms_dir):
        base_pdf = os.path.join(borrow_forms_dir, latest_year_hint, 'source.pdf')
    else:
        base_pdf = os.path.join(repo_root, f"resources/pdf_forms/uchiwakesyo_karibaraikin-kashitukekin/{latest_year_hint}/source.pdf")
    font_map = default_font_map(repo_root)
    try:
        ensure_font_registered("NotoSansJP", font_map["NotoSansJP"])  # best-effort
    except Exception:
        pass

    # ジオメトリ（無くても進行: required=False）。専用テンプレが無ければ空dictで進行
    borrow_geom_dir = os.path.join(repo_root, 'resources/pdf_templates/borrowings_two_tier')
    if os.path.isdir(borrow_geom_dir):
        geom = load_geometry("borrowings_two_tier", latest_year_hint, repo_root=repo_root, required=False, validate=False) or {}
    else:
        geom = {}
    geom = load_geometry("borrowings_two_tier", year, repo_root=repo_root, required=False, validate=False) or {}

    # 位置（無い場合は簡易デフォルト座標）
    up = geom.get('upper_total', {'x': 430.0, 'y': 740.0, 'w': 100.0, 'size': 12.0})
    lo = geom.get('lower_total', {'x': 430.0, 'y': 360.0, 'w': 100.0, 'size': 12.0})
    right_margin = float(geom.get('margins', {}).get('right_margin', 0.0))

    # 集計
    q = db.session.query
    bs_total = q(db.func.sum(Borrowing.balance_at_eoy)).filter_by(company_id=company_id).scalar() or 0
    pl_total = q(db.func.sum(Borrowing.paid_interest)).filter_by(company_id=company_id).scalar() or 0

    texts: List[TextSpec] = []
    # 上段（借入金合計）
    if bs_total and bs_total != 0:
        texts.append(TextSpec(
            page=0,
            x=float(lo['x']) + float(lo['w']) - float(right_margin),
            y=float(lo['y']) - float(lo['size'])/2.0,
            text=_fmt(int(pl_total)), font_name="NotoSansJP", font_size=float(lo['size']), align='right'
        ))

    # デバッグ矩形等は不要。最小の印字のみ。

    # base_pdf が無い年は、overlay_pdf が内部のフォールバック（開発用白紙ベース）で進行可能
    try:
        if has_request_context() and request.args.get('dbg_pdf') == '1':
            current_app.logger.info(f"[borrowings] totals: bs={bs_total}, pl={pl_total}")
    except Exception:
        pass

    return overlay_pdf(base_pdf_path=base_pdf, output_pdf_path=output_path, texts=texts, rectangles=[])


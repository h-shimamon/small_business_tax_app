# app/commands.py
import click
from flask.cli import with_appcontext
from app.company.services.master_data_service import MasterDataService
from app import db
from app.company.models import User

def register_commands(app):
    """アプリケーションにCLIコマンドを登録する"""
    app.cli.add_command(init_db_command)
    app.cli.add_command(seed_masters_command)
    app.cli.add_command(report_date_health_command)
    app.cli.add_command(seed_soa_command)
    try:
        env = app.config.get('ENV')
    except Exception:
        env = None
    if not (env and str(env).lower() == 'production'):
        app.cli.add_command(delete_seeded_command)
    app.cli.add_command(seed_notes_receivable_command)

@click.command('init-db')
@with_appcontext
def init_db_command():
    """
    データベースに初期データ（管理者ユーザーなど）を投入します。
    テーブルは `flask db upgrade` で先に作成しておく必要があります。
    """
    click.echo("データベースの初期データ投入を開始します...")
    try:
        # 既存のadminユーザーを検索し、存在すれば削除
        admin_user = User.query.filter_by(username='admin').first()
        if admin_user:
            db.session.delete(admin_user)
            db.session.commit()
            click.echo("既存の管理者ユーザーを削除しました。")

        from datetime import date
        from app.company.models import Company

        # 管理者ユーザー作成
        admin_user = User(username='admin')
        admin_user.set_password('password')
        db.session.add(admin_user)
        db.session.commit()
        click.echo("管理者ユーザーを作成しました。")

        # ダミーの会社情報を作成し、管理者ユーザーに紐付ける
        dummy_company = Company(
            corporate_number="1111111111111",
            company_name="（ダミー）株式会社 Gemini",
            company_name_kana="ダミー カブシキガイシャジェミニ",
            zip_code="1066126",
            prefecture="東京都",
            city="港区",
            address="六本木6-10-1 六本木ヒルズ森タワー",
            phone_number="03-6384-9000",
            establishment_date=date(2023, 1, 1),
            user_id=admin_user.id
        )
        db.session.add(dummy_company)
        db.session.commit()
        click.echo("管理者ユーザー用のダミー会社情報を作成しました。")

        # マスターデータの同期
        service = MasterDataService()
        service.check_and_sync()
        click.echo("マスターデータの同期を確認しました。")
        click.echo("初期データの投入が完了しました。")
    except Exception as e:
        click.echo(f'エラー: 初期データ投入中に問題が発生しました: {e}')
        # エラーの詳細を出力
        import traceback
        traceback.print_exc()


@click.command('seed-masters')
@with_appcontext
def seed_masters_command():
    """
    勘定科目マスターデータをCSVファイルからデータベースに強制的に再登録します。
    """
    click.echo('マスターデータの強制同期を開始します...')
    try:
        service = MasterDataService()
        service.force_sync()
        click.echo('マスターデータの同期が正常に完了しました。')
    except Exception as e:
        click.echo(f'エラー: マスターデータの同期中に問題が発生しました: {e}')


def _safe_parse_iso(text):
    """Return date from 'YYYY-MM-DD' (string) or None if invalid."""
    if not text:
        return None
    try:
        from datetime import date
        # strict length and separators, defensive against non-strings
        s = str(text)
        if len(s) != 10 or s[4] != '-' or s[7] != '-':
            return None
        y, m, d = int(s[0:4]), int(s[5:7]), int(s[8:10])
        return date(y, m, d)
    except Exception:
        return None


def _pair_metrics(rows, str_key, date_key):
    total = len(rows)
    str_vals = [r.get(str_key) for r in rows]
    date_vals = [r.get(date_key) for r in rows]
    def _is_empty_str(v):
        try:
            return (v is None) or (str(v).strip() == "")
        except Exception:
            return True
    str_null = sum(1 for v in str_vals if _is_empty_str(v))
    date_null = sum(1 for v in date_vals if v is None)
    both_set = sum(1 for s, d in zip(str_vals, date_vals) if not _is_empty_str(s) and d is not None)
    str_only = sum(1 for s, d in zip(str_vals, date_vals) if not _is_empty_str(s) and d is None)
    date_only = sum(1 for s, d in zip(str_vals, date_vals) if _is_empty_str(s) and d is not None)
    mismatch = 0
    for s, d in zip(str_vals, date_vals):
        if _is_empty_str(s) or d is None:
            continue
        ps = _safe_parse_iso(s)
        if ps != d:
            mismatch += 1
    return {
        'total': total,
        'str_null': str_null,
        'date_null': date_null,
        'both_set': both_set,
        'str_only': str_only,
        'date_only': date_only,
        'mismatch': mismatch,
    }


def _emit_pair_report(title, metrics):
    click.echo(f"\n[{title}]")
    click.echo(f"  total:         {metrics['total']}")
    click.echo(f"  str_null:      {metrics['str_null']}")
    click.echo(f"  date_null:     {metrics['date_null']}")
    click.echo(f"  both_set:      {metrics['both_set']}")
    click.echo(f"  str_only:      {metrics['str_only']}")
    click.echo(f"  date_only:     {metrics['date_only']}")
    click.echo(f"  mismatch:      {metrics['mismatch']}")


@click.command('report-date-health')
@with_appcontext
@click.option('--format', 'fmt', type=click.Choice(['text', 'json', 'csv']), default='text', help='出力形式（text/json/csv）')
def report_date_health_command(fmt):
    """Date/String(10) 同期の健全性レポートを出力します（UI非変更）。"""
    from app.company.models import Company, NotesReceivable
    if fmt == 'text':
        click.echo("Date/String(10) 健全性レポート")
    # Company
    try:
        company_rows = [
            {
                'accounting_period_start': c.accounting_period_start,
                'accounting_period_start_date': c.accounting_period_start_date,
                'accounting_period_end': c.accounting_period_end,
                'accounting_period_end_date': c.accounting_period_end_date,
                'closing_date': c.closing_date,
                'closing_date_date': c.closing_date_date,
            }
            for c in Company.query.all()
        ]
        m_aps = _pair_metrics(company_rows, 'accounting_period_start', 'accounting_period_start_date')
        m_ape = _pair_metrics(company_rows, 'accounting_period_end', 'accounting_period_end_date')
        m_clo = _pair_metrics(company_rows, 'closing_date', 'closing_date_date')
    except Exception as e:
        if fmt == 'text':
            click.echo(f"Company集計でエラー: {e}")
        m_aps = m_ape = m_clo = None

    # NotesReceivable
    try:
        nr_rows = [
            {
                'issue_date': n.issue_date,
                'issue_date_date': n.issue_date_date,
                'due_date': n.due_date,
                'due_date_date': n.due_date_date,
            }
            for n in NotesReceivable.query.all()
        ]
        m_nri = _pair_metrics(nr_rows, 'issue_date', 'issue_date_date')
        m_nrd = _pair_metrics(nr_rows, 'due_date', 'due_date_date')
    except Exception as e:
        if fmt == 'text':
            click.echo(f"NotesReceivable集計でエラー: {e}")
        m_nri = m_nrd = None

    # Output
    sections = [
        ('Company.accounting_period_start', m_aps),
        ('Company.accounting_period_end', m_ape),
        ('Company.closing_date', m_clo),
        ('NotesReceivable.issue_date', m_nri),
        ('NotesReceivable.due_date', m_nrd),
    ]
    if fmt == 'text':
        for title, metrics in sections:
            if metrics is not None:
                _emit_pair_report(title, metrics)
        click.echo("\n完了。必要ならCSV/JSON出力も追加可能です。")
    elif fmt == 'json':
        import json
        out = {title: metrics for title, metrics in sections if metrics is not None}
        click.echo(json.dumps(out, ensure_ascii=False, indent=2))
    elif fmt == 'csv':
        headers = ['section', 'total', 'str_null', 'date_null', 'both_set', 'str_only', 'date_only', 'mismatch']
        click.echo(','.join(headers))
        def _row(title, m):
            return f"{title},{m['total']},{m['str_null']},{m['date_null']},{m['both_set']},{m['str_only']},{m['date_only']},{m['mismatch']}"
        for title, m in sections:
            if m is not None:
                click.echo(_row(title, m))


@click.command('seed-soa')
@with_appcontext
@click.option('--page', required=True, help='対象ページキー（例: notes_receivable）')
@click.option('--company-id', type=int, default=None, help='対象会社ID（未指定時は単一会社がある場合それを使用）')
@click.option('--count', type=int, default=23, show_default=True, help='生成件数')
@click.option('--prefix', type=str, default='', show_default=True, help='名称/摘要に付与する識別用プレフィクス')
def seed_soa_command(page: str, company_id: int | None, count: int, prefix: str):
    """汎用 勘定科目内訳（SoA）ダミーデータ投入CLI。

    例: flask seed-soa --page notes_receivable --count 23
    """
    try:
        from app.cli.seed_soas import run_seed
        created = run_seed(page=page, company_id=company_id, count=count, prefix=prefix)
        click.echo(f"page='{page}' に {created} 件投入しました。")
    except KeyError as e:
        click.echo(str(e))
    except Exception as e:
        click.echo(f"エラー: ダミーデータ投入中に問題が発生しました: {e}")


@click.command('delete-seeded')
@with_appcontext
@click.option('--page', required=True, help='対象ページキー（例: notes_receivable）')
@click.option('--company-id', type=int, required=True, help='対象会社ID（必須）')
@click.option('--prefix', type=str, required=True, help='生成時に付与した識別用プレフィクス（必須）')
@click.option('--execute', is_flag=True, default=False, help='実際に削除を実行（指定がない場合はドライラン）')
def delete_seeded_command(page: str, company_id: int, prefix: str, execute: bool):
    """プレフィクス一致のダミーデータを一括削除（dev/staging専用）。

    デフォルトはドライラン（件数とID一覧のみ表示）。--execute 指定時のみ削除を実行します。
    本番環境（ENV=production）では register されません。
    """
    from app.cli.seed_soas import run_delete
    try:
        count, ids = run_delete(page=page, company_id=company_id, prefix=prefix, dry_run=(not execute))
        mode = '削除実行' if execute else 'ドライラン'
        click.echo(f"[{mode}] page='{page}' company_id={company_id} prefix='{prefix}' 対象件数={count}")
        preview = ids[:10]
        if preview:
            click.echo(f"先頭IDプレビュー: {preview}{' ...' if len(ids) > 10 else ''}")
        if execute:
            click.echo(f"削除完了: {count} 件")
        else:
            click.echo("--execute を付けると削除を実行します（dev/staging専用）")
    except Exception as e:
        click.echo(f"エラー: {e}")


@click.command('seed-soa')
@with_appcontext
@click.option('--page', required=True, help='対象ページキー（例: notes_receivable）')
@click.option('--company-id', type=int, default=None, help='対象会社ID（未指定時は単一会社がある場合それを使用）')
@click.option('--count', type=int, default=23, show_default=True, help='生成件数')
@click.option('--prefix', type=str, default='', show_default=True, help='名称/摘要に付与する識別用プレフィクス')
def seed_soa_command(page: str, company_id: int | None, count: int, prefix: str):
    """汎用 勘定科目内訳（SoA）ダミーデータ投入CLI。

    例: flask seed-soa --page notes_receivable --count 23
    """
    try:
        from app.cli.seed_soas import run_seed
        created = run_seed(page=page, company_id=company_id, count=count, prefix=prefix)
        click.echo(f"page='{page}' に {created} 件投入しました。")
    except KeyError as e:
        click.echo(str(e))
    except Exception as e:
        click.echo(f"エラー: ダミーデータ投入中に問題が発生しました: {e}")


@click.command('seed-notes-receivable')
@with_appcontext
@click.option('--company-id', type=int, default=None, help='対象会社ID（未指定時は単一会社がある場合それを使用）')
@click.option('--count', type=int, default=23, show_default=True, help='生成する受取手形の件数')
def seed_notes_receivable_command(company_id: int | None, count: int):
    """受取手形（NotesReceivable）をダミーデータで一括投入します。"""
    from datetime import date, timedelta
    import random
    from app.company.models import Company, NotesReceivable

    # 会社の決定
    target_company = None
    if company_id is not None:
        target_company = Company.query.filter_by(id=company_id).first()
        if not target_company:
            click.echo(f"エラー: company_id={company_id} の会社が見つかりません。")
            return
    else:
        companies = Company.query.all()
        if len(companies) == 1:
            target_company = companies[0]
        elif len(companies) == 0:
            click.echo('エラー: Company が存在しません。先に会社を作成してください。')
            return
        else:
            click.echo('エラー: 複数の Company が存在します。--company-id で対象を指定してください。')
            return

    rng = random.Random(42)
    today = date.today()
    bank_names = ['みずほ銀行', '三菱UFJ銀行', '三井住友銀行', 'りそな銀行', 'ゆうちょ銀行']
    branches = ['本店', '新宿支店', '渋谷支店', '大阪支店', '名古屋支店']

    created = 0
    for i in range(count):
        reg_no = ''.join(rng.choice('0123456789') for _ in range(13))
        drawer = f"ダミー株式会社 {i+1:02d}"
        issue_dt = today - timedelta(days=60 + i)
        due_dt = today + timedelta(days=30 + i)
        payer_bank = rng.choice(bank_names)
        payer_branch = rng.choice(branches)
        amount = (i + 1) * 10000
        discount_bank = rng.choice(bank_names)
        discount_branch = rng.choice(branches)
        remarks = f"ダミー明細 {i+1:02d}"

        nr = NotesReceivable(
            company_id=target_company.id,
            registration_number=reg_no,
            drawer=drawer,
            issue_date=issue_dt.strftime('%Y-%m-%d'),
            issue_date_date=issue_dt,
            due_date=due_dt.strftime('%Y-%m-%d'),
            due_date_date=due_dt,
            payer_bank=payer_bank,
            payer_branch=payer_branch,
            amount=amount,
            discount_bank=discount_bank,
            discount_branch=discount_branch,
            remarks=remarks,
        )
        db.session.add(nr)
        created += 1

    db.session.commit()
    click.echo(f"受取手形を {created} 件、Company(id={target_company.id}) に作成しました。")

from __future__ import annotations

from typing import Callable

from app.company.models import (  # noqa: E402
    AccountsPayable,
    AccountsReceivable,
    Deposit,
    LoansReceivable,
    NotesPayable,
    NotesReceivable,
    TemporaryPayment,
)
from app.extensions import db

from .seed_utils import (
    BANKS,
    BRANCHES,
    SeedContext,
    corporate_number_13,
    make_context,
    random_bank,
)

Seeder = Callable[[SeedContext, int], int]


def seed_notes_receivable(ctx: SeedContext, count: int) -> int:
    created = 0
    for i in range(count):
        reg_no = corporate_number_13(ctx.rng)
        drawer = f"{ctx.prefix}ダミー株式会社 {i+1:02d}".strip()
        # distribute dates around today deterministically
        issue_days = 60 + i
        due_days = 30 + i
        from datetime import timedelta
        issue_dt = ctx.today - timedelta(days=issue_days)
        due_dt = ctx.today + timedelta(days=due_days)
        payer_bank, payer_branch = random_bank(ctx.rng)
        discount_bank, discount_branch = random_bank(ctx.rng)
        amount = (i + 1) * 10000
        remarks = f"{ctx.prefix}ダミー明細 {i+1:02d}".strip()

        nr = NotesReceivable(
            company_id=ctx.company.id,
            registration_number=reg_no,
            drawer=drawer,
            issue_date=issue_dt,
            due_date=due_dt,
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
    return created


REGISTRY: dict[str, Seeder] = {
    'notes_receivable': seed_notes_receivable,
}


def run_seed(page: str, company_id: int | None, count: int, prefix: str = "") -> int:
    if page not in REGISTRY:
        raise KeyError(f"未対応のpageです: {page}")
    ctx = make_context(company_id=company_id, seed=42, prefix=prefix)
    # Pre-execution context visibility (DB / company / params)
    try:
        db_url = str(db.engine.url)
    except Exception:
        db_url = "<unknown>"
    print(f"[seed-soa] DB={db_url}")
    print(
        f"[seed-soa] company_id={getattr(ctx.company, 'id', '?')} name={getattr(ctx.company, 'company_name', '?')}"
    )
    print(f"[seed-soa] page={page} count={count} prefix='{prefix}'")
    # Gentle warning for common local mismatch patterns (no behavior change)
    if db_url.startswith("sqlite") and not db_url.endswith("dev.db"):
        print(f"[seed-soa][warn] 非標準DBに接続中: {db_url}")
    seeder = REGISTRY[page]
    return seeder(ctx, count)


# --- Additional seeders for other SoA pages ---

def seed_deposits(ctx: SeedContext, count: int) -> int:
    created = 0
    acct_types = ['普通預金', '当座預金', '定期預金']
    for i in range(count):
        fi = ctx.rng.choice(BANKS)
        br = ctx.rng.choice(BRANCHES)
        at = ctx.rng.choice(acct_types)
        num = ''.join(ctx.rng.choice('0123456789') for _ in range(7))
        bal = (i + 1) * 50000
        dep = Deposit(
            company_id=ctx.company.id,
            financial_institution=f"{ctx.prefix}{fi}".strip(),
            branch_name=br,
            account_type=at,
            account_number=num,
            balance=bal,
            remarks=(f"{ctx.prefix}ダミー預金 {i+1:02d}").strip(),
        )
        db.session.add(dep)
        created += 1
    db.session.commit()
    return created


def seed_accounts_receivable(ctx: SeedContext, count: int) -> int:
    created = 0
    acct_names = ['売掛金', '未収入金']
    for i in range(count):
        ar = AccountsReceivable(
            company_id=ctx.company.id,
            account_name=ctx.rng.choice(acct_names),
            partner_name=f"{ctx.prefix}取引先 {i+1:02d}".strip(),
            registration_number=corporate_number_13(ctx.rng),
            is_subsidiary=bool(ctx.rng.getrandbits(1)),
            partner_address=f"東京都千代田区丸の内{i+1:02d}-1",
            balance_at_eoy=(i + 1) * 70000,
            remarks=(f"{ctx.prefix}売掛ダミー {i+1:02d}").strip(),
        )
        db.session.add(ar)
        created += 1
    db.session.commit()
    return created


def seed_temporary_payments(ctx: SeedContext, count: int) -> int:
    created = 0
    acct_names = ['仮払金', '前渡金']
    for i in range(count):
        tp = TemporaryPayment(
            company_id=ctx.company.id,
            account_name=ctx.rng.choice(acct_names),
            partner_name=f"{ctx.prefix}先払先 {i+1:02d}".strip(),
            registration_number=corporate_number_13(ctx.rng),
            is_subsidiary=bool(ctx.rng.getrandbits(1)),
            partner_address=f"大阪府大阪市北区梅田{i+1:02d}-2",
            relationship='取引先',
            balance_at_eoy=(i + 1) * 30000,
            transaction_details=(f"{ctx.prefix}前渡し {i+1:02d}").strip(),
        )
        db.session.add(tp)
        created += 1
    db.session.commit()
    return created


def seed_notes_payable(ctx: SeedContext, count: int) -> int:
    created = 0
    from datetime import timedelta
    for i in range(count):
        issue_dt = ctx.today - timedelta(days=45 + i)
        due_dt = ctx.today + timedelta(days=45 + i)
        reg_no = corporate_number_13(ctx.rng)
        payer_bank, payer_branch = random_bank(ctx.rng)
        np = NotesPayable(
            company_id=ctx.company.id,
            registration_number=reg_no,
            payee=f"{ctx.prefix}支払先 {i+1:02d}".strip(),
            issue_date=issue_dt,
            due_date=due_dt,
            payer_bank=payer_bank,
            payer_branch=payer_branch,
            amount=(i + 1) * 80000,
            remarks=(f"{ctx.prefix}支払手形 {i+1:02d}").strip(),
        )
        db.session.add(np)
        created += 1
    db.session.commit()
    return created


def seed_accounts_payable(ctx: SeedContext, count: int) -> int:
    created = 0
    acct_names = ['買掛金', '未払金', '未払費用']
    for i in range(count):
        ap = AccountsPayable(
            company_id=ctx.company.id,
            account_name=ctx.rng.choice(acct_names),
            partner_name=f"{ctx.prefix}仕入先 {i+1:02d}".strip(),
            registration_number=corporate_number_13(ctx.rng),
            is_subsidiary=bool(ctx.rng.getrandbits(1)),
            partner_address=f"愛知県名古屋市中村区名駅{i+1:02d}-3",
            balance_at_eoy=(i + 1) * 60000,
            remarks=(f"{ctx.prefix}買掛ダミー {i+1:02d}").strip(),
        )
        db.session.add(ap)
        created += 1
    db.session.commit()
    return created


# ----------------------
# Loans Receivable seeder
# ----------------------

def seed_loans_receivable(ctx: SeedContext, count: int) -> int:
    created = 0
    relationships = ['代表者', '役員', '子会社', '取引先']
    for i in range(count):
        lr = LoansReceivable(
            company_id=ctx.company.id,
            registration_number=corporate_number_13(ctx.rng),
            borrower_name=f"{ctx.prefix}貸付先 {i+1:02d}".strip(),
            borrower_address=f"東京都港区赤坂{i+1:02d}-1",
            relationship=ctx.rng.choice(relationships),
            balance_at_eoy=(i + 1) * 40000,
            received_interest=(i + 1) * 1000,
            interest_rate=round(0.5 + (i % 5) * 0.5, 2),
            collateral_details=(f"{ctx.prefix}担保メモ {i+1:02d}").strip(),
            remarks=(f"{ctx.prefix}貸付ダミー {i+1:02d}").strip(),
        )
        db.session.add(lr)
        created += 1
    db.session.commit()
    return created


# extend registry
REGISTRY.update({
    'deposits': seed_deposits,
    'accounts_receivable': seed_accounts_receivable,
    'temporary_payments': seed_temporary_payments,
    'notes_payable': seed_notes_payable,
    'accounts_payable': seed_accounts_payable,
    'loans_receivable': seed_loans_receivable,
})

# ----------------------
# Additional SoA seeders (requested pages)
# ----------------------
from app.company.models import (  # noqa: E402
    Borrowing,
    ExecutiveCompensation,
    LandRent,
    TemporaryReceipt,
)


def seed_temporary_receipts(ctx: SeedContext, count: int) -> int:
    created = 0
    acct_names = ['仮受金', '前受金', '預り金']
    for i in range(count):
        tr = TemporaryReceipt(
            company_id=ctx.company.id,
            account_name=ctx.rng.choice(acct_names),
            partner_name=f"{ctx.prefix}受入先 {i+1:02d}".strip(),
            balance_at_eoy=(i + 1) * 25000,
            transaction_details=(f"{ctx.prefix}仮受 {i+1:02d}").strip(),
        )
        db.session.add(tr)
        created += 1
    db.session.commit()
    return created

def seed_borrowings(ctx: SeedContext, count: int) -> int:
    created = 0
    for i in range(count):
        br = Borrowing(
            company_id=ctx.company.id,
            lender_name=f"{ctx.prefix}借入先 {i+1:02d}".strip(),
            is_subsidiary=bool(ctx.rng.getrandbits(1)),
            balance_at_eoy=(i + 1) * 120000,
            interest_rate=round(0.5 + (i % 7) * 0.25, 2),
            paid_interest=(i + 1) * 1500,
            remarks=(f"{ctx.prefix}借入 {i+1:02d}").strip(),
        )
        db.session.add(br)
        created += 1
    db.session.commit()
    return created

def seed_executive_compensations(ctx: SeedContext, count: int) -> int:
    created = 0
    positions = ['代表取締役', '取締役', '監査役']
    for i in range(count):
        base = (i + 1) * 300000
        other = ((i % 3) * 20000)
        total = base + other
        ec = ExecutiveCompensation(
            company_id=ctx.company.id,
            shareholder_name=f"{ctx.prefix}役員 {i+1:02d}".strip(),
            relationship='役員',
            position=ctx.rng.choice(positions),
            base_salary=base,
            other_allowances=other,
            total_compensation=total,
        )
        db.session.add(ec)
        created += 1
    db.session.commit()
    return created

def seed_land_rents(ctx: SeedContext, count: int) -> int:
    created = 0
    acct_names = ['地代', '家賃']
    for i in range(count):
        lr = LandRent(
            company_id=ctx.company.id,
            account_name=ctx.rng.choice(acct_names),
            lessor_name=f"{ctx.prefix}賃借先 {i+1:02d}".strip(),
            property_details=f"{i+1:02d}号物件",
            rent_paid=(i + 1) * 50000,
            remarks=(f"{ctx.prefix}地代家賃 {i+1:02d}").strip(),
        )
        db.session.add(lr)
        created += 1
    db.session.commit()
    return created

# register the new seeders
REGISTRY.update({
    'temporary_receipts': seed_temporary_receipts,
    'borrowings': seed_borrowings,
    'executive_compensations': seed_executive_compensations,
    'land_rents': seed_land_rents,
})


# ----------------------
# Deleters (by prefix)
# ----------------------

def _delete_query_notes_receivable(ctx: SeedContext, prefix: str):
    q = NotesReceivable.query.filter_by(company_id=ctx.company.id)
    return q.filter(
        (NotesReceivable.drawer.startswith(prefix)) | (NotesReceivable.remarks.startswith(prefix))
    )


def _delete_query_deposits(ctx: SeedContext, prefix: str):
    q = Deposit.query.filter_by(company_id=ctx.company.id)
    return q.filter(
        (Deposit.financial_institution.startswith(prefix)) | (Deposit.remarks.startswith(prefix))
    )


def _delete_query_accounts_receivable(ctx: SeedContext, prefix: str):
    q = AccountsReceivable.query.filter_by(company_id=ctx.company.id)
    return q.filter(
        (AccountsReceivable.partner_name.startswith(prefix)) | (AccountsReceivable.remarks.startswith(prefix))
    )


def _delete_query_temporary_payments(ctx: SeedContext, prefix: str):
    q = TemporaryPayment.query.filter_by(company_id=ctx.company.id)
    return q.filter(
        (TemporaryPayment.partner_name.startswith(prefix)) | (TemporaryPayment.transaction_details.startswith(prefix))
    )


def _delete_query_notes_payable(ctx: SeedContext, prefix: str):
    q = NotesPayable.query.filter_by(company_id=ctx.company.id)
    return q.filter(NotesPayable.remarks.startswith(prefix) | NotesPayable.payee.startswith(prefix))


def _delete_query_accounts_payable(ctx: SeedContext, prefix: str):
    q = AccountsPayable.query.filter_by(company_id=ctx.company.id)
    return q.filter(
        (AccountsPayable.partner_name.startswith(prefix)) | (AccountsPayable.remarks.startswith(prefix))
    )


def _delete_query_loans_receivable(ctx: SeedContext, prefix: str):
    q = LoansReceivable.query.filter_by(company_id=ctx.company.id)
    return q.filter(
        (LoansReceivable.borrower_name.startswith(prefix)) | (LoansReceivable.remarks.startswith(prefix))
    )


DELETE_REGISTRY = {
    'notes_receivable': _delete_query_notes_receivable,
    'deposits': _delete_query_deposits,
    'accounts_receivable': _delete_query_accounts_receivable,
    'temporary_payments': _delete_query_temporary_payments,
    'notes_payable': _delete_query_notes_payable,
    'accounts_payable': _delete_query_accounts_payable,
    'loans_receivable': _delete_query_loans_receivable,
}

# Add delete queries for newly supported pages
from sqlalchemy import or_  # noqa: E402


def _delete_query_temporary_receipts(ctx: SeedContext, prefix: str):
    q = TemporaryReceipt.query.filter_by(company_id=ctx.company.id)
    return q.filter(or_(TemporaryReceipt.partner_name.startswith(prefix), TemporaryReceipt.transaction_details.startswith(prefix)))

def _delete_query_borrowings(ctx: SeedContext, prefix: str):
    q = Borrowing.query.filter_by(company_id=ctx.company.id)
    return q.filter(or_(Borrowing.lender_name.startswith(prefix), Borrowing.remarks.startswith(prefix)))

def _delete_query_executive_compensations(ctx: SeedContext, prefix: str):
    q = ExecutiveCompensation.query.filter_by(company_id=ctx.company.id)
    return q.filter(or_(ExecutiveCompensation.shareholder_name.startswith(prefix),))

def _delete_query_land_rents(ctx: SeedContext, prefix: str):
    q = LandRent.query.filter_by(company_id=ctx.company.id)
    return q.filter(or_(LandRent.lessor_name.startswith(prefix), LandRent.remarks.startswith(prefix)))

DELETE_REGISTRY.update({
    'temporary_receipts': _delete_query_temporary_receipts,
    'borrowings': _delete_query_borrowings,
    'executive_compensations': _delete_query_executive_compensations,
    'land_rents': _delete_query_land_rents,
})


def run_delete(page: str, company_id: int | None, prefix: str, dry_run: bool = True) -> tuple[int, list[int]]:
    if not prefix:
        raise ValueError('prefix は必須です（空文字は不可）')

from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import date, timedelta

from app.company.models import Company


def get_target_company(company_id: int | None) -> Company:
    if company_id is not None:
        company = Company.query.filter_by(id=company_id).first()
        if not company:
            raise ValueError(f"company_id={company_id} の会社が見つかりません")
        return company
    companies = Company.query.all()
    if len(companies) == 1:
        return companies[0]
    if len(companies) == 0:
        raise RuntimeError('Company が存在しません。先に会社を作成してください。')
    # 複数社が存在し company_id 未指定の場合は、安全にランダム選択（ボス了承済み）
    return random.choice(companies)


@dataclass
class SeedContext:
    company: Company
    rng: random.Random
    today: date
    prefix: str = ""


def make_context(company_id: int | None, seed: int = 42, prefix: str = "") -> SeedContext:
    company = get_target_company(company_id)
    return SeedContext(company=company, rng=random.Random(seed), today=date.today(), prefix=prefix)


def corporate_number_13(rng: random.Random) -> str:
    return ''.join(rng.choice('0123456789') for _ in range(13))


BANKS = ['みずほ銀行', '三菱UFJ銀行', '三井住友銀行', 'りそな銀行', 'ゆうちょ銀行']
BRANCHES = ['本店', '新宿支店', '渋谷支店', '大阪支店', '名古屋支店']


def random_bank(rng: random.Random) -> tuple[str, str]:
    return rng.choice(BANKS), rng.choice(BRANCHES)


def around_today(ctx: SeedContext, before_days: int, after_days: int) -> tuple[date, date]:
    issue = ctx.today - timedelta(days=before_days)
    due = ctx.today + timedelta(days=after_days)
    return issue, due

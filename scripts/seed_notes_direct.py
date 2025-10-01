from __future__ import annotations

import os
import random
import sqlite3
from datetime import date, timedelta

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'instance', 'database.db')
DB_PATH = os.path.abspath(DB_PATH)


def pick_company_id(conn: sqlite3.Connection) -> int:
    cur = conn.execute("SELECT id FROM company ORDER BY RANDOM() LIMIT 1")
    row = cur.fetchone()
    if not row:
        raise SystemExit("No company found. Please create a company first.")
    return int(row[0])


def gen_reg_no(rng: random.Random) -> str:
    return ''.join(rng.choice('0123456789') for _ in range(13))


def main(count: int = 23, prefix: str = "DEMO_") -> None:
    conn = sqlite3.connect(DB_PATH)
    try:
        company_id = pick_company_id(conn)
        rng = random.Random()
        today = date.today()
        banks = ['みずほ銀行', '三菱UFJ銀行', '三井住友銀行', 'りそな銀行', 'ゆうちょ銀行']
        branches = ['本店', '新宿支店', '渋谷支店', '大阪支店', '名古屋支店']
        created = 0
        for i in range(count):
            reg_no = gen_reg_no(rng)
            drawer = f"{prefix}ダミー株式会社 {i+1:02d}"
            issue_dt = today - timedelta(days=60 + i)
            due_dt = today + timedelta(days=30 + i)
            payer_bank = rng.choice(banks)
            payer_branch = rng.choice(branches)
            amount = (i + 1) * 10000
            discount_bank = rng.choice(banks)
            discount_branch = rng.choice(branches)
            remarks = f"{prefix}ダミー明細 {i+1:02d}"
            conn.execute(
                """
                INSERT INTO notes_receivable (
                    drawer, registration_number, issue_date, due_date, payer_bank, payer_branch,
                    amount, discount_bank, discount_branch, remarks, company_id, issue_date_date, due_date_date
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    drawer,
                    reg_no,
                    issue_dt.strftime('%Y-%m-%d'),
                    due_dt.strftime('%Y-%m-%d'),
                    payer_bank,
                    payer_branch,
                    amount,
                    discount_bank,
                    discount_branch,
                    remarks,
                    company_id,
                    issue_dt.strftime('%Y-%m-%d'),
                    due_dt.strftime('%Y-%m-%d'),
                ),
            )
            created += 1
        conn.commit()
        print(f"OK: Inserted {created} notes_receivable rows for company_id={company_id}")
    finally:
        conn.close()


if __name__ == '__main__':
    main()


from __future__ import annotations

"""
Smoke test for seed-soa and delete-seeded helpers using an in-memory DB.
Does not touch real files or the running app DB.
"""

from datetime import date

from app import create_app, db
from app.company.models import User, Company
from app.cli.seed_soas import run_seed, run_delete


def setup_in_memory_app():
    app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'ENV': 'development',
        'WTF_CSRF_ENABLED': False,
        'SECRET_KEY': 'test',
    })
    with app.app_context():
        db.create_all()
    return app


def bootstrap_company():
    user = User(username='tester', email='tester@example.com')
    user.set_password('password')
    db.session.add(user)
    db.session.flush()
    comp = Company(
        corporate_number='9999999999999',
        company_name='テスト株式会社',
        company_name_kana='テスト カブシキガイシャ',
        zip_code='1000001',
        prefecture='東京都',
        city='千代田区',
        address='丸の内1-1-1',
        phone_number='03-0000-0000',
        establishment_date=date(2020, 1, 1),
        user_id=user.id,
    )
    db.session.add(comp)
    db.session.commit()
    return comp.id


def main():
    app = setup_in_memory_app()
    with app.app_context():
        company_id = bootstrap_company()
        # Seed
        created = run_seed(page='notes_receivable', company_id=company_id, count=5, prefix='SMOKE_')
        assert created == 5, f"expected 5 created, got {created}"
        # Dry-run delete
        count, ids = run_delete(page='notes_receivable', company_id=company_id, prefix='SMOKE_', dry_run=True)
        assert count == 5 and len(ids) == 5
        # Execute delete
        count2, _ = run_delete(page='notes_receivable', company_id=company_id, prefix='SMOKE_', dry_run=False)
        assert count2 == 5
        # Verify empty after delete
        count3, _ = run_delete(page='notes_receivable', company_id=company_id, prefix='SMOKE_', dry_run=True)
        assert count3 == 0
        print('OK: seed/delete smoke test passed')


if __name__ == '__main__':
    main()


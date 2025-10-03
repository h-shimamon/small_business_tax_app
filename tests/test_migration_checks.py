from scripts.check_migrations import main as run_migration_checks


def test_migration_checks_pass():
    assert run_migration_checks() == 0

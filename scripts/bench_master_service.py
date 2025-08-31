import time
from contextlib import contextmanager

from app import create_app, db
from app.company.services.master_data_service import MasterDataService, clear_master_df_cache

@contextmanager
def app_ctx():
    app = create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'})
    with app.app_context():
        yield app

def bench_once(label: str, fn, repeat: int = 5):
    t0 = time.perf_counter()
    for _ in range(repeat):
        fn()
    t1 = time.perf_counter()
    print(f"{label}: {(t1 - t0):.4f}s (repeat={repeat})")

if __name__ == '__main__':
    with app_ctx() as app:
        db.create_all()
        svc = MasterDataService()
        # warm-up
        svc.get_bs_master_df(); svc.get_pl_master_df()
        # first (cold)
        clear_master_df_cache()
        bench_once('cold BS', svc.get_bs_master_df)
        bench_once('cold PL', svc.get_pl_master_df)
        # cached
        bench_once('cached BS', svc.get_bs_master_df)
        bench_once('cached PL', svc.get_pl_master_df)
        # after clear
        clear_master_df_cache()
        bench_once('re-cold BS', svc.get_bs_master_df)
        bench_once('re-cold PL', svc.get_pl_master_df)

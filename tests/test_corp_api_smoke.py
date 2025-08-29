import os
from app import create_app


def _make_app():
    # Minimal env to boot under CI
    os.environ.setdefault("FLASK_ENV", "development")
    return create_app()


def test_corp_resolve_ok():
    app = _make_app()
    with app.test_client() as c:
        rv = c.get("/api/corp/resolve?number=0000000000000")
        assert rv.status_code == 200
        data = rv.get_json()
        assert data and "data" in data and data["data"]["corporate_number"] == "0000000000000"


def test_corp_search_ok():
    app = _make_app()
    with app.test_client() as c:
        # name=サンプル, pref=東京都
        rv = c.get("/api/corp/search?name=%E3%82%B5%E3%83%B3%E3%83%97%E3%83%AB&pref=%E6%9D%B1%E4%BA%AC%E9%83%BD")
        assert rv.status_code == 200
        payload = rv.get_json()
        assert payload is not None and "items" in payload
        # Stub may return [] or sample; allow both
        assert isinstance(payload["items"], list)

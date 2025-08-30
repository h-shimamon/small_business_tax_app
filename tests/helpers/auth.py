from contextlib import contextmanager


def login_as(client, user_id: int = 1) -> None:
    """Log in as the given user id by injecting session (Flask-Login compatible).

    Usage:
        from tests.helpers.auth import login_as
        login_as(client, 1)
    """
    with client.session_transaction() as sess:
        sess["_user_id"] = str(user_id)
        sess["_fresh"] = True


def logout(client) -> None:
    """Clear login session."""
    with client.session_transaction() as sess:
        for k in ["_user_id", "_fresh"]:
            if k in sess:
                del sess[k]

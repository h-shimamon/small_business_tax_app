from __future__ import annotations

import time

from flask import Request

# 超簡易レート制限（プロセス内メモリ）。本番は外部ストアに差し替え前提。
# key=(ip,email), 値=(window_start_epoch, count)
_store: dict[tuple[str, str], tuple[float, int]] = {}
WINDOW_SEC = 60.0
LIMIT = 5
RESET_WINDOW_SEC = 3600.0
RESET_LIMIT = 3
SIGNUP_WINDOW_SEC = 3600.0
SIGNUP_LIMIT = 3


def too_many_attempts(req: Request, email: str) -> bool:
    ip = (req.headers.get("X-Forwarded-For", "") or req.remote_addr or "-").split(",")[0].strip()
    key = (ip, (email or "").lower())
    now = time.time()
    win, cnt = _store.get(key, (now, 0))
    if now - win > WINDOW_SEC:
        win, cnt = now, 0
    cnt += 1
    _store[key] = (win, cnt)
    return cnt > LIMIT


def too_many_reset_requests(req: Request, email: str) -> bool:
    ip = (req.headers.get("X-Forwarded-For", "") or req.remote_addr or "-").split(",")[0].strip()
    key = (ip, (email or "").lower() + "::reset")
    now = time.time()
    win, cnt = _store.get(key, (now, 0))
    if now - win > RESET_WINDOW_SEC:
        win, cnt = now, 0
    cnt += 1
    _store[key] = (win, cnt)
    return cnt > RESET_LIMIT


def too_many_signup_requests(req: Request, email: str) -> bool:
    ip = (req.headers.get("X-Forwarded-For", "") or req.remote_addr or "-").split(",")[0].strip()
    key = (ip, (email or "").lower() + "::signup")
    now = time.time()
    win, cnt = _store.get(key, (now, 0))
    if now - win > SIGNUP_WINDOW_SEC:
        win, cnt = now, 0
    cnt += 1
    _store[key] = (win, cnt)
    return cnt > SIGNUP_LIMIT

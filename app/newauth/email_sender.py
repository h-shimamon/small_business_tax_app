from __future__ import annotations

"""
Email sending abstraction for newauth.
- Provide a minimal, replaceable interface.
- Default sender is a no-op logger (safe for dev/CI).
"""
import logging  # noqa: E402
import smtplib  # noqa: E402
from dataclasses import dataclass  # noqa: E402
from email.message import EmailMessage  # noqa: E402
from typing import Protocol  # noqa: E402

from flask import current_app, has_app_context  # noqa: E402

logger = logging.getLogger(__name__)


class EmailSender(Protocol):
    def send(self, to: str, subject: str, html: str | None = None, text: str | None = None) -> None: ...


@dataclass
class DummyEmailSender:
    def send(self, to: str, subject: str, html: str | None = None, text: str | None = None) -> None:
        # Safe log (PII最小): 宛先のマスクと件名のみ
        masked = self._mask(to)
        logger.info("[EmailDummy] to=%s, subject=%s", masked, subject)

    @staticmethod
    def _mask(addr: str) -> str:
        try:
            name, domain = (addr or "").split("@", 1)
            if len(name) <= 2:
                return "*" * len(name) + "@" + domain
            return name[0] + "*" * (len(name) - 2) + name[-1] + "@" + domain
        except Exception:
            return "***"


@dataclass
class SMTPEmailSender:
    host: str
    port: int
    username: str | None = None
    password: str | None = None
    use_tls: bool = True
    default_from: str = "no-reply@example.com"
    timeout: int = 10

    def send(self, to: str, subject: str, html: str | None = None, text: str | None = None) -> None:
        msg = EmailMessage()
        msg["To"] = to
        msg["Subject"] = subject
        msg["From"] = self.username or self.default_from
        msg.set_content(text or "")
        if html:
            msg.add_alternative(html, subtype="html")
        try:
            with smtplib.SMTP(self.host, self.port, timeout=self.timeout) as smtp:
                if self.use_tls:
                    smtp.starttls()
                if self.username:
                    smtp.login(self.username, self.password or "")
                smtp.send_message(msg)
            logger.info(
                "[EmailSMTP] delivered",
                extra={"email_backend": "smtp", "to": DummyEmailSender._mask(to)},
            )
        except Exception:
            logger.exception(
                "[EmailSMTP] delivery failed",
                extra={"email_backend": "smtp", "to": DummyEmailSender._mask(to)},
            )


def _config_value(key: str, default):
    if has_app_context():
        return current_app.config.get(key, default)
    return default


def get_sender() -> EmailSender:
    backend = str(_config_value('NEW_AUTH_EMAIL_BACKEND', 'dummy')).lower()
    if backend == 'smtp':
        host = _config_value('NEW_AUTH_EMAIL_HOST', '')
        if not host:
            logger.warning('[EmailSender] SMTP backend selected but host is missing; using DummyEmailSender')
            return DummyEmailSender()
        return SMTPEmailSender(
            host=host,
            port=int(_config_value('NEW_AUTH_EMAIL_PORT', 587) or 587),
            username=_config_value('NEW_AUTH_EMAIL_USERNAME', None),
            password=_config_value('NEW_AUTH_EMAIL_PASSWORD', None),
            use_tls=bool(_config_value('NEW_AUTH_EMAIL_USE_TLS', True)),
            default_from=_config_value('NEW_AUTH_EMAIL_FROM', 'no-reply@example.com'),
        )
    return DummyEmailSender()

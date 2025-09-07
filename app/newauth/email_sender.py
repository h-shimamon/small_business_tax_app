from __future__ import annotations

"""
Email sending abstraction for newauth.
- Provide a minimal, replaceable interface.
- Default sender is a no-op logger (safe for dev/CI).
"""
import logging  # noqa: E402
from dataclasses import dataclass  # noqa: E402
from typing import Protocol, Optional  # noqa: E402

logger = logging.getLogger(__name__)


class EmailSender(Protocol):
    def send(self, to: str, subject: str, html: Optional[str] = None, text: Optional[str] = None) -> None: ...


@dataclass
class DummyEmailSender:
    def send(self, to: str, subject: str, html: Optional[str] = None, text: Optional[str] = None) -> None:
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


def get_sender() -> EmailSender:
    # 将来: 環境変数や設定に応じて実装を切替
    return DummyEmailSender()
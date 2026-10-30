"""Protokollierung: eine JSON-Zeile pro Ereignis, ohne personenbezogene Daten im Klartext."""

import hashlib
import json
import logging

from site_report_bot.config import settings


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        eintrag = {
            "zeit": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "modul": record.name,
            "nachricht": record.getMessage(),
        }
        # Zusatzfelder aus logger.info(..., extra={...})
        for schluessel in ("chat", "art", "dauer_s", "fehler"):
            if hasattr(record, schluessel):
                eintrag[schluessel] = getattr(record, schluessel)
        return json.dumps(eintrag, ensure_ascii=False)


def setup_logging() -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    logging.basicConfig(level=settings.log_level, handlers=[handler], force=True)


def pseudonym(kennung: str | int) -> str:
    """Kurzer Hash statt Chat-ID oder Telefonnummer: Ereignisse bleiben zuordenbar, die Person nicht."""
    return hashlib.sha256(str(kennung).encode()).hexdigest()[:10]

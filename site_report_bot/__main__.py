"""Startpunkt: `python -m site_report_bot` startet den Telegram-Bot."""

from site_report_bot.log import setup_logging
from site_report_bot.telegram_bot import run

if __name__ == "__main__":
    setup_logging()
    run()

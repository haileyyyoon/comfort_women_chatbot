"""
sheet_logger.py
---------------
Optional logging of chat Q&A pairs to a Google Sheet, so museum staff can
review what visitors are asking. This is best-effort: if the Sheet isn't
configured (or a write fails), the chatbot still answers normally and
just skips logging.
"""

import logging
import os
from datetime import datetime, timezone

import gspread

logger = logging.getLogger(__name__)

CREDENTIALS_PATH = os.getenv("GOOGLE_SHEETS_CREDENTIALS_PATH")
SHEET_ID = os.getenv("GOOGLE_SHEET_ID")
WORKSHEET_NAME = os.getenv("GOOGLE_SHEET_WORKSHEET_NAME", "Sheet1")

_worksheet = None
_init_attempted = False


def _get_worksheet():
    global _worksheet, _init_attempted
    if _worksheet is not None or _init_attempted:
        return _worksheet
    _init_attempted = True

    if not CREDENTIALS_PATH or not SHEET_ID:
        logger.info("Google Sheets logging is not configured (env vars missing); skipping.")
        return None

    try:
        client = gspread.service_account(filename=CREDENTIALS_PATH)
        spreadsheet = client.open_by_key(SHEET_ID)
        try:
            _worksheet = spreadsheet.worksheet(WORKSHEET_NAME)
        except gspread.WorksheetNotFound:
            _worksheet = spreadsheet.add_worksheet(WORKSHEET_NAME, rows=1000, cols=4)
            _worksheet.append_row(["Timestamp (UTC)", "Language", "Question", "Answer"])
    except Exception:
        logger.exception("Could not connect to Google Sheets; logging disabled for this run.")
        _worksheet = None

    return _worksheet


def log_qa(question: str, answer: str, language: str) -> None:
    """Best-effort append of one Q&A row. Never raises."""
    worksheet = _get_worksheet()
    if worksheet is None:
        return
    try:
        timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
        worksheet.append_row([timestamp, language, question, answer])
    except Exception:
        logger.exception("Failed to log Q&A to Google Sheets")

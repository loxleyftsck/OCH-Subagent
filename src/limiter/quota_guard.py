import sqlite3
import logging
from datetime import datetime, date
from pathlib import Path
from typing import Dict, Any, Optional
from src.config import settings

logger = logging.getLogger("quota_guard")

class QuotaGuard:
    """Tracks local daily API usage and prevents accidental budget exhaustion."""
    def __init__(self, db_path: Optional[Path] = None):
        if db_path is None:
            self.db_path = settings.DATA_DIR / "quota.sqlite"
        else:
            self.db_path = db_path
        self._init_db()

    def _init_db(self):
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS daily_usage (
                    usage_date TEXT PRIMARY KEY,
                    ocr_calls INTEGER DEFAULT 0,
                    text_calls INTEGER DEFAULT 0,
                    total_tokens INTEGER DEFAULT 0,
                    estimated_cost_usd REAL DEFAULT 0.0
                )
            """)
            conn.commit()

    def _get_today_str(self) -> str:
        return date.today().isoformat()

    def record_call(self, is_ocr: bool, tokens: int = 500):
        today = self._get_today_str()
        cost_est = (tokens / 1000.0) * (0.002 if is_ocr else 0.0005)
        
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO daily_usage (usage_date, ocr_calls, text_calls, total_tokens, estimated_cost_usd)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(usage_date) DO UPDATE SET
                    ocr_calls = ocr_calls + ?,
                    text_calls = text_calls + ?,
                    total_tokens = total_tokens + ?,
                    estimated_cost_usd = estimated_cost_usd + ?
            """, (
                today,
                1 if is_ocr else 0,
                0 if is_ocr else 1,
                tokens,
                cost_est,
                1 if is_ocr else 0,
                0 if is_ocr else 1,
                tokens,
                cost_est
            ))
            conn.commit()

    def check_safety_limit(self, is_ocr: bool = True) -> bool:
        """Returns True if within safe limit, False if hard cap reached."""
        if not is_ocr:
            return True
        today = self._get_today_str()
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT ocr_calls FROM daily_usage WHERE usage_date = ?", (today,))
            row = cursor.fetchone()
            if row and row[0] >= settings.MAX_DAILY_LOCAL_OCR_CALLS:
                logger.error(f"🛑 [SAFETY STOP] Reached maximum daily local OCR calls limit ({settings.MAX_DAILY_LOCAL_OCR_CALLS}). Halting to protect team budget!")
                return False
        return True

    def get_summary(self) -> Dict[str, Any]:
        today = self._get_today_str()
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT ocr_calls, text_calls, total_tokens, estimated_cost_usd FROM daily_usage WHERE usage_date = ?", (today,))
            row = cursor.fetchone()
            if row:
                ocr_calls, text_calls, tokens, cost = row
                return {
                    "date": today,
                    "ocr_calls": ocr_calls,
                    "max_daily_ocr_calls": settings.MAX_DAILY_LOCAL_OCR_CALLS,
                    "text_calls": text_calls,
                    "total_tokens": tokens,
                    "estimated_cost_usd": round(cost, 4),
                    "remaining_ocr_calls": max(0, settings.MAX_DAILY_LOCAL_OCR_CALLS - ocr_calls)
                }
        return {
            "date": today,
            "ocr_calls": 0,
            "max_daily_ocr_calls": settings.MAX_DAILY_LOCAL_OCR_CALLS,
            "text_calls": 0,
            "total_tokens": 0,
            "estimated_cost_usd": 0.0,
            "remaining_ocr_calls": settings.MAX_DAILY_LOCAL_OCR_CALLS
        }

quota_guard = QuotaGuard()

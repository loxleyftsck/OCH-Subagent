import sqlite3
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from datetime import datetime
from src.config import settings

logger = logging.getLogger("local_cache")

class LocalCacheManager:
    def __init__(self, db_path: Optional[Path] = None):
        if db_path is None:
            self.db_path = settings.DATA_DIR / "cache.sqlite"
        else:
            self.db_path = db_path
        self._init_db()

    def _init_db(self):
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ocr_cache (
                    image_hash TEXT PRIMARY KEY,
                    raw_text TEXT NOT NULL,
                    model_name TEXT NOT NULL,
                    structured_json TEXT,
                    created_at TEXT NOT NULL,
                    token_estimate INTEGER DEFAULT 0
                )
            """)
            conn.commit()

    def get(self, image_hash: str) -> Optional[Dict[str, Any]]:
        """Retrieve cached OCR and parsed JSON if exists."""
        if not settings.ENABLE_LOCAL_CACHE:
            return None

        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT raw_text, model_name, structured_json, created_at, token_estimate FROM ocr_cache WHERE image_hash = ?",
                (image_hash,)
            )
            row = cursor.fetchone()
            if row:
                raw_text, model_name, structured_json_str, created_at, token_estimate = row
                structured_json = json.loads(structured_json_str) if structured_json_str else None
                logger.info(f"⚡ [CACHE HIT] Found cached OCR for hash: {image_hash[:10]}...")
                return {
                    "image_hash": image_hash,
                    "raw_text": raw_text,
                    "model_name": model_name,
                    "structured_json": structured_json,
                    "created_at": created_at,
                    "token_estimate": token_estimate,
                    "is_cached": True
                }
        return None

    def set(
        self,
        image_hash: str,
        raw_text: str,
        model_name: str,
        structured_json: Optional[Dict[str, Any]] = None,
        token_estimate: int = 0
    ):
        """Save OCR and structured JSON result to cache."""
        if not settings.ENABLE_LOCAL_CACHE:
            return

        json_str = json.dumps(structured_json, ensure_ascii=False) if structured_json else None
        now_str = datetime.now().isoformat()
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO ocr_cache 
                (image_hash, raw_text, model_name, structured_json, created_at, token_estimate)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (image_hash, raw_text, model_name, json_str, now_str, token_estimate))
            conn.commit()
            logger.info(f"💾 [CACHE STORED] Saved OCR result for hash: {image_hash[:10]}...")

    def update_structured_json(self, image_hash: str, structured_json: Dict[str, Any]):
        """Update parsed structured JSON for an existing hash."""
        json_str = json.dumps(structured_json, ensure_ascii=False)
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE ocr_cache SET structured_json = ? WHERE image_hash = ?",
                (json_str, image_hash)
            )
            conn.commit()

local_cache = LocalCacheManager()

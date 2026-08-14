import asyncio
import time
import logging
from typing import Dict, Any
from src.config import settings

logger = logging.getLogger("rate_limiter")

class SharedRateLimiter:
    """
    Coordinates safe, collision-free API calls across a 7-person shared team quota.
    Enforces minimum interval (30s for OCR, 2s for text) and strict concurrency lock.
    """
    def __init__(self):
        self._concurrency_semaphore = asyncio.Semaphore(settings.MAX_CONCURRENT_REQUESTS)
        self._last_ocr_call_time: float = 0.0
        self._last_general_call_time: float = 0.0
        self._lock = asyncio.Lock()
        self._active_requests: int = 0

    async def acquire_slot(self, is_ocr: bool = False) -> float:
        """
        Wait until both the concurrency slot and the rate interval are safe to execute.
        Returns the duration waited in seconds.
        """
        waited = 0.0
        await self._concurrency_semaphore.acquire()
        
        async with self._lock:
            self._active_requests += 1
            now = time.time()
            interval = settings.OCR_INTERVAL_SECONDS if is_ocr else settings.GENERAL_INTERVAL_SECONDS
            last_call = self._last_ocr_call_time if is_ocr else self._last_general_call_time
            elapsed = now - last_call

            if elapsed < interval:
                sleep_time = interval - elapsed
                logger.info(f"⏳ [SAFETY RATE LIMIT] Throttling for {sleep_time:.2f}s to respect shared team quota ({'OCR' if is_ocr else 'Text'})...")
                waited = sleep_time
                await asyncio.sleep(sleep_time)

            # Update call timestamp
            if is_ocr:
                self._last_ocr_call_time = time.time()
            else:
                self._last_general_call_time = time.time()

        return waited

    def release_slot(self):
        """Release the concurrency semaphore slot."""
        self._active_requests = max(0, self._active_requests - 1)
        self._concurrency_semaphore.release()

    def get_status(self) -> Dict[str, Any]:
        """Return real-time safety status for dashboard monitor."""
        now = time.time()
        ocr_elapsed = now - self._last_ocr_call_time
        ocr_remaining = max(0.0, settings.OCR_INTERVAL_SECONDS - ocr_elapsed)
        
        return {
            "team_shared_mode": settings.TEAM_SHARED_MODE,
            "max_concurrency": settings.MAX_CONCURRENT_REQUESTS,
            "active_concurrency": self._active_requests,
            "ocr_interval_seconds": settings.OCR_INTERVAL_SECONDS,
            "ocr_cooldown_remaining_seconds": round(ocr_remaining, 1),
            "ocr_ready": ocr_remaining == 0.0,
            "mock_mode": settings.MOCK_MODE
        }

rate_limiter = SharedRateLimiter()

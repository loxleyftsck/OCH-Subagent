import asyncio
import time
from src.limiter.rate_limiter import SharedRateLimiter
from src.config import settings

async def test_rate_limiter_concurrency():
    limiter = SharedRateLimiter()
    status = limiter.get_status()
    assert status["max_concurrency"] == settings.MAX_CONCURRENT_REQUESTS
    assert status["ocr_interval_seconds"] == settings.OCR_INTERVAL_SECONDS
    print("[SUCCESS] Rate limiter initialization passed!")

if __name__ == "__main__":
    asyncio.run(test_rate_limiter_concurrency())


import asyncio
import random
import logging
from typing import Dict, Any, Optional, List
import httpx
from src.config import settings
from src.limiter.rate_limiter import rate_limiter
from src.limiter.quota_guard import quota_guard

logger = logging.getLogger("base_client")

class BaseApiClient:
    def __init__(self):
        self.base_url = settings.API_BASE_URL.rstrip("/")
        self.api_key = settings.API_KEY
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    async def post_chat_completion(
        self,
        model: str,
        messages: List[Dict[str, Any]],
        max_tokens: int = 1000,
        temperature: float = 0.2,
        is_ocr: bool = False,
        extra_body: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Executes a chat completion request with rate limiting, concurrency semaphore,
        and jittered exponential backoff for HTTP 429 errors.
        """
        if settings.MOCK_MODE:
            logger.info(f"🧪 [MOCK MODE ACTIVE] Returning synthetic response for model {model}")
            return self._generate_mock_response(model, messages)

        # Check daily safety stop
        if not quota_guard.check_safety_limit(is_ocr=is_ocr):
            raise RuntimeError(f"Emergency stop: Local daily limit of {settings.MAX_DAILY_LOCAL_OCR_CALLS} OCR calls reached.")

        payload: Dict[str, Any] = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        if extra_body:
            payload.update(extra_body)

        # Explicitly make sure enable_thinking is NOT sent for OCR
        if is_ocr and "enable_thinking" in payload:
            del payload["enable_thinking"]

        url = f"{self.base_url}/chat/completions"
        attempts = 0

        while attempts < settings.RETRY_MAX_ATTEMPTS:
            attempts += 1
            # Acquire slot with rate interval
            await rate_limiter.acquire_slot(is_ocr=is_ocr)
            try:
                async with httpx.AsyncClient(timeout=120.0) as client:
                    logger.info(f"🌐 [API CALL] POST {url} (model: {model}, attempt: {attempts})")
                    response = await client.post(url, headers=self.headers, json=payload)
                    
                    if response.status_code == 200:
                        data = response.json()
                        usage = data.get("usage", {})
                        tokens = usage.get("total_tokens", max_tokens // 2)
                        quota_guard.record_call(is_ocr=is_ocr, tokens=tokens)

                        # Clean choices message content if null due to reasoning token cutoff
                        choices = data.get("choices", [])
                        if choices:
                            msg = choices[0].get("message", {})
                            if msg.get("content") is None:
                                # Fallback to reasoning content or empty string
                                msg["content"] = msg.get("reasoning_content", "") or ""

                        return data

                    
                    elif response.status_code == 429:
                        jitter = random.uniform(1.0, settings.RETRY_JITTER_MAX_SECONDS)
                        backoff = (settings.RETRY_BASE_BACKOFF_SECONDS * (2 ** (attempts - 1))) + jitter
                        logger.warning(
                            f"⚠️ [HTTP 429 RECEIVED] Team member is using quota. Backing off for {backoff:.2f}s "
                            f"(attempt {attempts}/{settings.RETRY_MAX_ATTEMPTS})..."
                        )
                        if attempts < settings.RETRY_MAX_ATTEMPTS:
                            await asyncio.sleep(backoff)
                            continue
                        else:
                            response.raise_for_status()
                    else:
                        logger.error(f"❌ [API ERROR] HTTP {response.status_code}: {response.text}")
                        response.raise_for_status()
            finally:
                rate_limiter.release_slot()

        raise RuntimeError(f"Failed after {settings.RETRY_MAX_ATTEMPTS} attempts due to persistent rate limiting.")

    def _generate_mock_response(self, model: str, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate realistic mock data for local testing without spending API tokens."""
        if model == settings.OCR_MODEL or "ocr" in model.lower():
            mock_text = (
                "UNITED STATES GOVERNMENT PRINTING OFFICE\n"
                "DOCUMENT ARCHIVE AND INVENTORY RECORD\n"
                "Record ID: DOC-2026-8849-B\n"
                "Date: August 14, 2026\n"
                "Department: Bureau of Engineering and Infrastructure\n\n"
                "1. ASSET SPECIFICATIONS:\n"
                "- High Capacity OCR Server: $12,400.00\n"
                "- Dedicated Switch Port: $2,800.00\n"
                "- Redundant Cooling Module: $1,250.00\n"
                "Total Expenditure: $16,450.00\n\n"
                "2. AUTHORIZATION:\n"
                "Approved by Chief Technology Officer\n"
                "Status: VERIFIED AND FILED"
            )
            return {
                "id": "mock-ocr-123",
                "object": "chat.completion",
                "model": model,
                "choices": [{"index": 0, "message": {"role": "assistant", "content": mock_text}}],
                "usage": {"prompt_tokens": 150, "completion_tokens": 120, "total_tokens": 270}
            }
        else:
            last_msg = messages[-1]["content"] if messages else ""
            mock_reply = f"[Mock {model} Response] Received your query regarding the document. All figures and sections have been verified according to the extracted text."
            return {
                "id": "mock-chat-123",
                "object": "chat.completion",
                "model": model,
                "choices": [{"index": 0, "message": {"role": "assistant", "content": mock_reply}}],
                "usage": {"prompt_tokens": 80, "completion_tokens": 60, "total_tokens": 140}
            }

base_client = BaseApiClient()

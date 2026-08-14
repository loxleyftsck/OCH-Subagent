import logging
from pathlib import Path
from typing import Union, Dict, Any, Optional
from PIL import Image
from src.config import settings
from src.client.base_client import base_client
from src.cache.local_cache import local_cache
from src.utils.image_utils import get_image_hash, optimize_image, image_to_data_uri

logger = logging.getLogger("ocr_client")

class OCRClient:
    """Specialized client for ocr-lighton with base64 formatting, hash caching, and token optimization."""
    
    async def extract_text_from_image(
        self,
        image_input: Union[bytes, Image.Image, Path, str],
        prompt: str = "Extract all text from this image.",
        max_tokens: int = 1000
    ) -> Dict[str, Any]:

        """
        Extract text from an image or page using ocr-lighton.
        Checks local SHA-256 cache first to prevent redundant API calls.
        """
        # 1. Calculate image hash
        img_hash = get_image_hash(image_input)
        
        # 2. Check local cache
        cached = local_cache.get(img_hash)
        if cached:
            return cached

        # 3. Optimize and compress image to keep token cost sub-8k
        opt_bytes, mime_type = optimize_image(image_input, max_dimension=1400, quality=85)
        data_uri = image_to_data_uri(opt_bytes, mime_type=mime_type)

        # 4. Construct payload (ARRAY format required)
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": data_uri}}
                ]
            }
        ]

        logger.info(f"🔍 [OCR REQUEST] Sending image (hash: {img_hash[:10]}..., mime: {mime_type}) to {settings.OCR_MODEL}")
        
        # 5. Call API via base client
        response = await base_client.post_chat_completion(
            model=settings.OCR_MODEL,
            messages=messages,
            max_tokens=max_tokens,
            temperature=0.1,
            is_ocr=True
        )

        choices = response.get("choices", [])
        if not choices:
            raise RuntimeError(f"Empty choices returned by OCR API: {response}")

        raw_text = choices[0].get("message", {}).get("content", "")
        tokens = response.get("usage", {}).get("total_tokens", 0)

        # 6. Save to local cache
        local_cache.set(
            image_hash=img_hash,
            raw_text=raw_text,
            model_name=settings.OCR_MODEL,
            token_estimate=tokens
        )

        return {
            "image_hash": img_hash,
            "raw_text": raw_text,
            "model_name": settings.OCR_MODEL,
            "structured_json": None,
            "token_estimate": tokens,
            "is_cached": False
        }

ocr_client = OCRClient()

import asyncio
import io
import sys
import time
from PIL import Image, ImageDraw
import httpx
from src.config import settings
from src.utils.image_utils import image_to_data_uri, optimize_image

async def run_live_api_test():
    print(f"=== TESTING API CONNECTIVITY ===")
    print(f"Endpoint: {settings.API_BASE_URL}")
    print(f"API Key : {settings.API_KEY[:8]}...{settings.API_KEY[-4:]}")
    print()

    headers = {
        "Authorization": f"Bearer {settings.API_KEY}",
        "Content-Type": "application/json"
    }

    # 1. Test Text Model (qwen-35b / nemotron-35)
    print("1. Testing Text Model (qwen-35b)...")
    text_payload = {
        "model": "qwen-35b",
        "messages": [
            {"role": "user", "content": "Respond with only the word: 'ONLINE'"}
        ],
        "max_tokens": 300,
        "temperature": 0.1
    }

    try:
        start_t = time.time()
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{settings.API_BASE_URL}/chat/completions",
                headers=headers,
                json=text_payload
            )
            elapsed = time.time() - start_t
            print(f"   HTTP Status: {resp.status_code} ({elapsed:.2f}s)")
            if resp.status_code == 200:
                data = resp.json()
                msg = data["choices"][0]["message"]
                content = (msg.get("content") or msg.get("reasoning_content") or "").strip()
                print(f"   [SUCCESS] Response from qwen-35b: '{content[:50]}...'")
            else:
                print(f"   [FAILED] Error Body: {resp.text}")
    except Exception as e:
        print(f"   [ERROR] Connection failed: {e}")


    print()

    # 2. Test OCR Model (ocr-lighton) with small synthetic image
    print("2. Testing OCR Model (ocr-lighton)...")
    
    # Create small test image containing text "TEST-OCR-2026"
    test_img = Image.new("RGB", (300, 100), color=(255, 255, 255))
    draw = ImageDraw.Draw(test_img)
    draw.text((20, 35), "TEST-OCR-2026", fill=(0, 0, 0))
    
    buf = io.BytesIO()
    test_img.save(buf, format="PNG")
    data_uri = image_to_data_uri(buf.getvalue(), mime_type="image/png")

    ocr_payload = {
        "model": "ocr-lighton",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Extract all text from this image."},
                    {"type": "image_url", "image_url": {"url": data_uri}}
                ]
            }
        ],
        "max_tokens": 50
    }

    try:
        start_t = time.time()
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{settings.API_BASE_URL}/chat/completions",
                headers=headers,
                json=ocr_payload
            )
            elapsed = time.time() - start_t
            print(f"   HTTP Status: {resp.status_code} ({elapsed:.2f}s)")
            if resp.status_code == 200:
                data = resp.json()
                content = data["choices"][0]["message"]["content"].strip()
                print(f"   [SUCCESS] Response from ocr-lighton: '{content}'")
            elif resp.status_code == 429:
                print(f"   [RATE LIMITED 429] Endpoint busy / rate limit hit. (Shared team collision).")
            else:
                print(f"   [FAILED] Error Body: {resp.text}")
    except Exception as e:
        print(f"   [ERROR] Connection failed: {e}")

    print("\n=== TEST FINISHED ===")

if __name__ == "__main__":
    asyncio.run(run_live_api_test())

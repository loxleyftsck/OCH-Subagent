import os
import sys
import tempfile
from pathlib import Path
from PIL import Image
from src.cache.local_cache import LocalCacheManager
from src.utils.image_utils import get_image_hash

def test_cache_hit_and_store():
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
        db_path = Path(tmpdir) / "test_cache.sqlite"
        cache = LocalCacheManager(db_path=db_path)

        # Create dummy image
        img = Image.new("RGB", (100, 100), color="blue")
        img_hash = get_image_hash(img)

        # Initially not found
        assert cache.get(img_hash) is None

        # Store result
        cache.set(
            image_hash=img_hash,
            raw_text="SAMPLE OCR TEXT",
            model_name="ocr-lighton",
            structured_json={"document_title": "Test Title"},
            token_estimate=120
        )

        # Retrieve and verify hit
        cached = cache.get(img_hash)
        assert cached is not None
        assert cached["raw_text"] == "SAMPLE OCR TEXT"
        assert cached["structured_json"]["document_title"] == "Test Title"
        assert cached["is_cached"] is True
        print("[SUCCESS] Cache hit test passed!")

if __name__ == "__main__":
    test_cache_hit_and_store()


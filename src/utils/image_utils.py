import base64
import hashlib
import io
from pathlib import Path
from typing import Tuple, Union
from PIL import Image

def get_image_hash(image_input: Union[bytes, Image.Image, Path, str]) -> str:
    """Compute SHA256 hash of an image for caching."""
    if isinstance(image_input, (str, Path)):
        with open(image_input, "rb") as f:
            data = f.read()
    elif isinstance(image_input, Image.Image):
        buffer = io.BytesIO()
        image_input.save(buffer, format="PNG")
        data = buffer.getvalue()
    elif isinstance(image_input, bytes):
        data = image_input
    else:
        raise ValueError(f"Unsupported image input type: {type(image_input)}")
    
    return hashlib.sha256(data).hexdigest()

def optimize_image(
    image_input: Union[bytes, Image.Image, Path, str],
    max_dimension: int = 1400,
    quality: int = 85
) -> Tuple[bytes, str]:
    """
    Resize and optimize image to reduce token cost and ensure sub-8k token limits.
    Returns (optimized_bytes, mime_type).
    """
    if isinstance(image_input, (str, Path)):
        img = Image.open(image_input)
    elif isinstance(image_input, bytes):
        img = Image.open(io.BytesIO(image_input))
    elif isinstance(image_input, Image.Image):
        img = image_input.copy()
    else:
        raise ValueError(f"Unsupported image input type: {type(image_input)}")

    # Convert to RGB if necessary (e.g., RGBA or P)
    if img.mode in ("RGBA", "LA", "P"):
        background = Image.new("RGB", img.size, (255, 255, 255))
        if img.mode == "P":
            img = img.convert("RGBA")
        background.paste(img, mask=img.split()[-1] if img.mode in ("RGBA", "LA") else None)
        img = background
    elif img.mode != "RGB":
        img = img.convert("RGB")

    # Resize if dimensions exceed max_dimension
    w, h = img.size
    if max(w, h) > max_dimension:
        if w > h:
            new_w = max_dimension
            new_h = int(h * (max_dimension / w))
        else:
            new_h = max_dimension
            new_w = int(w * (max_dimension / h))
        img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)

    # Save to JPEG buffer
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=quality, optimize=True)
    return buffer.getvalue(), "image/jpeg"

def image_to_base64(image_bytes: bytes) -> str:
    """Encode bytes to base64 string."""
    return base64.b64encode(image_bytes).decode("utf-8")

def image_to_data_uri(image_bytes: bytes, mime_type: str = "image/jpeg") -> str:
    """Encode image to data URI format."""
    b64_str = image_to_base64(image_bytes)
    return f"data:{mime_type};base64,{b64_str}"

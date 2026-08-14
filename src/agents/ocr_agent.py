import logging
from typing import Union, Dict, Any
from pathlib import Path
from PIL import Image
from src.agents.base_agent import BaseSubagent
from src.client.ocr_client import ocr_client
from src.config import settings

logger = logging.getLogger("ocr_agent")

class OCRAgent(BaseSubagent):
    """Subagent specialized in extracting raw text and layout hierarchy from documents."""
    def __init__(self):
        super().__init__(name="OCRExtractorSubagent", model=settings.OCR_MODEL)

    async def process(
        self,
        image_input: Union[bytes, Image.Image, Path, str],
        prompt: str = "Extract all text from this image."
    ) -> Dict[str, Any]:

        logger.info(f"🤖 [{self.name}] Initiating extraction using {self.model}...")
        result = await ocr_client.extract_text_from_image(image_input=image_input, prompt=prompt)
        return result

ocr_agent = OCRAgent()

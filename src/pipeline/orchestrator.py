import logging
from pathlib import Path
from typing import Union, Dict, Any, Optional
from PIL import Image
from src.agents.ocr_agent import ocr_agent
from src.agents.parser_agent import parser_agent
from src.agents.chat_agent import chat_agent
from src.utils.pdf_utils import render_pdf_page_to_image, get_pdf_page_count
from src.pipeline.schemas import OCRResponseSchema

logger = logging.getLogger("orchestrator")

class DocumentOrchestrator:
    """Coordinates Multi-Agent workflow: PDF Rasterize -> OCR -> Structure -> Validation -> Chat."""

    async def process_pdf_page(
        self,
        pdf_path: Union[str, Path],
        page_number: int = 1,
        auto_structure: bool = True
    ) -> Dict[str, Any]:
        """Process a single PDF page through OCR and Structuring subagents."""
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found at {pdf_path}")

        total_pages = get_pdf_page_count(pdf_path)
        logger.info(f"📄 Processing {pdf_path.name} (Page {page_number}/{total_pages})...")

        # 1. Render page to image
        pil_image = render_pdf_page_to_image(pdf_path, page_number=page_number, scale=2.0)

        # 2. Run OCR Extraction Subagent
        ocr_result = await ocr_agent.process(image_input=pil_image)
        raw_text = ocr_result["raw_text"]
        image_hash = ocr_result["image_hash"]

        structured_data = None
        if auto_structure and raw_text.strip():
            # 3. Run Structuring Parser Subagent
            structured_data = await parser_agent.process(raw_text=raw_text, image_hash=image_hash)

        return {
            "file_name": pdf_path.name,
            "page_number": page_number,
            "total_pages": total_pages,
            "image_hash": image_hash,
            "raw_text": raw_text,
            "model_name": ocr_result["model_name"],
            "is_cached": ocr_result.get("is_cached", False),
            "token_estimate": ocr_result.get("token_estimate", 0),
            "structured_data": structured_data
        }

    async def process_image_file(
        self,
        image_path: Union[str, Path],
        auto_structure: bool = True
    ) -> Dict[str, Any]:
        """Process an image file through OCR and Structuring subagents."""
        image_path = Path(image_path)
        if not image_path.exists():
            raise FileNotFoundError(f"Image not found at {image_path}")

        pil_image = Image.open(image_path)
        ocr_result = await ocr_agent.process(image_input=pil_image)
        raw_text = ocr_result["raw_text"]
        image_hash = ocr_result["image_hash"]

        structured_data = None
        if auto_structure and raw_text.strip():
            structured_data = await parser_agent.process(raw_text=raw_text, image_hash=image_hash)

        return {
            "file_name": image_path.name,
            "page_number": 1,
            "total_pages": 1,
            "image_hash": image_hash,
            "raw_text": raw_text,
            "model_name": ocr_result["model_name"],
            "is_cached": ocr_result.get("is_cached", False),
            "token_estimate": ocr_result.get("token_estimate", 0),
            "structured_data": structured_data
        }

orchestrator = DocumentOrchestrator()

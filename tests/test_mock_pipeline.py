import asyncio
from pathlib import Path
from PIL import Image
from src.config import settings
from src.dataset.hf_downloader import create_fallback_sample_pdf
from src.pipeline.orchestrator import orchestrator
from src.agents.chat_agent import chat_agent

async def test_end_to_end_mock():
    # Force mock mode for fast local verification
    settings.MOCK_MODE = True
    settings.ensure_directories()
    
    # Create sample PDF
    test_pdf = settings.PDF_DIR / "govdoc_row_4.pdf"
    create_fallback_sample_pdf(test_pdf, row_index=4)

    print("Running OCR & Structuring pipeline...")
    result = await orchestrator.process_pdf_page(test_pdf, page_number=1, auto_structure=True)
    assert result is not None
    assert "raw_text" in result
    print("[SUCCESS] OCR Result Received:", result["raw_text"][:60], "...")

    print("Running Chat Subagent query...")
    chat_res = await chat_agent.process(
        messages=[{"role": "user", "content": "What is the total expenditure mentioned in this document?"}],
        document_text=result["raw_text"]
    )
    assert chat_res is not None
    assert "reply" in chat_res
    print("[SUCCESS] Chat Subagent Replied:", chat_res["reply"][:60], "...")
    print("[SUCCESS] All pipeline tests passed!")

if __name__ == "__main__":
    asyncio.run(test_end_to_end_mock())


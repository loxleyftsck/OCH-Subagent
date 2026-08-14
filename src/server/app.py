import io
import logging
from pathlib import Path
from typing import List, Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse, FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.config import settings
from src.dataset.hf_downloader import download_sample_pdf, list_downloaded_pdfs
from src.utils.pdf_utils import get_pdf_page_count, render_pdf_page_to_image
from src.utils.image_utils import optimize_image, get_image_hash
from src.cache.local_cache import local_cache
from src.limiter.rate_limiter import rate_limiter
from src.limiter.quota_guard import quota_guard
from src.pipeline.orchestrator import orchestrator
from src.agents.chat_agent import chat_agent
from src.pipeline.schemas import ChatRequest, ChatResponse


logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("server")

app = FastAPI(title="OCH-Subagent System", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Routes

@app.get("/api/safety/status")
async def get_safety_status():
    """Real-time rate limit cooldown, concurrency slot, and daily budget usage."""
    limiter_status = rate_limiter.get_status()
    quota_summary = quota_guard.get_summary()
    return {
        "limiter": limiter_status,
        "quota": quota_summary,
        "models": {
            "ocr": settings.OCR_MODEL,
            "text": settings.TEXT_MODEL,
            "chat": settings.CHAT_MODEL,
            "router": settings.ROUTER_MODEL,
            "vision": settings.VISION_MODEL
        }
    }

@app.get("/api/documents")
async def get_documents():
    """List all available documents in data/govdocs."""
    return list_downloaded_pdfs()

@app.post("/api/documents/download-hf")
async def download_hf_dataset_row(row_index: int = Form(4)):
    """Download a specific row from Hugging Face BEE-spoke-data/govdocs1-pdf-source."""
    path = download_sample_pdf(row_index=row_index)
    if not path or not path.exists():
        raise HTTPException(status_code=500, detail=f"Failed to fetch row {row_index} from Hugging Face.")
    return {"status": "success", "file_name": path.name, "row_index": row_index}

@app.post("/api/documents/upload")
async def upload_document(file: UploadFile = File(...)):
    """Upload a custom PDF or image file."""
    settings.PDF_DIR.mkdir(parents=True, exist_ok=True)
    target_path = settings.PDF_DIR / file.filename
    content = await file.read()
    with open(target_path, "wb") as f:
        f.write(content)
    return {"status": "success", "file_name": file.filename, "size_bytes": len(content)}

@app.get("/api/documents/{filename}/meta")
async def get_document_metadata(filename: str):
    """Get page count and file information."""
    file_path = settings.PDF_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    is_pdf = filename.lower().endswith(".pdf")
    total_pages = get_pdf_page_count(file_path) if is_pdf else 1
    
    return {
        "filename": filename,
        "is_pdf": is_pdf,
        "total_pages": total_pages,
        "size_bytes": file_path.stat().st_size
    }

@app.get("/api/documents/{filename}/page/{page_number}/image")
async def get_document_page_image(filename: str, page_number: int = 1, scale: float = 1.5):
    """Render and serve a specific PDF page as a JPEG image for the viewer."""
    file_path = settings.PDF_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    if filename.lower().endswith(".pdf"):
        pil_img = render_pdf_page_to_image(file_path, page_number=page_number, scale=scale)
    else:
        from PIL import Image
        pil_img = Image.open(file_path)

    buf = io.BytesIO()
    pil_img.save(buf, format="JPEG", quality=90)
    buf.seek(0)
    return StreamingResponse(buf, media_type="image/jpeg")

@app.post("/api/documents/{filename}/ocr")
async def run_ocr_pipeline(filename: str, page_number: int = Form(1), auto_structure: bool = Form(True)):
    """Execute OCR and Structuring Subagents on a document page."""
    file_path = settings.PDF_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    try:
        if filename.lower().endswith(".pdf"):
            result = await orchestrator.process_pdf_page(file_path, page_number=page_number, auto_structure=auto_structure)
        else:
            result = await orchestrator.process_image_file(file_path, auto_structure=auto_structure)
        return result
    except Exception as e:
        logger.error(f"Error in OCR pipeline: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat", response_model=ChatResponse)
async def chat_with_document(request: ChatRequest):
    """Interactive document Q&A subagent."""
    file_path = settings.PDF_DIR / request.pdf_name
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"Dokumen '{request.pdf_name}' tidak ditemukan.")

    doc_text = ""
    try:
        if request.pdf_name.lower().endswith(".pdf"):
            # Render page and check cache first
            pil_img = render_pdf_page_to_image(file_path, page_number=request.page_number, scale=1.5)
            img_hash = get_image_hash(pil_img)
            cached = local_cache.get(img_hash)
            if cached and cached.get("raw_text"):
                doc_text = cached["raw_text"]
            else:
                ocr_res = await orchestrator.process_pdf_page(file_path, page_number=request.page_number, auto_structure=False)
                doc_text = ocr_res.get("raw_text", "")
        else:
            img_hash = get_image_hash(file_path)
            cached = local_cache.get(img_hash)
            if cached and cached.get("raw_text"):
                doc_text = cached["raw_text"]
            else:
                ocr_res = await orchestrator.process_image_file(file_path, auto_structure=False)
                doc_text = ocr_res.get("raw_text", "")
    except Exception as e:
        logger.warning(f"Could not retrieve OCR context: {e}")
        doc_text = "[No OCR text available for this document]"

    try:
        chat_res = await chat_agent.process(
            messages=[{"role": m.role, "content": m.content} for m in request.messages],
            document_text=doc_text,
            model_override=request.model
        )

        return ChatResponse(
            reply=chat_res["reply"],
            model_used=chat_res["model_used"],
            tokens_used=chat_res.get("tokens_used", 0)
        )
    except Exception as e:
        logger.error(f"Error in chat agent: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# Static files mount
web_dir = settings.BASE_DIR / "web"
web_dir.mkdir(parents=True, exist_ok=True)
app.mount("/", StaticFiles(directory=str(web_dir), html=True), name="static")

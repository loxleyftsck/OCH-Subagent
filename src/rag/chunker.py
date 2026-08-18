import re
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

logger = logging.getLogger("rag.chunker")


class DocumentChunk(BaseModel):
    chunk_id: str
    filename: str
    page_number: int
    text: str
    start_char: int = 0
    end_char: int = 0
    section_title: Optional[str] = None
    token_count_approx: int = 0


class DocumentChunker:
    """Extracts and chunks document text from multi-page PDFs or text files."""

    def __init__(self, chunk_size: int = 600, chunk_overlap: int = 100):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def extract_text_from_pdf(self, pdf_path: Path) -> List[Dict[str, Any]]:
        """Extract text page-by-page from PDF with fallback to PyMuPDF and OCR cache."""
        pages = []
        try:
            import pymupdf
            doc = pymupdf.open(pdf_path)
            for i, page in enumerate(doc):
                text = page.get_text("text") or ""
                # If page is an image scan, check if we have OCR cache for it
                if not text.strip():
                    try:
                        from src.utils.pdf_utils import render_pdf_page_to_image
                        from src.utils.image_utils import get_image_hash
                        from src.cache.local_cache import local_cache
                        pil_img = render_pdf_page_to_image(pdf_path, page_number=i + 1, scale=1.0)
                        h = get_image_hash(pil_img)
                        cached = local_cache.get(h)
                        if cached and cached.get("raw_text"):
                            text = cached["raw_text"]
                    except Exception:
                        pass
                pages.append({"page_number": i + 1, "text": text.strip()})
            doc.close()
            return pages
        except Exception as e:
            logger.warning(f"PyMuPDF failed on {pdf_path.name}: {e}, trying pypdf fallback...")

        try:
            from pypdf import PdfReader
            reader = PdfReader(str(pdf_path))
            for i, page in enumerate(reader.pages):
                text = page.extract_text() or ""
                pages.append({"page_number": i + 1, "text": text.strip()})
            return pages
        except Exception as e:
            logger.error(f"Failed to extract text from {pdf_path.name}: {e}")
            return []

    def chunk_document(self, file_path: Path) -> List[DocumentChunk]:
        """Chunk a document with page and section awareness."""
        filename = file_path.name
        chunks: List[DocumentChunk] = []

        if file_path.suffix.lower() == ".pdf":
            pages = self.extract_text_from_pdf(file_path)
        else:
            try:
                text = file_path.read_text(encoding="utf-8", errors="ignore")
                pages = [{"page_number": 1, "text": text}]
            except Exception as e:
                logger.error(f"Error reading file {filename}: {e}")
                pages = []

        global_chunk_idx = 0
        article_pattern = re.compile(r"(BAB\s+[IVXLCDM]+|Pasal\s+\d+|Bagian\s+Ke[a-z]+|Paragraf\s+\d+)", re.IGNORECASE)

        for p_info in pages:
            page_num = p_info["page_number"]
            page_text = p_info["text"]

            if not page_text.strip():
                continue

            # Split into paragraphs / sections
            paragraphs = [p.strip() for p in page_text.split("\n\n") if p.strip()]
            if not paragraphs:
                paragraphs = [page_text]

            current_chunk_text = ""
            current_section = None

            for para in paragraphs:
                header_match = article_pattern.search(para)
                if header_match:
                    current_section = header_match.group(0)

                if len(current_chunk_text) + len(para) + 1 <= self.chunk_size:
                    current_chunk_text += ("\n\n" + para if current_chunk_text else para)
                else:
                    if current_chunk_text:
                        global_chunk_idx += 1
                        chunks.append(
                            DocumentChunk(
                                chunk_id=f"{filename}_p{page_num}_c{global_chunk_idx}",
                                filename=filename,
                                page_number=page_num,
                                text=current_chunk_text,
                                section_title=current_section,
                                token_count_approx=len(current_chunk_text.split())
                            )
                        )
                    
                    if len(para) > self.chunk_size:
                        start = 0
                        while start < len(para):
                            end = min(start + self.chunk_size, len(para))
                            sub_text = para[start:end]
                            global_chunk_idx += 1
                            chunks.append(
                                DocumentChunk(
                                    chunk_id=f"{filename}_p{page_num}_c{global_chunk_idx}",
                                    filename=filename,
                                    page_number=page_num,
                                    text=sub_text,
                                    section_title=current_section,
                                    token_count_approx=len(sub_text.split())
                                )
                            )
                            start += (self.chunk_size - self.chunk_overlap)
                        current_chunk_text = ""
                    else:
                        current_chunk_text = para

            if current_chunk_text:
                global_chunk_idx += 1
                chunks.append(
                    DocumentChunk(
                        chunk_id=f"{filename}_p{page_num}_c{global_chunk_idx}",
                        filename=filename,
                        page_number=page_num,
                        text=current_chunk_text,
                        section_title=current_section,
                        token_count_approx=len(current_chunk_text.split())
                    )
                )

        logger.info(f"Generated {len(chunks)} chunks for {filename} across {len(pages)} pages.")
        return chunks

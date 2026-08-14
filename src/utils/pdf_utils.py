import io
from pathlib import Path
from typing import List, Tuple, Union
from PIL import Image

def get_pdf_page_count(pdf_path: Union[str, Path, bytes]) -> int:
    """Return total number of pages in the PDF."""
    try:
        import pymupdf
        if isinstance(pdf_path, bytes):
            doc = pymupdf.open(stream=pdf_path, filetype="pdf")
        else:
            doc = pymupdf.open(str(pdf_path))
        count = len(doc)
        doc.close()
        return count
    except Exception:
        try:
            import pypdfium2 as pdfium
            if isinstance(pdf_path, bytes):
                doc = pdfium.PdfDocument(pdf_path)
            else:
                doc = pdfium.PdfDocument(str(pdf_path))
            count = len(doc)
            doc.close()
            return count
        except Exception:
            try:
                import pypdf
                if isinstance(pdf_path, bytes):
                    reader = pypdf.PdfReader(io.BytesIO(pdf_path))
                else:
                    reader = pypdf.PdfReader(str(pdf_path))
                return len(reader.pages)
            except Exception as e:
                raise RuntimeError(f"Failed to read PDF pages: {e}")

def render_pdf_page_to_image(
    pdf_path: Union[str, Path, bytes],
    page_number: int = 1,
    scale: float = 2.0
) -> Image.Image:
    """
    Render a specific PDF page (1-indexed) into a PIL Image.
    """
    # 1. Try PyMuPDF
    try:
        import pymupdf
        if isinstance(pdf_path, bytes):
            doc = pymupdf.open(stream=pdf_path, filetype="pdf")
        else:
            doc = pymupdf.open(str(pdf_path))
        
        if page_number < 1 or page_number > len(doc):
            doc.close()
            raise ValueError(f"Page {page_number} is out of bounds (1..{len(doc)})")
        
        page = doc[page_number - 1]
        # render at dpi
        dpi = int(72 * scale)
        pix = page.get_pixmap(dpi=dpi)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        doc.close()
        return img
    except Exception as e_mupdf:
        # 2. Fallback to pypdfium2
        try:
            import pypdfium2 as pdfium
            if isinstance(pdf_path, bytes):
                doc = pdfium.PdfDocument(pdf_path)
            else:
                doc = pdfium.PdfDocument(str(pdf_path))
            
            if page_number < 1 or page_number > len(doc):
                doc.close()
                raise ValueError(f"Page {page_number} is out of bounds (1..{len(doc)})")
            
            page = doc[page_number - 1]
            bitmap = page.render(scale=scale)
            pil_image = bitmap.to_pil()
            doc.close()
            return pil_image
        except Exception as e_pdfium:
            raise RuntimeError(f"Failed to render page {page_number} of PDF: {e_mupdf} | {e_pdfium}")


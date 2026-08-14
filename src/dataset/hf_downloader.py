import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from src.config import settings

logger = logging.getLogger("hf_downloader")

DATASET_NAME = "BEE-spoke-data/govdocs1-pdf-source"

def download_sample_pdf(row_index: int = 4, target_dir: Optional[Path] = None) -> Optional[Path]:
    """
    Download a specific row (default row=4) from BEE-spoke-data/govdocs1-pdf-source.
    Saves the PDF file into target_dir (defaults to data/govdocs).
    """
    if target_dir is None:
        target_dir = settings.PDF_DIR
    target_dir.mkdir(parents=True, exist_ok=True)

    expected_path = target_dir / f"govdoc_row_{row_index}.pdf"
    meta_path = target_dir / f"govdoc_row_{row_index}.json"

    if expected_path.exists():
        logger.info(f"Row {row_index} already downloaded at {expected_path}")
        return expected_path

    try:
        from datasets import load_dataset
        logger.info(f"Loading dataset {DATASET_NAME} stream for row {row_index}...")
        ds = load_dataset(DATASET_NAME, split="train", streaming=True)
        
        target_row = None
        for i, item in enumerate(ds):
            if i == row_index:
                target_row = item
                break

        if not target_row:
            logger.error(f"Row {row_index} not found in {DATASET_NAME}")
            return None

        # Extract PDF bytes
        pdf_bytes = None
        doc_id = target_row.get("doc_id", f"row_{row_index}")
        
        if "pdf_bytes" in target_row and target_row["pdf_bytes"]:
            pdf_bytes = target_row["pdf_bytes"]
        elif "bytes" in target_row and target_row["bytes"]:
            pdf_bytes = target_row["bytes"]
        elif "file" in target_row and isinstance(target_row["file"], bytes):
            pdf_bytes = target_row["file"]
        elif "pdf" in target_row:
            pdf_field = target_row["pdf"]
            if isinstance(pdf_field, dict) and "bytes" in pdf_field:
                pdf_bytes = pdf_field["bytes"]
            elif isinstance(pdf_field, bytes):
                pdf_bytes = pdf_field

        if pdf_bytes:
            with open(expected_path, "wb") as f:
                f.write(pdf_bytes)
            
            # Save metadata
            meta = {
                "dataset": DATASET_NAME,
                "row_index": row_index,
                "doc_id": doc_id,
                "file_path": str(expected_path),
                "num_pages": target_row.get("num_pages"),
                "file_size": len(pdf_bytes)
            }
            with open(meta_path, "w", encoding="utf-8") as f:
                json.dump(meta, f, indent=2)

            logger.info(f"Successfully saved row {row_index} to {expected_path}")
            return expected_path
        else:
            logger.warning(f"Could not extract raw bytes from row: {list(target_row.keys())}")
            # Save whatever metadata we have
            with open(meta_path, "w", encoding="utf-8") as f:
                json.dump({k: str(v) for k, v in target_row.items() if k != "pdf_bytes"}, f, indent=2)
            return None

    except Exception as e:
        logger.error(f"Error downloading from Hugging Face: {e}")
        # If network error or library issue, create a fallback sample PDF for development/testing
        return create_fallback_sample_pdf(expected_path, row_index)

def create_fallback_sample_pdf(output_path: Path, row_index: int) -> Path:
    """Create a sample PDF document for testing when offline or dataset is unreachable."""
    from PIL import Image, ImageDraw, ImageFont
    
    img = Image.new("RGB", (1000, 1400), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    
    # Draw sample GovDoc / Invoice Header
    draw.rectangle([(40, 40), (960, 120)], fill=(240, 243, 246))
    draw.text((60, 60), f"GOVERNMENT DOCUMENT ARCHIVE - RECORD #{row_index:04d}", fill=(20, 35, 60))
    draw.text((60, 90), "CONFIDENTIAL & OFFICIAL RECORD // DEPT OF PUBLIC INFRASTRUCTURE", fill=(100, 110, 120))
    
    # Body text
    body_lines = [
        "1. EXECUTIVE SUMMARY & PROJECT SCOPE",
        "This document details the procurement, verification, and audit of public infrastructure equipment.",
        "Reference Code: GOV-2026-DOC-004B",
        "Issued Date: 14 August 2026",
        "Authorizing Officer: Dr. H. Michain, Lead Inspector",
        "",
        "2. AUDITED EXPENDITURES & ASSETS",
        "Item #1: Industrial Optical Character Recognition Server (Model OCH-3500) - $14,500.00",
        "Item #2: Fiber-Optic Local Node Gateway (10 Gbps Interface) - $3,200.00",
        "Item #3: High-Reliability Power Distribution Unit - $1,150.00",
        "Subtotal: $18,850.00 | Tax (10%): $1,885.00 | Total Approved Budget: $20,735.00",
        "",
        "3. COMPLIANCE & VERIFICATION NOTES",
        "All units verified in accordance with national safety and stream concurrency standards.",
        "Status: VERIFIED AND ARCHIVED."
    ]
    
    y = 160
    for line in body_lines:
        if line.startswith(("1.", "2.", "3.")):
            draw.text((60, y), line, fill=(15, 25, 45))
            y += 35
        else:
            draw.text((60, y), line, fill=(50, 60, 70))
            y += 28

    # Save as PDF
    img.save(str(output_path), "PDF", resolution=100.0)
    logger.info(f"Created fallback GovDoc sample PDF at {output_path}")
    return output_path

def create_sample_receipt_image(output_path: Path) -> Path:
    """Create a realistic sample supermarket/cafe receipt image for testing."""
    from PIL import Image, ImageDraw
    
    # Receipt dimensions (typical thermal paper aspect ratio)
    img = Image.new("RGB", (600, 950), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    
    # Store Header
    draw.text((180, 40), "INDOMART SUPERMARKET", fill=(10, 10, 10))
    draw.text((160, 65), "Jl. Sudirman No. 45, Jakarta", fill=(80, 80, 80))
    draw.text((190, 85), "Telp: (021) 555-0199", fill=(80, 80, 80))
    draw.text((50, 115), "-" * 52, fill=(180, 180, 180))
    
    # Transaction Meta
    draw.text((50, 135), "No. Struk : STRUK-2026-8891", fill=(30, 30, 30))
    draw.text((50, 155), "Tanggal   : 14/08/2026  14:32", fill=(30, 30, 30))
    draw.text((50, 175), "Kasir     : Budi Santoso (POS-02)", fill=(30, 30, 30))
    draw.text((50, 195), "-" * 52, fill=(180, 180, 180))
    
    # Items
    items = [
        ("Indomilk Susu UHT 1L", "2 x 18.500", "37.000"),
        ("Roti Tawar Gandum", "1 x 16.000", "16.000"),
        ("Kopi Kapal Api Special 165g", "1 x 14.500", "14.500"),
        ("Minyak Goreng Bimoli 2L", "1 x 34.000", "34.000"),
        ("Teh Botol Sosro 450ml", "3 x 6.500", "19.500"),
    ]
    
    y = 220
    for name, qty_price, total in items:
        draw.text((50, y), name, fill=(20, 20, 20))
        draw.text((50, y + 20), f"  {qty_price}", fill=(100, 100, 100))
        draw.text((450, y + 20), total, fill=(20, 20, 20))
        y += 50
        
    draw.text((50, y), "-" * 52, fill=(180, 180, 180))
    y += 25
    
    # Totals
    draw.text((50, y), "Subtotal", fill=(60, 60, 60))
    draw.text((440, y), "Rp 121.000", fill=(20, 20, 20))
    y += 25
    draw.text((50, y), "Diskon Member (5%)", fill=(60, 60, 60))
    draw.text((445, y), "-Rp 6.050", fill=(20, 120, 20))
    y += 25
    draw.text((50, y), "PPN (11%)", fill=(60, 60, 60))
    draw.text((445, y), "Rp 12.645", fill=(60, 60, 60))
    y += 30
    draw.text((50, y), "TOTAL AKHIR", fill=(10, 10, 10))
    draw.text((430, y), "Rp 127.595", fill=(10, 10, 10))
    y += 35
    draw.text((50, y), "Metode Bayar : QRIS (GOPAY)", fill=(50, 50, 50))
    y += 25
    draw.text((50, y), "Status       : LUNAS", fill=(20, 140, 20))
    y += 40
    
    # Footer
    draw.text((170, y), "*** TERIMA KASIH ***", fill=(80, 80, 80))
    draw.text((140, y + 20), "Barang yang sudah dibeli", fill=(120, 120, 120))
    draw.text((130, y + 40), "tidak dapat ditukar / dikembalikan", fill=(120, 120, 120))
    
    img.save(str(output_path), "JPEG", quality=95)
    logger.info(f"Created sample receipt image at {output_path}")
    return output_path

def list_downloaded_pdfs() -> List[Dict[str, Any]]:
    """List all PDFs and receipt images available in data/govdocs."""
    settings.PDF_DIR.mkdir(parents=True, exist_ok=True)
    supported_exts = ("*.pdf", "*.png", "*.jpg", "*.jpeg", "*.webp")
    doc_files = []
    for ext in supported_exts:
        doc_files.extend(settings.PDF_DIR.glob(ext))
    
    # Sort files
    doc_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    
    results = []
    for p in doc_files:
        meta_file = p.with_suffix(".json")
        meta = {}
        if meta_file.exists():
            try:
                with open(meta_file, "r", encoding="utf-8") as f:
                    meta = json.load(f)
            except Exception:
                pass
        
        is_pdf = p.suffix.lower() == ".pdf"
        results.append({
            "filename": p.name,
            "path": str(p),
            "is_pdf": is_pdf,
            "type": "PDF Document" if is_pdf else "Receipt / Image",
            "size_bytes": p.stat().st_size,
            "metadata": meta
        })
    return results


from src.config import settings
from src.dataset.hf_downloader import create_fallback_sample_pdf, create_sample_receipt_image

def init_default_samples():
    settings.ensure_directories()
    sample_pdf = settings.PDF_DIR / "govdoc_row_4.pdf"
    if not sample_pdf.exists():
        create_fallback_sample_pdf(sample_pdf, row_index=4)
        print(f"Created sample PDF at {sample_pdf}")

    sample_receipt = settings.PDF_DIR / "sample_struk_indomaret.jpg"
    if not sample_receipt.exists():
        create_sample_receipt_image(sample_receipt)
        print(f"Created sample receipt image at {sample_receipt}")

if __name__ == "__main__":
    init_default_samples()


from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field

class OCRResponseSchema(BaseModel):
    image_hash: str
    raw_text: str
    model_name: str
    is_cached: bool = False
    token_estimate: int = 0
    structured_json: Optional[Dict[str, Any]] = None

class ReceiptItemSchema(BaseModel):
    name: str = Field(description="Nama atau deskripsi produk/barang")
    qty: Optional[float] = Field(default=1.0, description="Jumlah kuantitas barang")
    unit_price: Optional[float] = Field(None, description="Harga satuan barang")
    total_price: Optional[float] = Field(None, description="Total harga untuk baris item ini")

class ReceiptAnalysisSchema(BaseModel):
    merchant_name: str = Field(description="Nama toko, restoran, minimarket, atau penjual")
    document_type: str = Field(default="Struk Belanja / Receipt", description="Tipe dokumen")
    transaction_date: Optional[str] = Field(None, description="Tanggal transaksi (misal: 14/08/2026)")
    transaction_time: Optional[str] = Field(None, description="Waktu/jam transaksi (misal: 14:30:00)")
    receipt_number: Optional[str] = Field(None, description="Nomor nota, invoice, atau struk")
    cashier: Optional[str] = Field(None, description="Nama kasir atau nomor kasir/POS")
    items: List[ReceiptItemSchema] = Field(default_factory=list, description="Daftar rincian barang yang dibeli")
    subtotal: Optional[float] = Field(None, description="Subtotal sebelum pajak/diskon")
    discount: Optional[float] = Field(None, description="Potongan harga / diskon jika ada")
    tax: Optional[float] = Field(None, description="Pajak PPN atau service charge jika ada")
    total_amount: Optional[float] = Field(None, description="Total akhir / grand total belanja")
    payment_method: Optional[str] = Field(None, description="Metode pembayaran: Tunai/Cash, QRIS, Debit, dsb.")
    change_amount: Optional[float] = Field(None, description="Uang kembalian jika ada")
    summary: str = Field(description="Ringkasan singkat transaksi belanja")

class DocumentAnalysisSchema(BaseModel):
    document_title: str = Field(description="Title or heading of the document")
    document_type: str = Field(description="Category e.g., Government Document, Invoice, Receipt, Report, Form")
    reference_number: Optional[str] = Field(None, description="Document identifier, invoice number, or case code")
    dates: List[str] = Field(default_factory=list, description="Any detected dates or issuance timestamps")
    organizations: List[str] = Field(default_factory=list, description="Issuing bodies, agencies, or companies")
    key_entities: Dict[str, Any] = Field(default_factory=dict, description="Key extracted fields, line items, or amounts")
    summary: str = Field(description="Concise 2-3 sentence summary of document contents")

class CitationItem(BaseModel):
    chunk_id: str
    page_number: int
    text_snippet: str
    score: float
    method: str
    section_title: Optional[str] = None

class ChatMessage(BaseModel):
    role: str # "user" | "assistant" | "system"
    content: str

class ChatRequest(BaseModel):
    pdf_name: str
    page_number: int = 1
    messages: List[ChatMessage]
    model: Optional[str] = None
    retrieval_mode: Optional[str] = "ocr"  # "ocr", "dense_rag", "hybrid_rag", "compare"

class ChatResponse(BaseModel):
    reply: str
    model_used: str
    tokens_used: int = 0
    retrieval_mode: str = "ocr"
    citations: List[CitationItem] = Field(default_factory=list)
    comparison_data: Optional[Dict[str, Any]] = None

class RAGQueryRequest(BaseModel):
    filename: str
    query: str
    mode: Optional[str] = "hybrid"  # "hybrid", "dense", "bm25"
    top_k: Optional[int] = 4

class RAGQueryResponse(BaseModel):
    query: str
    filename: str
    mode: str
    execution_time_ms: float
    total_indexed_chunks: int
    citations: List[CitationItem]
    combined_context: str


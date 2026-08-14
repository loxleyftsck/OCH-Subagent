import json
import re
import logging
from typing import Dict, Any, Optional

from src.agents.base_agent import BaseSubagent
from src.client.base_client import base_client
from src.config import settings
from src.cache.local_cache import local_cache

logger = logging.getLogger("parser_agent")


PARSER_SYSTEM_PROMPT = """You are an expert Document & Receipt Intelligence AI.
Analyze the OCR raw text and extract structured information strictly in JSON format.

If the document is a RECEIPT / STRUK BELANJA / INVOICE:
{
  "document_type": "Struk Belanja / Receipt",
  "merchant_name": "Nama Toko / Minimarket / Restoran",
  "transaction_date": "DD/MM/YYYY or YYYY-MM-DD",
  "transaction_time": "HH:MM:SS or null",
  "receipt_number": "Nomor Struk / Invoice #",
  "cashier": "Nama Kasir / ID Kasir",
  "items": [
    {
      "name": "Nama Produk / Barang",
      "qty": 1,
      "unit_price": 10000,
      "total_price": 10000
    }
  ],
  "subtotal": 25000,
  "discount": 0,
  "tax": 2500,
  "total_amount": 27500,
  "payment_method": "Cash / QRIS / Debit / Credit",
  "change_amount": 0,
  "summary": "Ringkasan transaksi pembelian"
}

If the document is a GENERAL / GOVERNMENT / REPORT DOCUMENT:
{
  "document_type": "Government Document / Report / Memo / Official Letter",
  "document_title": "Judul atau Heading Utama Dokumen",
  "reference_number": "Nomor Dokumen / SK / Surat",
  "dates": ["Daftar tanggal"],
  "organizations": ["Nama Lembaga / Instansi"],
  "key_entities": {
    "key_1": "value"
  },
  "summary": "Ringkasan isi dokumen"
}

Output ONLY valid JSON inside ```json ``` block or plain JSON.
"""

class ParserAgent(BaseSubagent):
    """Subagent specialized in converting raw OCR text into verified JSON structure (Receipts & Documents)."""
    def __init__(self):
        super().__init__(name="StructuringParserSubagent", model=settings.TEXT_MODEL)

    async def process(self, raw_text: str, image_hash: Optional[str] = None) -> Dict[str, Any]:
        logger.info(f"🤖 [{self.name}] Structuring OCR text using {self.model}...")

        # If cache already has structured JSON for this hash, use it
        if image_hash:
            cached = local_cache.get(image_hash)
            if cached and cached.get("structured_json"):
                logger.info(f"⚡ [{self.name}] Using cached structured JSON for hash: {image_hash[:10]}...")
                return cached["structured_json"]

        messages = [
            {"role": "system", "content": PARSER_SYSTEM_PROMPT},
            {"role": "user", "content": f"Here is the OCR raw text:\n\n{raw_text}\n\nParse into the appropriate JSON structure:"}
        ]

        response = await base_client.post_chat_completion(
            model=self.model,
            messages=messages,
            max_tokens=1500,
            temperature=0.1,
            is_ocr=False
        )

        content = response["choices"][0]["message"]["content"]
        
        candidates = []

        # 1. Extract all code fence JSON blocks (greedy & non-greedy)
        for m in re.finditer(r"```(?:json)?\s*([\s\S]*?)\s*```", content):
            fence_content = m.group(1).strip()
            # Find outermost balanced { ... } within fence
            start_i = fence_content.find("{")
            end_i = fence_content.rfind("}")
            if start_i != -1 and end_i > start_i:
                block = fence_content[start_i:end_i + 1]
                try:
                    candidates.append(json.loads(block))
                except Exception:
                    try:
                        fixed = re.sub(r",\s*([\]}])", r"\1", block)
                        candidates.append(json.loads(fixed))
                    except Exception:
                        pass

        # 2. Extract balanced curly brace blocks from whole content
        for start_idx in [i for i, c in enumerate(content) if c == "{"]:
            open_b = 0
            for end_idx in range(start_idx, len(content)):
                if content[end_idx] == "{":
                    open_b += 1
                elif content[end_idx] == "}":
                    open_b -= 1
                    if open_b == 0:
                        block = content[start_idx:end_idx + 1].strip()
                        try:
                            candidates.append(json.loads(block))
                        except Exception:
                            try:
                                fixed = re.sub(r",\s*([\]}])", r"\1", block)
                                candidates.append(json.loads(fixed))
                            except Exception:
                                pass
                        break

        # Pick candidate with the most keys (root document object)
        parsed_data = None
        if candidates:
            candidates.sort(key=lambda d: len(d.keys()) if isinstance(d, dict) else 0, reverse=True)
            parsed_data = candidates[0]


        if parsed_data:
            validated = parsed_data
        else:
            logger.warning("⚠️ No valid JSON block found in LLM output. Falling back to dynamic heuristic extraction.")
            lines = [l.strip() for l in raw_text.split("\n") if l.strip() and not l.strip().startswith(("-", "=", "#"))]
            first_line = lines[0] if lines else "Parsed Document"
            
            # Heuristic receipt detection
            is_rcpt = any(kw in raw_text.lower() for kw in ["struk", "receipt", "total", "subtotal", "cash", "kasir", "change", "tax", "vat"])
            
            total_val = None
            total_matches = re.findall(r"(?:total|amount|grand total|bayar)\s*[:=]?\s*(?:[€$£]|rp\.?)?\s*([\d\.,]+)", raw_text, re.IGNORECASE)
            if total_matches:
                try:
                    clean_num = total_matches[-1].replace(".", "").replace(",", ".")
                    total_val = float(clean_num)
                except Exception:
                    pass

            validated = {
                "document_type": "Struk Belanja / Receipt" if is_rcpt else "Generic Document",
                "merchant_name": first_line if is_rcpt else None,
                "document_title": first_line if not is_rcpt else "Struk Belanja",
                "total_amount": total_val,
                "summary": (content[:300] if content else raw_text[:300])
            }




        # Update cache with structured JSON
        if image_hash:
            local_cache.update_structured_json(image_hash, validated)

        return validated



parser_agent = ParserAgent()

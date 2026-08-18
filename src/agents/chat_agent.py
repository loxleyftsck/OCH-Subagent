import logging
from typing import List, Dict, Any, Optional
from src.agents.base_agent import BaseSubagent
from src.client.base_client import base_client
from src.config import settings

logger = logging.getLogger("chat_agent")

import re

def clean_reasoning_text(text: str) -> str:
    """Filter out internal model chain-of-thought traces so the response is clean and human-friendly."""
    if not text:
        return ""
    
    # 1. Remove <think>...</think> blocks
    if "<think>" in text:
        if "</think>" in text:
            text = text.split("</think>")[-1].strip()
        else:
            # If think was truncated without closing tag
            text = re.sub(r"<think>[\s\S]*", "", text).strip()
    
    # 2. Check if thinking process keywords exist
    thinking_indicators = [
        "Here's a thinking process:",
        "Thinking Process:",
        "1. **Analyze User Input",
        "1. **Analyze User Input:**",
        "**Analyze User Input**",
        "1.  **Analyze User Input"
    ]
    
    has_thinking = any(ind in text for ind in thinking_indicators)
    
    if has_thinking:
        # Check if an explicit Draft / Output / Final Answer section exists
        draft_markers = [
            "Draft:",
            "Draft Response:",
            "Output:",
            "Final Answer:",
            "Answer:",
            "Formulate Response (Internal Refinement - Indonesian):",
            "Formulate Response (in Indonesian, matching user's language):",
            "Formulate Response:"
        ]
        
        for marker in draft_markers:
            if marker in text:
                parts = text.split(marker)
                candidate = parts[-1].strip()
                # Remove any trailing self-correction or verification notes
                for end_marker in ["5. **Self-Correction", "Self-Correction/Verification", "**Self-Correction", "Self-Correction:"]:
                    if end_marker in candidate:
                        candidate = candidate.split(end_marker)[0].strip()
                if len(candidate) > 15:
                    return candidate

        # Fallback line-by-line filtering: remove thought lines
        lines = text.split("\n")
        filtered_lines = []
        is_in_thought = False
        
        for line in lines:
            trimmed = line.strip()
            # If line starts with thinking step
            if re.match(r"^\d+\.\s+\*\*(Analyze|Extract|Perform|Formulate|Self-Correction|Identify)", trimmed) or \
               trimmed.startswith(("Here's a thinking process", "Thinking Process:", "- Language:", "- Question:", "- Key tasks:", "Prices:", "- Note:", "Most expensive:", "Cheapest:", "Sum:")):
                is_in_thought = True
            elif trimmed.startswith(("Berdasarkan", "Halo", "Untuk", "Total", "Berikut", "Barang", "Item")):
                is_in_thought = False
            
            if not is_in_thought and trimmed:
                filtered_lines.append(line)
        
        if filtered_lines:
            return "\n".join(filtered_lines).strip()

    return text.strip()

class ChatAgent(BaseSubagent):
    """Subagent for interactive Q&A and conversation grounded on document contents."""
    def __init__(self, model: Optional[str] = None):
        selected_model = model or settings.CHAT_MODEL
        super().__init__(name="DocumentChatSubagent", model=selected_model)

    async def process(
        self,
        messages: List[Dict[str, str]],
        document_text: str,
        document_meta: Optional[Dict[str, Any]] = None,
        model_override: Optional[str] = None
    ) -> Dict[str, Any]:
        target_model = model_override or self.model
        logger.info(f"🤖 [{self.name}] Processing chat query with model {target_model}...")

        # Remove any error or system logs that might have leaked into user history
        cleaned_messages = []
        for msg in messages:
            content = msg["content"]
            # Clean if error message was accidentally appended
            if "⚠️ Terjadi kendala:" in content:
                content = content.split("⚠️ Terjadi kendala:")[0].strip()
            if content:
                cleaned_messages.append({"role": msg["role"], "content": content})

        retrieval_mode_label = "Hybrid RAG (BM25 + Dense Vector + RRF)" if "hybrid" in str(model_override or "") else "Document Context"
        
        system_instruction = (
            "You are an intelligent, polite, and helpful Document Assistant Subagent. You have direct access to the extracted "
            "document text and relevant context chunks.\n\n"
            "=== DOCUMENT RETRIEVAL CONTEXT ===\n"
            f"{document_text}\n"
            "==================================\n"
            "IMPORTANT RULES:\n"
            "1. Answer the user's question directly, clearly, and politely in Indonesian (or the language asked).\n"
            "2. Always cite specific page numbers (e.g. `[Halaman X]` or `[Pasal Y, Halaman X]`) when referencing information from the document.\n"
            "3. If the context contains multiple pages or sections, synthesize the answer comprehensively.\n"
            "4. Provide accurate calculations step-by-step with clean markdown bullet points.\n"
            "5. DO NOT output any internal thinking steps, chain-of-thought logs, or 'Here's a thinking process:'. Output ONLY the final user-facing response."
        )

        formatted_messages = [{"role": "system", "content": system_instruction}]
        for msg in cleaned_messages:
            formatted_messages.append({"role": msg["role"], "content": msg["content"]})

        response = await base_client.post_chat_completion(
            model=target_model,
            messages=formatted_messages,
            max_tokens=2000,
            temperature=0.2,
            is_ocr=False
        )

        raw_reply = response["choices"][0]["message"]["content"]
        cleaned_reply = clean_reasoning_text(raw_reply)
        tokens = response.get("usage", {}).get("total_tokens", 0)

        return {
            "reply": cleaned_reply,
            "model_used": target_model,
            "tokens_used": tokens
        }

chat_agent = ChatAgent()



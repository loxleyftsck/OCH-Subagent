import logging
from typing import List, Dict, Any, Optional
from src.agents.base_agent import BaseSubagent
from src.client.base_client import base_client
from src.config import settings

logger = logging.getLogger("chat_agent")

def clean_reasoning_text(text: str) -> str:
    """Filter out internal model chain-of-thought traces so the response is clean and human-friendly."""
    if not text:
        return ""
    
    # 1. Remove <think>...</think> blocks
    if "<think>" in text and "</think>" in text:
        text = text.split("</think>")[-1].strip()
    
    # 2. If it leaked thinking process text
    if "Here's a thinking process:" in text or "Thinking Process:" in text:
        # Check if there is a Draft / Output section
        for marker in ["Draft:", "Draft Response:", "Output:", "Final Answer:", "Answer:"]:
            if marker in text:
                parts = text.split(marker)
                candidate = parts[-1].strip()
                # Remove any self-correction trailing section if present
                if "**Self-Correction" in candidate:
                    candidate = candidate.split("**Self-Correction")[0].strip()
                if "Self-Correction:" in candidate:
                    candidate = candidate.split("Self-Correction:")[0].strip()
                if len(candidate) > 20:
                    return candidate

        # If thinking process took the whole message without explicit marker
        lines = text.split("\n")
        cleaned_lines = []
        skip = False
        for line in lines:
            if line.strip().startswith(("1. **Analyze", "2. **Identify", "3. **Perform", "4. **Formulate", "5. **Self-Correction", "**Analyze", "**Identify")):
                skip = True
            elif line.strip().startswith(("Berdasarkan", "Total", "Halo", "Untuk", "Berikut")):
                skip = False
            
            if not skip and line.strip():
                cleaned_lines.append(line)
        
        if cleaned_lines:
            return "\n".join(cleaned_lines).strip()

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

        system_instruction = (
            "You are an intelligent, friendly Document Assistant Subagent. You have direct access to the extracted OCR text "
            "and structured metadata of the user's active document.\n\n"
            "=== DOCUMENT CONTEXT ===\n"
            f"{document_text}\n"
            "========================\n"
            "INSTRUCTIONS:\n"
            "- Answer the user's question directly, politely, and clearly in the same language as the user (e.g. Indonesian).\n"
            "- Present calculations with clean bullet points and clear totals.\n"
            "- NEVER include internal thinking logs (like 'Thinking Process:', '1. Analyze User Input') in your final output.\n"
            "- Output ONLY the final conversational response meant for the human user."
        )

        formatted_messages = [{"role": "system", "content": system_instruction}]
        for msg in messages:
            formatted_messages.append({"role": msg["role"], "content": msg["content"]})

        response = await base_client.post_chat_completion(
            model=target_model,
            messages=formatted_messages,
            max_tokens=1500,
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


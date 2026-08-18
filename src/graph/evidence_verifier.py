import re
import logging
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from src.graph.legal_graph import LegalKnowledgeGraph, legal_kg

logger = logging.getLogger("graph.evidence_verifier")


class VerificationResult(BaseModel):
    is_verified: bool
    confidence_score: float
    verified_citations: List[str]
    missing_references: List[str]
    amendment_flags: List[str]
    verification_notes: str


class EvidenceVerifier:
    """Verifies factual grounding, article status, and cross-reference citations against the Legal Knowledge Graph."""

    def __init__(self, kg: LegalKnowledgeGraph = legal_kg):
        self.kg = kg

    def verify_query_and_context(self, query: str, retrieved_chunks: List[Any]) -> VerificationResult:
        """Cross-check query and chunks against graph to verify cross-references and legal hierarchy."""
        article_pattern = re.compile(r"Pasal\s+([0-9]+)", re.IGNORECASE)
        query_articles = article_pattern.findall(query)
        chunk_articles = []
        for c in retrieved_chunks:
            chunk_articles.extend(article_pattern.findall(getattr(c, "text_snippet", str(c))))

        all_detected_articles = list(set(query_articles + chunk_articles))
        verified_citations = []
        missing_references = []
        amendment_flags = []

        for art in all_detected_articles:
            subgraph = self.kg.traverse_subgraph(art, max_depth=1)
            if subgraph["primary_nodes"]:
                verified_citations.append(f"Pasal {art}")

                # Check if this article points to another article not yet in context
                for edge in subgraph["edges"]:
                    if edge["relation_type"] == "MERUJUK_KE":
                        ref_target = edge["target_id"].split("_PASAL_")[-1]
                        if ref_target not in all_detected_articles:
                            missing_references.append(f"Pasal {ref_target} (dirujuk oleh Pasal {art})")

                    elif edge["relation_type"] in ["MENGUBAH", "MENCABUT"]:
                        amendment_flags.append(edge["description"])

        confidence = 1.0 if verified_citations else 0.75
        if amendment_flags:
            confidence *= 0.9

        notes = (
            f"Terverifikasi {len(verified_citations)} pasal dalam naskah peraturan. "
            f"{f'Ditemukan rujukan silang: {missing_references}. ' if missing_references else ''}"
            f"{f'Catatan Perubahan: {amendment_flags}.' if amendment_flags else ''}"
        )

        return VerificationResult(
            is_verified=len(verified_citations) > 0,
            confidence_score=round(confidence, 2),
            verified_citations=verified_citations,
            missing_references=missing_references,
            amendment_flags=amendment_flags,
            verification_notes=notes
        )


evidence_verifier = EvidenceVerifier()

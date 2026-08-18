import time
import logging
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from src.rag.hybrid_retriever import hybrid_retriever, RetrievalCitation
from src.graph.legal_graph import legal_kg
from src.graph.evidence_verifier import evidence_verifier, VerificationResult

logger = logging.getLogger("rag.agentic_graph_rag")


class GraphRAGResult(BaseModel):
    query: str
    filename: str
    execution_time_ms: float
    retrieval_citations: List[RetrievalCitation]
    graph_context: str
    verification: VerificationResult
    final_grounded_context: str


class AgenticGraphRAG:
    """Agentic GraphRAG combining BM25, Dense Vector, Legal Knowledge Graph, and Evidence Verification."""

    def __init__(self):
        self.retriever = hybrid_retriever
        self.kg = legal_kg
        self.verifier = evidence_verifier

    def index_document_with_graph(self, file_path: Path):
        """Index chunks in both Hybrid RAG and Legal Knowledge Graph."""
        doc_index = self.retriever.index_document(file_path)
        self.kg.build_graph_from_chunks(doc_index.chunks, filename=file_path.name)
        return doc_index

    def execute_agentic_pipeline(self, file_path: Path, query: str, top_k: int = 4) -> GraphRAGResult:
        """Run complete Agentic GraphRAG flow: Planner -> Hybrid Search -> Graph Traversal -> Verification."""
        filename = file_path.name
        start_t = time.perf_counter()

        # 1. Ensure indexed in both RAG and Graph
        if not self.retriever.is_indexed(filename):
            self.index_document_with_graph(file_path)

        # 2. Hybrid Retrieval (BM25 + Dense RRF)
        rag_res = self.retriever.retrieve(file_path, query, mode="hybrid", top_k=top_k)

        # 3. Query Planner & Graph Subgraph Extraction
        article_pattern = re.compile(r"Pasal\s+([0-9]+)", re.IGNORECASE)
        articles_in_query = article_pattern.findall(query)
        if not articles_in_query:
            # Check articles in retrieved chunks
            for cit in rag_res.citations:
                found = article_pattern.findall(cit.text_snippet)
                if found:
                    articles_in_query.extend(found)

        graph_context = ""
        subgraphs = []
        for art_num in list(set(articles_in_query))[:3]:
            subgraph = self.kg.traverse_subgraph(art_num, max_depth=2)
            subgraphs.append(subgraph)
            formatted = self.kg.format_graph_context_for_prompt(subgraph)
            if formatted:
                graph_context += formatted + "\n"

        # 4. Evidence Verification
        verification = self.verifier.verify_query_and_context(query, rag_res.citations)

        # 5. Build final synthesis context
        verification_header = (
            f"=== EVIDENCE VERIFICATION STATUS ===\n"
            f"Status: {'VERIFIED 🟢' if verification.is_verified else 'CAUTION ⚠️'} (Confidence: {int(verification.confidence_score*100)}%)\n"
            f"Catatan: {verification.verification_notes}\n"
            f"====================================\n\n"
        )

        final_grounded_context = (
            f"{verification_header}"
            f"=== RETRIEVED STATUTORY ARTICLES ===\n"
            f"{rag_res.combined_context}\n\n"
            f"{graph_context}"
        )

        duration_ms = (time.perf_counter() - start_t) * 1000

        return GraphRAGResult(
            query=query,
            filename=filename,
            execution_time_ms=round(duration_ms, 3),
            retrieval_citations=rag_res.citations,
            graph_context=graph_context,
            verification=verification,
            final_grounded_context=final_grounded_context
        )


agentic_graph_rag = AgenticGraphRAG()

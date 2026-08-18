import time
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Literal
from pydantic import BaseModel

from src.config import settings
from src.rag.chunker import DocumentChunker, DocumentChunk
from src.rag.bm25_engine import BM25Engine
from src.rag.vector_engine import VectorEngine

logger = logging.getLogger("rag.hybrid_retriever")


class RetrievalCitation(BaseModel):
    chunk_id: str
    page_number: int
    text_snippet: str
    score: float
    method: str  # "hybrid", "dense", or "bm25"
    section_title: Optional[str] = None


class RetrievalResult(BaseModel):
    query: str
    filename: str
    mode: str
    execution_time_ms: float
    total_indexed_chunks: int
    citations: List[RetrievalCitation]
    combined_context: str


class DocumentIndex:
    """Holds chunk, BM25, and vector index for a single document."""
    def __init__(self, filename: str, chunks: List[DocumentChunk]):
        self.filename = filename
        self.chunks = chunks
        self.bm25 = BM25Engine()
        self.bm25.index(chunks)
        self.vector = VectorEngine()
        self.vector.index(chunks)
        self.indexed_at = time.time()


class HybridRetriever:
    """Multi-document Hybrid RAG retriever with Reciprocal Rank Fusion."""

    def __init__(self):
        self.chunker = DocumentChunker(chunk_size=700, chunk_overlap=120)
        self.indexes: Dict[str, DocumentIndex] = {}

    def is_indexed(self, filename: str) -> bool:
        return filename in self.indexes

    def get_index_stats(self, filename: str) -> Dict[str, Any]:
        if filename not in self.indexes:
            return {"indexed": False, "chunk_count": 0}
        idx = self.indexes[filename]
        return {
            "indexed": True,
            "filename": filename,
            "chunk_count": len(idx.chunks),
            "indexed_at": idx.indexed_at
        }

    def index_document(self, file_path: Path) -> DocumentIndex:
        """Parse, chunk, and index a document in BM25 & Vector engines."""
        filename = file_path.name
        start_t = time.time()
        logger.info(f"Indexing document {filename} for Hybrid RAG...")

        chunks = self.chunker.chunk_document(file_path)
        doc_index = DocumentIndex(filename=filename, chunks=chunks)
        self.indexes[filename] = doc_index

        duration = (time.time() - start_t) * 1000
        logger.info(f"Indexed {filename} ({len(chunks)} chunks) in {duration:.1f}ms")
        return doc_index

    def retrieve(
        self,
        file_path: Path,
        query: str,
        mode: Literal["hybrid", "dense", "bm25"] = "hybrid",
        top_k: int = 4,
        rrf_k: int = 60
    ) -> RetrievalResult:
        """Execute retrieval across BM25, Dense Vector, or Hybrid RRF."""
        filename = file_path.name
        start_t = time.time()

        if filename not in self.indexes:
            self.index_document(file_path)

        doc_index = self.indexes[filename]
        if not doc_index.chunks:
            return RetrievalResult(
                query=query,
                filename=filename,
                mode=mode,
                execution_time_ms=0.0,
                total_indexed_chunks=0,
                citations=[],
                combined_context="[Dokumen kosong atau tidak memiliki teks yang dapat diekstrak]"
            )

        citations: List[RetrievalCitation] = []

        if mode == "bm25":
            bm25_results = doc_index.bm25.search(query, top_k=top_k)
            for chunk, score in bm25_results:
                citations.append(
                    RetrievalCitation(
                        chunk_id=chunk.chunk_id,
                        page_number=chunk.page_number,
                        text_snippet=chunk.text,
                        score=round(score, 3),
                        method="bm25",
                        section_title=chunk.section_title
                    )
                )

        elif mode == "dense":
            dense_results = doc_index.vector.search(query, top_k=top_k)
            for chunk, score in dense_results:
                citations.append(
                    RetrievalCitation(
                        chunk_id=chunk.chunk_id,
                        page_number=chunk.page_number,
                        text_snippet=chunk.text,
                        score=round(score, 3),
                        method="dense",
                        section_title=chunk.section_title
                    )
                )

        else:  # Hybrid (RRF Fusion)
            bm25_results = doc_index.bm25.search(query, top_k=top_k * 2)
            dense_results = doc_index.vector.search(query, top_k=top_k * 2)

            rrf_scores: Dict[str, float] = {}
            chunk_map: Dict[str, DocumentChunk] = {}
            methods_seen: Dict[str, List[str]] = {}

            # Add BM25 ranks
            for rank, (chunk, score) in enumerate(bm25_results):
                cid = chunk.chunk_id
                chunk_map[cid] = chunk
                rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (1.0 / (rrf_k + rank + 1))
                methods_seen.setdefault(cid, []).append("bm25")

            # Add Dense ranks
            for rank, (chunk, score) in enumerate(dense_results):
                cid = chunk.chunk_id
                chunk_map[cid] = chunk
                rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (1.0 / (rrf_k + rank + 1))
                methods_seen.setdefault(cid, []).append("dense")

            # Sort by RRF score descending
            sorted_rrf = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]

            for cid, rrf_score in sorted_rrf:
                chunk = chunk_map[cid]
                method_label = "hybrid (bm25+dense)" if len(methods_seen[cid]) > 1 else methods_seen[cid][0]
                citations.append(
                    RetrievalCitation(
                        chunk_id=chunk.chunk_id,
                        page_number=chunk.page_number,
                        text_snippet=chunk.text,
                        score=round(rrf_score * 100, 3),  # Scaled for readability
                        method=method_label,
                        section_title=chunk.section_title
                    )
                )

        exec_time = (time.time() - start_t) * 1000

        # Build clean combined context with page citation markers
        context_blocks = []
        for cit in citations:
            sec_info = f" - {cit.section_title}" if cit.section_title else ""
            context_blocks.append(f"--- [Halaman {cit.page_number}{sec_info}] ---\n{cit.text_snippet}")

        combined_context = "\n\n".join(context_blocks) if context_blocks else "[Tidak ada bagian dokumen yang cocok dengan query]"

        return RetrievalResult(
            query=query,
            filename=filename,
            mode=mode,
            execution_time_ms=round(exec_time, 2),
            total_indexed_chunks=len(doc_index.chunks),
            citations=citations,
            combined_context=combined_context
        )

    def compare_modes(self, file_path: Path, query: str, top_k: int = 3) -> Dict[str, Any]:
        """Run Dense, BM25, and Hybrid retrievals concurrently and compare results."""
        res_bm25 = self.retrieve(file_path, query, mode="bm25", top_k=top_k)
        res_dense = self.retrieve(file_path, query, mode="dense", top_k=top_k)
        res_hybrid = self.retrieve(file_path, query, mode="hybrid", top_k=top_k)

        return {
            "query": query,
            "filename": file_path.name,
            "comparison": {
                "bm25": {
                    "execution_time_ms": res_bm25.execution_time_ms,
                    "top_pages": [c.page_number for c in res_bm25.citations],
                    "citations": [c.model_dump() for c in res_bm25.citations]
                },
                "dense": {
                    "execution_time_ms": res_dense.execution_time_ms,
                    "top_pages": [c.page_number for c in res_dense.citations],
                    "citations": [c.model_dump() for c in res_dense.citations]
                },
                "hybrid": {
                    "execution_time_ms": res_hybrid.execution_time_ms,
                    "top_pages": [c.page_number for c in res_hybrid.citations],
                    "citations": [c.model_dump() for c in res_hybrid.citations]
                }
            }
        }


hybrid_retriever = HybridRetriever()

import math
import re
from typing import List, Dict, Tuple, Any
from collections import Counter
from src.rag.chunker import DocumentChunk


def tokenize(text: str) -> List[str]:
    """Tokenize text into lowercase words while preserving law/article patterns."""
    text = text.lower()
    # Normalize punctuation but keep alphanumeric and hyphens
    tokens = re.findall(r"\b[a-z0-9\-_/]+\b", text)
    return tokens


class BM25Engine:
    """Fast, zero-dependency BM25Okapi lexical retrieval engine."""

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.chunks: List[DocumentChunk] = []
        self.corpus_size: int = 0
        self.avg_doc_len: float = 0.0
        self.doc_lens: List[int] = []
        self.doc_freqs: Dict[str, int] = {}
        self.doc_token_counts: List[Counter] = []
        self.idf: Dict[str, float] = {}

    def index(self, chunks: List[DocumentChunk]):
        """Index a collection of document chunks."""
        self.chunks = chunks
        self.corpus_size = len(chunks)
        if self.corpus_size == 0:
            return

        self.doc_token_counts = []
        self.doc_lens = []
        self.doc_freqs = Counter()

        total_len = 0
        for chunk in chunks:
            tokens = tokenize(chunk.text)
            t_count = Counter(tokens)
            self.doc_token_counts.append(t_count)
            doc_l = len(tokens)
            self.doc_lens.append(doc_l)
            total_len += doc_l

            for word in t_count.keys():
                self.doc_freqs[word] += 1

        self.avg_doc_len = total_len / self.corpus_size if self.corpus_size > 0 else 1.0

        # Calculate IDF for all seen tokens
        self.idf = {}
        for word, freq in self.doc_freqs.items():
            # Standard Lucene/BM25 IDF formula with smoothing
            self.idf[word] = math.log(1.0 + (self.corpus_size - freq + 0.5) / (freq + 0.5))

    def search(self, query: str, top_k: int = 5) -> List[Tuple[DocumentChunk, float]]:
        """Search indexed chunks and return top_k results with BM25 scores."""
        if self.corpus_size == 0:
            return []

        query_tokens = tokenize(query)
        if not query_tokens:
            return []

        scores = [0.0] * self.corpus_size

        for q_token in query_tokens:
            idf_val = self.idf.get(q_token, 0.0)
            if idf_val <= 0:
                continue

            for idx, token_counter in enumerate(self.doc_token_counts):
                tf = token_counter.get(q_token, 0)
                if tf > 0:
                    doc_len = self.doc_lens[idx]
                    denominator = tf + self.k1 * (1.0 - self.b + self.b * (doc_len / self.avg_doc_len))
                    term_score = idf_val * ((tf * (self.k1 + 1.0)) / denominator)
                    scores[idx] += term_score

        # Boost exact phrase matches or article numbers in text
        q_lower = query.lower().strip()
        for idx, chunk in enumerate(self.chunks):
            if q_lower in chunk.text.lower():
                scores[idx] *= 1.35

        # Pair with chunk and sort
        scored_results = [(self.chunks[i], scores[i]) for i in range(self.corpus_size) if scores[i] > 0]
        scored_results.sort(key=lambda x: x[1], reverse=True)

        return scored_results[:top_k]

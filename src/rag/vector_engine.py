import math
import re
from typing import List, Dict, Tuple, Any
from collections import Counter
from src.rag.chunker import DocumentChunk


def extract_features(text: str) -> List[str]:
    """Extract word tokens, word bigrams, and character n-grams for semantic matching."""
    cleaned = re.sub(r"[^\w\s]", " ", text.lower())
    words = [w for w in cleaned.split() if len(w) > 1]
    features = []
    
    # 1. Individual words
    features.extend(words)
    
    # 2. Word bigrams for phrase matching (e.g. "upah minimum", "cipta kerja", "hak cipta")
    for i in range(len(words) - 1):
        features.append(f"{words[i]}_{words[i+1]}")
        
    # 3. Character subword n-grams
    for word in words:
        if len(word) >= 4:
            for n in (3, 4):
                for i in range(len(word) - n + 1):
                    features.append(f"#{word[i:i+n]}")
                    
    return features


class VectorEngine:
    """Dense Semantic Vector Search Engine using Subword & N-Gram TF-IDF with L2-normalized Cosine Similarity."""

    def __init__(self):
        self.chunks: List[DocumentChunk] = []
        self.vocabulary: Dict[str, int] = {}
        self.idf: Dict[str, float] = {}
        self.chunk_vectors: List[Dict[int, float]] = []
        self.chunk_norms: List[float] = []

    def index(self, chunks: List[DocumentChunk]):
        """Index chunks into normalized semantic vector space."""
        self.chunks = chunks
        num_docs = len(chunks)
        if num_docs == 0:
            return

        doc_feature_counts = []
        df = Counter()

        for chunk in chunks:
            feats = extract_features(chunk.text)
            counts = Counter(feats)
            doc_feature_counts.append(counts)
            for f in counts.keys():
                df[f] += 1

        self.vocabulary = {}
        self.idf = {}
        idx = 0
        for f, freq in df.items():
            self.vocabulary[f] = idx
            # Smooth IDF
            self.idf[f] = math.log((num_docs + 1.0) / (freq + 1.0)) + 1.0
            idx += 1

        self.chunk_vectors = []
        self.chunk_norms = []

        for counts in doc_feature_counts:
            vec: Dict[int, float] = {}
            sum_sq = 0.0
            for f, count in counts.items():
                if f in self.vocabulary:
                    v_idx = self.vocabulary[f]
                    # Bigrams and whole words have higher importance than subword hashes
                    boost = 1.8 if "_" in f else (1.2 if not f.startswith("#") else 0.4)
                    weight = (1.0 + math.log(count)) * self.idf[f] * boost
                    vec[v_idx] = weight
                    sum_sq += weight * weight

            norm = math.sqrt(sum_sq) if sum_sq > 0 else 1.0
            self.chunk_vectors.append(vec)
            self.chunk_norms.append(norm)

    def search(self, query: str, top_k: int = 5) -> List[Tuple[DocumentChunk, float]]:
        """Compute Cosine Similarity between query vector and indexed document vectors."""
        if not self.chunks or not self.vocabulary:
            return []

        q_feats = extract_features(query)
        q_counts = Counter(q_feats)

        q_vec: Dict[int, float] = {}
        q_sum_sq = 0.0
        for f, count in q_counts.items():
            if f in self.vocabulary:
                v_idx = self.vocabulary[f]
                boost = 1.8 if "_" in f else (1.2 if not f.startswith("#") else 0.4)
                weight = (1.0 + math.log(count)) * self.idf[f] * boost
                q_vec[v_idx] = weight
                q_sum_sq += weight * weight

        q_norm = math.sqrt(q_sum_sq) if q_sum_sq > 0 else 1.0
        if not q_vec or q_norm == 0:
            return []

        results = []
        for i in range(len(self.chunks)):
            doc_vec = self.chunk_vectors[i]
            doc_norm = self.chunk_norms[i]

            dot = 0.0
            for v_idx, q_w in q_vec.items():
                if v_idx in doc_vec:
                    dot += q_w * doc_vec[v_idx]

            cosine_sim = dot / (q_norm * doc_norm) if (q_norm * doc_norm) > 0 else 0.0
            if cosine_sim > 0.01:
                results.append((self.chunks[i], cosine_sim))

        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]

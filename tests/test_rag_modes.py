import sys
import unittest
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.rag.chunker import DocumentChunk, DocumentChunker
from src.rag.bm25_engine import BM25Engine
from src.rag.vector_engine import VectorEngine
from src.rag.hybrid_retriever import hybrid_retriever


class TestHybridRAGPipeline(unittest.TestCase):

    def setUp(self):
        # Create synthetic chunks resembling legal and government documents
        self.sample_chunks = [
            DocumentChunk(
                chunk_id="doc1_p1_c1",
                filename="UU_Sample.pdf",
                page_number=1,
                text="UNDANG-UNDANG REPUBLIK INDONESIA NOMOR 11 TAHUN 2020 TENTANG CIPTA KERJA. BAB I KETENTUAN UMUM.",
                section_title="BAB I"
            ),
            DocumentChunk(
                chunk_id="doc1_p2_c2",
                filename="UU_Sample.pdf",
                page_number=2,
                text="Pasal 18 ayat 1: Setiap pengusaha wajib memberikan waktu istirahat dan cuti kepada pekerja atau buruh.",
                section_title="Pasal 18"
            ),
            DocumentChunk(
                chunk_id="doc1_p3_c3",
                filename="UU_Sample.pdf",
                page_number=3,
                text="Pasal 27: Pengaturan mengenai upah minimum provinsi dan upah minimum kabupaten ditetapkan oleh Gubernur.",
                section_title="Pasal 27"
            ),
            DocumentChunk(
                chunk_id="doc1_p4_c4",
                filename="UU_Sample.pdf",
                page_number=4,
                text="BAB IV KETENAGAKERJAAN. Pemutusan Hubungan Kerja (PHK) harus dirundingkan terlebih dahulu antara pengusaha dan serikat pekerja.",
                section_title="BAB IV"
            ),
            DocumentChunk(
                chunk_id="doc1_p5_c5",
                filename="UU_Sample.pdf",
                page_number=5,
                text="Sanksi administratif bagi pelanggaran izin lingkungan hidup berupa teguran tertulis, denda administratif, atau pencabutan izin usaha.",
                section_title="Sanksi"
            )
        ]

    def test_bm25_exact_article_retrieval(self):
        engine = BM25Engine()
        engine.index(self.sample_chunks)
        results = engine.search("Pasal 18", top_k=2)
        self.assertTrue(len(results) > 0)
        top_chunk, score = results[0]
        self.assertEqual(top_chunk.page_number, 2)
        self.assertIn("Pasal 18", top_chunk.text)

    def test_vector_semantic_retrieval(self):
        engine = VectorEngine()
        engine.index(self.sample_chunks)
        results = engine.search("upah minimum provinsi gubernur", top_k=2)
        self.assertTrue(len(results) > 0)
        top_chunk, score = results[0]
        self.assertEqual(top_chunk.page_number, 3)
        self.assertIn("upah minimum", top_chunk.text)

    def test_hybrid_rrf_retrieval_on_pdf(self):
        test_file = Path("data/govdocs/UU_Nomor_1_Tahun_1965.pdf")
        if test_file.exists():
            res = hybrid_retriever.retrieve(test_file, query="Pengadilan Tinggi Denpasar", mode="hybrid", top_k=3)
            self.assertEqual(res.mode, "hybrid")
            self.assertTrue(len(res.citations) > 0)
            self.assertGreater(res.total_indexed_chunks, 0)
            print(f"Hybrid retrieval returned {len(res.citations)} citations in {res.execution_time_ms}ms")

    def test_comparison_modes(self):
        test_file = Path("data/govdocs/UU_Nomor_1_Tahun_1965.pdf")
        if test_file.exists():
            comparison = hybrid_retriever.compare_modes(test_file, query="Pengadilan Tinggi", top_k=2)
            self.assertIn("comparison", comparison)
            self.assertIn("bm25", comparison["comparison"])
            self.assertIn("dense", comparison["comparison"])
            self.assertIn("hybrid", comparison["comparison"])


if __name__ == "__main__":
    unittest.main()

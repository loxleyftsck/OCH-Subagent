import re
import logging
from typing import List, Dict, Any, Optional, Set, Tuple
from pydantic import BaseModel, Field

logger = logging.getLogger("graph.legal_kg")


class LegalNode(BaseModel):
    node_id: str
    node_type: str  # "REGULATION", "CHAPTER", "ARTICLE", "CLAUSE", "TOPIC"
    label: str
    filename: str
    page_number: int
    text: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class LegalEdge(BaseModel):
    source_id: str
    target_id: str
    relation_type: str  # "BAGIAN_DARI", "MERUJUK_KE", "MENGUBAH", "MENCABUT", "PELAKSANAAN_DARI"
    description: Optional[str] = None
    weight: float = 1.0


class LegalKnowledgeGraph:
    """In-memory lightweight Knowledge Graph specialized for Indonesian Legal Documents."""

    def __init__(self):
        self.nodes: Dict[str, LegalNode] = {}
        self.edges: List[LegalEdge] = []
        self.adjacency: Dict[str, List[LegalEdge]] = {}
        self.reverse_adjacency: Dict[str, List[LegalEdge]] = {}

    def add_node(self, node: LegalNode):
        self.nodes[node.node_id] = node
        if node.node_id not in self.adjacency:
            self.adjacency[node.node_id] = []
        if node.node_id not in self.reverse_adjacency:
            self.reverse_adjacency[node.node_id] = []

    def add_edge(self, edge: LegalEdge):
        self.edges.append(edge)
        self.adjacency.setdefault(edge.source_id, []).append(edge)
        self.reverse_adjacency.setdefault(edge.target_id, []).append(edge)

    def build_graph_from_chunks(self, chunks: List[Any], filename: str):
        """Extract legal entities (Bab, Pasal, Ayat, Rujukan) and construct the knowledge graph."""
        reg_node_id = f"REG_{filename}"
        reg_node = LegalNode(
            node_id=reg_node_id,
            node_type="REGULATION",
            label=filename.replace(".pdf", "").replace("_", " "),
            filename=filename,
            page_number=1,
            text=f"Dokumen Regulasi {filename}"
        )
        self.add_node(reg_node)

        current_chapter_id = None
        current_chapter_label = "BAB I"

        # Regex patterns for Indonesian Legal Structure
        chapter_regex = re.compile(r"BAB\s+([IVXLCDM]+|[0-9]+)\s*([^\n\.]*)", re.IGNORECASE)
        article_regex = re.compile(r"Pasal\s+([0-9]+)", re.IGNORECASE)
        cross_ref_regex = re.compile(r"(sebagaimana dimaksud dalam|berdasarkan|sesuai dengan)?\s*Pasal\s+([0-9]+)(\s+ayat\s*\(([0-9]+)\))?", re.IGNORECASE)
        amend_regex = re.compile(r"(mengubah|mencabut|atas perubahan)\s+Undang-Undang\s+Nomor\s+([0-9]+)\s+Tahun\s+([0-9]+)", re.IGNORECASE)

        for chunk in chunks:
            text = chunk.text
            page_num = chunk.page_number
            chunk_id = chunk.chunk_id

            # 1. Detect Chapter / BAB
            chap_match = chapter_regex.search(text)
            if chap_match:
                chap_num = chap_match.group(1).upper()
                chap_title = chap_match.group(2).strip()
                current_chapter_id = f"{filename}_BAB_{chap_num}"
                current_chapter_label = f"BAB {chap_num}"

                if current_chapter_id not in self.nodes:
                    chap_node = LegalNode(
                        node_id=current_chapter_id,
                        node_type="CHAPTER",
                        label=f"BAB {chap_num} {chap_title}",
                        filename=filename,
                        page_number=page_num,
                        text=chap_match.group(0)
                    )
                    self.add_node(chap_node)
                    # Edge: BAB -> REGULATION
                    self.add_edge(LegalEdge(
                        source_id=current_chapter_id,
                        target_id=reg_node_id,
                        relation_type="BAGIAN_DARI",
                        description=f"Bab {chap_num} merupakan bagian dari regulasi"
                    ))

            # 2. Detect Articles / PASAL
            art_matches = article_regex.findall(text)
            for art_num in art_matches:
                art_node_id = f"{filename}_PASAL_{art_num}"
                if art_node_id not in self.nodes:
                    art_node = LegalNode(
                        node_id=art_node_id,
                        node_type="ARTICLE",
                        label=f"Pasal {art_num}",
                        filename=filename,
                        page_number=page_num,
                        text=text[:400]
                    )
                    self.add_node(art_node)

                    # Edge: Pasal -> Bab
                    target_parent = current_chapter_id or reg_node_id
                    self.add_edge(LegalEdge(
                        source_id=art_node_id,
                        target_id=target_parent,
                        relation_type="BAGIAN_DARI",
                        description=f"Pasal {art_num} termuat dalam {current_chapter_label}"
                    ))

                # 3. Detect Cross-References within Article text ("sebagaimana dimaksud dalam Pasal Y")
                for m in cross_ref_regex.finditer(text):
                    ref_art_num = m.group(2)
                    if ref_art_num != art_num:  # Avoid self-loop
                        target_ref_id = f"{filename}_PASAL_{ref_art_num}"
                        self.add_edge(LegalEdge(
                            source_id=art_node_id,
                            target_id=target_ref_id,
                            relation_type="MERUJUK_KE",
                            description=f"Pasal {art_num} merujuk ketentuan Pasal {ref_art_num}",
                            weight=1.5
                        ))

            # 4. Detect Amendment / Repeal relations (Mengubah / Mencabut UU Lain)
            for m in amend_regex.finditer(text):
                action = m.group(1).upper()
                uu_num = m.group(2)
                uu_yr = m.group(3)
                target_law_id = f"REG_UU_Nomor_{uu_num}_Tahun_{uu_yr}"
                rel_type = "MENCABUT" if "MENCABUT" in action else "MENGUBAH"
                
                self.add_edge(LegalEdge(
                    source_id=reg_node_id,
                    target_id=target_law_id,
                    relation_type=rel_type,
                    description=f"{filename} {rel_type.lower()} UU No. {uu_num} Tahun {uu_yr}",
                    weight=2.0
                ))

        logger.info(f"Knowledge Graph for {filename}: {len(self.nodes)} Nodes, {len(self.edges)} Edges extracted.")

    def traverse_subgraph(self, target_article_num: str, max_depth: int = 2) -> Dict[str, Any]:
        """Traverse connected nodes (hierarchies, references, amendments) for an article."""
        matched_nodes = [nid for nid in self.nodes if f"PASAL_{target_article_num}" in nid]
        if not matched_nodes:
            return {"primary_nodes": [], "related_nodes": [], "edges": []}

        visited_nodes: Set[str] = set()
        collected_edges: List[LegalEdge] = []

        queue = [(nid, 0) for nid in matched_nodes]
        for nid, _ in queue:
            visited_nodes.add(nid)

        while queue:
            curr_id, depth = queue.pop(0)
            if depth >= max_depth:
                continue

            # Forward edges
            for edge in self.adjacency.get(curr_id, []):
                collected_edges.append(edge)
                if edge.target_id not in visited_nodes and edge.target_id in self.nodes:
                    visited_nodes.add(edge.target_id)
                    queue.append((edge.target_id, depth + 1))

            # Backward edges (e.g. articles referencing this article)
            for edge in self.reverse_adjacency.get(curr_id, []):
                collected_edges.append(edge)
                if edge.source_id not in visited_nodes and edge.source_id in self.nodes:
                    visited_nodes.add(edge.source_id)
                    queue.append((edge.source_id, depth + 1))

        return {
            "primary_nodes": [self.nodes[nid].model_dump() for nid in matched_nodes],
            "related_nodes": [self.nodes[nid].model_dump() for nid in visited_nodes if nid not in matched_nodes],
            "edges": [e.model_dump() for e in collected_edges]
        }

    def format_graph_context_for_prompt(self, subgraph: Dict[str, Any]) -> str:
        """Format the extracted legal subgraph into clear structured Markdown for LLM ingestion."""
        if not subgraph or not subgraph.get("primary_nodes"):
            return ""

        lines = ["\n=== LEGAL KNOWLEDGE GRAPH RELATIONS ==="]
        for node in subgraph["primary_nodes"][:3]:
            lines.append(f"[Simpul Utama] {node['label']} (Halaman {node['page_number']})")

        if subgraph.get("edges"):
            lines.append("\n[Relasi Hukum Antar-Pasal & Hierarki]")
            for edge in subgraph["edges"][:6]:
                src = self.nodes.get(edge["source_id"], None)
                tgt = self.nodes.get(edge["target_id"], None)
                src_lbl = src.label if src else edge["source_id"]
                tgt_lbl = tgt.label if tgt else edge["target_id"]
                lines.append(f"  - [{src_lbl}] --({edge['relation_type']})--> [{tgt_lbl}] ({edge.get('description', '')})")

        if subgraph.get("related_nodes"):
            lines.append("\n[Rujukan Terkait]")
            for node in subgraph["related_nodes"][:3]:
                lines.append(f"  - {node['label']} (Halaman {node['page_number']}): {node['text'][:120]}...")

        lines.append("=========================================\n")
        return "\n".join(lines)



legal_kg = LegalKnowledgeGraph()

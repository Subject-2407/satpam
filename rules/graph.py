"""Indeks graph dalam memori untuk rule engine.

Diadaptasi dari `InMemoryGraph` sistem v1.0
(`src-old/backend/app/services/ai_engine/graph.py`), disederhanakan ke kontrak
8 tipe node dan 8 relation.

Yang disediakan hanya yang dibutuhkan aturan: tetangga per tipe relasi, tetangga
sejauh beberapa hop dengan batas, dan hitungan tetangga berbeda. Tidak ada
skoring di sini.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field

from rules.loader import RuleEdge, RuleNode


@dataclass
class RuleGraph:
    """Node, edge, dan indeks ketetanggaannya."""

    nodes: dict[str, RuleNode]
    edges: list[RuleEdge]
    _out: dict[str, list[int]] = field(default_factory=dict, repr=False)
    _in: dict[str, list[int]] = field(default_factory=dict, repr=False)

    @classmethod
    def build(cls, nodes: list[RuleNode], edges: list[RuleEdge]) -> RuleGraph:
        graph = cls(nodes={node.node_id: node for node in nodes}, edges=list(edges))
        for index, edge in enumerate(graph.edges):
            graph._out.setdefault(edge.src_id, []).append(index)
            graph._in.setdefault(edge.dst_id, []).append(index)
        return graph

    # -- akses edge ----------------------------------------------------

    def out_edges(self, node_id: str, rel_type: str | None = None) -> list[RuleEdge]:
        return [
            self.edges[index]
            for index in self._out.get(node_id, ())
            if rel_type is None or self.edges[index].rel_type == rel_type
        ]

    def in_edges(self, node_id: str, rel_type: str | None = None) -> list[RuleEdge]:
        return [
            self.edges[index]
            for index in self._in.get(node_id, ())
            if rel_type is None or self.edges[index].rel_type == rel_type
        ]

    def degree(self, node_id: str) -> int:
        return len(self._out.get(node_id, ())) + len(self._in.get(node_id, ()))

    # -- tetangga ------------------------------------------------------

    def sources(
        self,
        node_id: str,
        rel_type: str,
        node_type: str | None = None,
    ) -> set[str]:
        """Node berbeda yang mengarah ke `node_id` lewat `rel_type`."""
        result = set()
        for edge in self.in_edges(node_id, rel_type):
            source = self.nodes.get(edge.src_id)
            if source is None:
                continue
            if node_type is None or source.node_type == node_type:
                result.add(source.node_id)
        return result

    def targets(
        self,
        node_id: str,
        rel_type: str,
        node_type: str | None = None,
    ) -> set[str]:
        """Node berbeda yang dituju `node_id` lewat `rel_type`."""
        result = set()
        for edge in self.out_edges(node_id, rel_type):
            target = self.nodes.get(edge.dst_id)
            if target is None:
                continue
            if node_type is None or target.node_type == node_type:
                result.add(target.node_id)
        return result

    def adjacent(self, node_id: str) -> set[str]:
        """Seluruh tetangga langsung, tanpa memandang arah maupun tipe relasi."""
        result = set()
        for edge in self.out_edges(node_id):
            result.add(edge.dst_id)
        for edge in self.in_edges(node_id):
            result.add(edge.src_id)
        result.discard(node_id)
        return result

    def neighborhood(
        self,
        node_id: str,
        max_depth: int = 2,
        limit: int = 250,
    ) -> set[str]:
        """Node dalam jangkauan `max_depth` hop, termasuk `node_id` sendiri.

        Batas `limit` diwarisi dari sistem v1.0 (`max_depth=2, limit=250`). Ia
        bukan hiasan: tanpa batas, satu nomor kontak yang dipakai banyak domain
        akan menarik ribuan node ke dalam konteksnya dan setiap aturan menyala
        untuk hampir semua node.
        """
        seen = {node_id}
        frontier = deque([(node_id, 0)])
        while frontier:
            current, depth = frontier.popleft()
            if depth >= max_depth:
                continue
            for neighbor in self.adjacent(current):
                if neighbor in seen:
                    continue
                seen.add(neighbor)
                if len(seen) >= limit:
                    return seen
                frontier.append((neighbor, depth + 1))
        return seen

    def nodes_of_type(self, node_type: str) -> list[RuleNode]:
        return [node for node in self.nodes.values() if node.node_type == node_type]

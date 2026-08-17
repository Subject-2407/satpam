"""SATPAM AI engine.

The engine is intentionally pure Python where possible so extraction, graph
search, scoring, early warning, and blacklist-candidate logic can be tested
without a live Neo4j instance.
"""

from app.services.ai_engine.analysis import analyze_entity, analyze_graph
from app.services.ai_engine.extractor import extract_report_entities
from app.services.ai_engine.graph import InMemoryGraph
from app.services.ai_engine.graph_builder import (
    ReportGraphInput,
    build_report_graph,
    dataset_to_graph,
)
from app.services.ai_engine.scoring import score_entity, score_path
from app.services.ai_engine.search import bfs_evidence_path, bfs_neighborhood

__all__ = [
    "InMemoryGraph",
    "ReportGraphInput",
    "analyze_entity",
    "analyze_graph",
    "bfs_evidence_path",
    "bfs_neighborhood",
    "build_report_graph",
    "dataset_to_graph",
    "extract_report_entities",
    "score_entity",
    "score_path",
]


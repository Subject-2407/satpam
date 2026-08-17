import json
from pathlib import Path

from app.services.ai_engine.alerts import detect_early_warnings
from app.services.ai_engine.analysis import analyze_entity, analyze_graph
from app.services.ai_engine.graph_builder import dataset_to_graph
from app.services.ai_engine.search import (
    a_star_search,
    bfs_evidence_path,
    bidirectional_search,
    uniform_cost_search,
)


DATASET_PATH = Path(__file__).resolve().parents[3] / "engine" / "data" / "dummy_dataset_week1.json"


def load_graph():
    dataset = json.loads(DATASET_PATH.read_text(encoding="utf-8"))
    return dataset_to_graph(dataset)


def test_bfs_and_optional_search_find_blacklist_path():
    graph = load_graph()
    start = ("Domain", "domain-bonus-alpha-test")
    targets = set(graph.keys_by_type("BlacklistEntity"))

    bfs_path = bfs_evidence_path(graph, start, max_depth=3)
    ucs_path = uniform_cost_search(graph, start, max_depth=3)
    bds_path = bidirectional_search(graph, start, targets, max_depth=3)
    astar_path = a_star_search(graph, start, max_depth=3)

    assert bfs_path is not None
    assert ucs_path is not None
    assert bds_path is not None
    assert astar_path is not None
    assert any(node.type == "BlacklistEntity" for node in bfs_path.nodes)


def test_scoring_flags_blacklist_candidate_without_final_blacklist():
    graph = load_graph()
    result = analyze_entity(graph, ("Domain", "domain-bonus-alpha-test"))

    assert result.assessment.score >= 60
    assert result.blacklist_candidate is not None
    assert result.blacklist_candidate.status == "blacklist_candidate"
    assert "R-005" in result.blacklist_candidate.rule_ids


def test_early_warning_detects_traffic_crawler_and_payment_patterns():
    graph = load_graph()
    assessments = analyze_graph(graph)
    warnings = detect_early_warnings(graph, assessments)
    alert_types = {warning.alert_type for warning in warnings}

    assert "Traffic Spike Alert" in alert_types
    assert "Suspicious Redirect Alert" in alert_types
    assert "Payment Fan-in Alert" in alert_types
    assert all(warning.simulation_only for warning in warnings)


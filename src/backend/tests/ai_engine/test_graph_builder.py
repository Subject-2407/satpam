from app.services.ai_engine.analysis import analyze_entity
from app.services.ai_engine.graph_builder import (
    ReportGraphInput,
    build_report_graph,
    graph_build_result_to_graph,
)


def test_build_report_graph_creates_expected_relationships():
    result = build_report_graph(
        ReportGraphInput(
            report_id="report-test-001",
            source="dummy_user_report",
            description=(
                "Promo bonus slot di https://bonus-alpha.test/promo, "
                "kontak WA 0812-0000-1101 dan transfer ke rekening 1234****9001."
            ),
            category_hint="judol",
        )
    )

    graph = graph_build_result_to_graph(result)
    relationship_types = {relationship["type"] for relationship in graph.relationships.values()}
    assert {"MENTIONS", "CONTAINS_KEYWORD", "REDIRECTS_TO", "CONTACTS", "USES_ACCOUNT"} <= relationship_types

    analysis = analyze_entity(graph, ("Report", "report-test-001"))
    assert analysis.assessment.score >= 60
    assert analysis.assessment.level in {"high", "critical"}
    assert "R-013" in [hit.rule_id for hit in analysis.assessment.rule_hits]


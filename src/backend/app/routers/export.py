"""
Endpoint export hasil analisis (JSON atau Markdown).

Export tidak menyertakan data sensitif mentah — nilai rekening/nomor sudah
dalam bentuk masked pada graph. Bahasa indikatif, bukan vonis.

simulation only.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import PlainTextResponse

from app.auth import Role, require_roles
from app.database import get_driver
from app.routers._common import repo_or_503
from app.services.ai_engine.analysis import analyze_entity
from app.services.ai_engine.graph import InMemoryGraph

router = APIRouter(prefix="/api", tags=["export"])


def _analysis_to_markdown(node_type: str, node_id: str, analysis: dict, generated_at: str) -> str:
    assessment = analysis.get("assessment", {})
    lines = [
        f"# Laporan Analisis Risiko (Simulasi) — {node_type}",
        "",
        f"- Entitas: `{node_id}`",
        f"- Skor risiko (indikatif): {assessment.get('score')}",
        f"- Level risiko: {assessment.get('level')}",
        f"- Confidence: {assessment.get('confidence')}",
        f"- Dibuat: {generated_at}",
        "",
        "> Catatan: Hasil ini bersifat indikatif dan memerlukan verifikasi manusia. "
        "Bukan vonis dan tidak memicu pemblokiran nyata. Semua data adalah simulasi.",
        "",
        "## Penjelasan",
        "",
        assessment.get("explanation", "(tidak ada penjelasan)"),
        "",
        "## Rule yang Aktif",
        "",
    ]
    triggered = assessment.get("triggeredRules", [])
    if triggered:
        for hit in triggered:
            lines.append(
                f"- **{hit.get('ruleId')}** ({hit.get('weight')}): "
                f"{hit.get('title')} — {hit.get('evidence')}"
            )
    else:
        lines.append("- (tidak ada rule aktif)")

    lines += ["", "## Rekomendasi", ""]
    recs = assessment.get("recommendations", [])
    if recs:
        for rec in recs:
            lines.append(
                f"- [{rec.get('priority')}] {rec.get('actionType')}: {rec.get('reason')}"
            )
    else:
        lines.append("- (tidak ada rekomendasi)")

    return "\n".join(lines)


@router.get("/export/analysis/{node_type}/{node_id}")
async def export_analysis(
    node_type: str,
    node_id: str,
    format: Literal["json", "markdown"] = Query(default="json"),
    depth: int = Query(default=3, ge=1, le=5),
    limit: int = Query(default=250, ge=1, le=1000),
    _current_user: dict = Depends(require_roles(Role.ANALYST, Role.SUPERVISOR, Role.ADMIN)),
    driver=Depends(get_driver),
):
    """Export hasil analisis sebuah entitas dalam format JSON atau Markdown."""
    repo = repo_or_503(driver)
    try:
        payload = await repo.get_neighborhood(node_type, node_id, depth=depth, limit=limit)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    if not payload["nodes"]:
        raise HTTPException(status_code=404, detail="Node tidak ditemukan")

    graph = InMemoryGraph(nodes=payload["nodes"], relationships=payload["relationships"])
    try:
        result = analyze_entity(graph, (node_type, node_id), max_depth=depth)
    except KeyError:
        raise HTTPException(status_code=404, detail="Node tidak ditemukan")

    analysis = result.as_dict()
    generated_at = datetime.now(timezone.utc).isoformat()

    if format == "markdown":
        text = _analysis_to_markdown(node_type, node_id, analysis, generated_at)
        return PlainTextResponse(content=text, media_type="text/markdown")

    return {
        "generatedAt": generated_at,
        "simulationOnly": True,
        "disclaimer": (
            "Hasil indikatif, memerlukan verifikasi manusia. Bukan vonis, "
            "tidak memicu pemblokiran nyata. Semua data simulasi."
        ),
        "entity": {"type": node_type, "id": node_id},
        "analysis": analysis,
    }

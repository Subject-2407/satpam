import json
import uuid
from datetime import datetime, timezone
from typing import List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.auth import get_current_user
from app.database import get_driver
from app.repositories.neo4j_repo import Neo4jRepository

router = APIRouter(prefix="/api", tags=["reports"])


class BankAccountInput(BaseModel):
    bankName: str
    accountAlias: str
    maskedAccountNumber: str


class AppInput(BaseModel):
    appName: str
    packageName: str


class ReportCreateRequest(BaseModel):
    source: str = "user_report"
    description: str
    categoryHint: Literal[
        "judol", "pinjol_illegal", "cross_ecosystem", "payment_flow", "traffic_crawler", "benign"
    ]
    urls: Optional[List[str]] = None
    phoneNumbers: Optional[List[str]] = None
    bankAccounts: Optional[List[BankAccountInput]] = None
    apps: Optional[List[AppInput]] = None


class ReportCreateResponse(BaseModel):
    reportId: str
    status: str
    message: str


@router.post("/reports", response_model=ReportCreateResponse, status_code=201)
async def create_report(
    body: ReportCreateRequest,
    current_user: dict = Depends(get_current_user),
    driver=Depends(get_driver),
):
    """
    Simpan laporan dummy ke Neo4j sebagai node Report.

    Dapat diakses oleh semua role yang sudah login.
    Data yang dikirim adalah data simulasi, bukan laporan nyata.
    """
    if driver is None:
        raise HTTPException(status_code=503, detail="Database tidak tersedia")

    report_id = f"report-{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc).isoformat()

    props: dict = {
        "id": report_id,
        "type": "Report",
        "label": f"Laporan {body.categoryHint.replace('_', ' ').title()}",
        "source": body.source,
        "description": body.description,
        "categoryHint": body.categoryHint,
        "status": "new",
        "verificationStatus": "unreviewed",
        "confidence": "low",
        "riskScore": 0,
        "riskLevel": "low",
        "submittedBy": current_user["id"],
        "submittedByRole": current_user["role"],
        "rawUrls": body.urls or [],
        "rawPhoneNumbers": body.phoneNumbers or [],
        # Neo4j tidak mendukung list of dicts — serialisasi ke JSON string
        "rawApps": json.dumps([a.model_dump() for a in (body.apps or [])]),
        "rawBankAccounts": json.dumps([a.model_dump() for a in (body.bankAccounts or [])]),
        "createdAt": now,
        "updatedAt": now,
    }

    repo = Neo4jRepository(driver)
    try:
        await repo.merge_node("Report", report_id, props)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Gagal menyimpan laporan: {exc}")

    return ReportCreateResponse(
        reportId=report_id,
        status="new",
        message="Laporan diterima sebagai data simulasi dan sedang diproses",
    )

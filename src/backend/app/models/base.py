from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ConfidenceLevel(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class RiskLevel(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class VerificationStatus(str, Enum):
    unreviewed = "unreviewed"
    needs_review = "needs_review"
    verified_risk = "verified_risk"
    false_positive = "false_positive"
    escalated = "escalated"
    closed = "closed"


class BaseNode(BaseModel):
    """Properti standar untuk semua node SATPAM. Data adalah simulasi/dummy."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    id: str
    type: str
    label: str
    source: str
    createdAt: datetime
    updatedAt: Optional[datetime] = None
    firstSeenAt: Optional[datetime] = None
    lastSeenAt: Optional[datetime] = None
    confidence: Optional[ConfidenceLevel] = None
    riskScore: Optional[int] = Field(default=None, ge=0, le=100)
    riskLevel: Optional[RiskLevel] = None
    verificationStatus: VerificationStatus = VerificationStatus.unreviewed

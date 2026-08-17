from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.base import ConfidenceLevel


class RelationshipEndpoint(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: str
    id: str


class RelationshipModel(BaseModel):
    """Edge dalam graph SATPAM. Semua data adalah simulasi."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    id: str
    type: str
    from_: RelationshipEndpoint = Field(alias="from")
    to: RelationshipEndpoint
    source: str
    confidence: ConfidenceLevel
    weight: float = Field(ge=0)
    evidenceId: Optional[str] = None
    firstSeenAt: Optional[datetime] = None
    lastSeenAt: Optional[datetime] = None
    createdAt: datetime

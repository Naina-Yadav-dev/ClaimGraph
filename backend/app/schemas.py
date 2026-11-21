
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class InvestigationCreate(BaseModel):

    input_type: Literal["text", "url"] = "text"

    content: str = Field(
        min_length=1,
        max_length=10000
    )

    @field_validator("content")
    @classmethod
    def validate_content(cls, value: str) -> str:

        value = value.strip()

        if not value:
            raise ValueError("Content cannot be empty.")

        return value



# ==========================================
# EVIDENCE SCHEMAS
# ==========================================

class EvidenceCreate(BaseModel):

    claim_id: int

    source_title: str | None = None

    source_url: str

    source_domain: str | None = None

    snippet: str = Field(
        min_length=1,
        max_length=10000
    )

    evidence_type: Literal[
        "supporting",
        "contradicting",
        "unclassified"
    ] = "unclassified"


class EvidenceResponse(BaseModel):

    id: int

    claim_id: int

    source_title: str | None = None

    source_url: str

    source_domain: str | None = None

    snippet: str

    evidence_type: str

    class Config:
        from_attributes = True

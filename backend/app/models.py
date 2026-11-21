
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey,
    Float,
)

from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .database import Base


# ==========================================
# 1. INVESTIGATION TABLE
# ==========================================

class Investigation(Base):

    __tablename__ = "investigations"

    id = Column(String, primary_key=True, index=True)

    input_type = Column(String(20), nullable=False)

    content = Column(Text, nullable=False)

    status = Column(
        String(30),
        nullable=False,
        default="received"
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    claims = relationship(
        "Claim",
        back_populates="investigation",
        cascade="all, delete-orphan"
    )


# ==========================================
# 2. CLAIM TABLE
# ==========================================

class Claim(Base):

    __tablename__ = "claims"

    id = Column(Integer, primary_key=True, index=True)

    investigation_id = Column(
        String,
        ForeignKey("investigations.id"),
        nullable=False,
        index=True
    )

    claim_number = Column(String(20), nullable=False)

    claim_text = Column(Text, nullable=False)

    extraction_method = Column(
        String(30),
        nullable=False
    )

    status = Column(
        String(30),
        nullable=False,
        default="candidate"
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    investigation = relationship(
        "Investigation",
        back_populates="claims"
    )

    entities = relationship(
        "Entity",
        back_populates="claim",
        cascade="all, delete-orphan"
    )

    evidences = relationship(
        "Evidence",
        back_populates="claim",
        cascade="all, delete-orphan"
    )


# ==========================================
# 3. ENTITY TABLE
# ==========================================

class Entity(Base):

    __tablename__ = "entities"

    id = Column(Integer, primary_key=True, index=True)

    claim_id = Column(
        Integer,
        ForeignKey("claims.id"),
        nullable=False,
        index=True
    )

    entity_text = Column(
        String(500),
        nullable=False
    )

    label = Column(
        String(30),
        nullable=False
    )

    start_offset = Column(
        Integer,
        nullable=False
    )

    end_offset = Column(
        Integer,
        nullable=False
    )

    extraction_method = Column(
        String(30),
        nullable=False
    )

    claim = relationship(
        "Claim",
        back_populates="entities"
    )


# ==========================================
# 4. EVIDENCE TABLE
# ==========================================

class Evidence(Base):

    __tablename__ = "evidences"

    id = Column(Integer, primary_key=True, index=True)

    claim_id = Column(
        Integer,
        ForeignKey("claims.id"),
        nullable=False,
        index=True
    )

    source_title = Column(
        String(500),
        nullable=True
    )

    source_url = Column(
        Text,
        nullable=False
    )

    source_domain = Column(
        String(255),
        nullable=True
    )

    snippet = Column(
        Text,
        nullable=False
    )

    evidence_type = Column(
        String(30),
        nullable=False,
        default="unclassified"
    )

    retrieved_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    claim = relationship(
        "Claim",
        back_populates="evidences"
    )

    analysis_records = relationship(
        "EvidenceAnalysis",
        back_populates="evidence",
        cascade="all, delete-orphan"
    )


# ==========================================
# 5. EVIDENCE ANALYSIS HISTORY TABLE
# ==========================================

class EvidenceAnalysis(Base):

    __tablename__ = "evidence_analyses"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    evidence_id = Column(
        Integer,
        ForeignKey("evidences.id"),
        nullable=False,
        index=True
    )

    similarity_score = Column(
        Float,
        nullable=False,
        default=0.0
    )

    assessment = Column(
        String(30),
        nullable=False
    )

    confidence = Column(
        String(20),
        nullable=False,
        default="low"
    )

    reason = Column(
        Text,
        nullable=True
    )

    analyzed_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    evidence = relationship(
        "Evidence",
        back_populates="analysis_records"
    )

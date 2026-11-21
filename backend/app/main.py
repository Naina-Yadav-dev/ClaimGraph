from uuid import uuid4
import logging
from pathlib import Path

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from . import models, schemas
from .database import engine, get_db
from .nlp.pipeline import analyze_text
from .services.evidence_collector import search_evidence
from .services.evidence_analyzer import analyze_evidence


# ==================================================
# 1. LOGGING AND DATABASE
# ==================================================

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Creates missing tables, including evidence_analyses.
# It does not delete or overwrite existing SQLite tables/data.
models.Base.metadata.create_all(bind=engine)


# ==================================================
# 2. FASTAPI APPLICATION
# ==================================================

app = FastAPI(
    title="ClaimGraph API",
    description=(
        "AI-assisted, evidence-based misinformation "
        "investigation platform"
    ),
    version="0.5.0",
)


# ==================================================
# 3. CORS
# ==================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================================================
# 4. HOME AND HEALTH
# ==================================================

@app.get("/")
def home():
    return {
        "message": "Welcome to ClaimGraph!",
        "status": "Backend is running",
        "version": "0.5.0",
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "claimgraph-backend",
    }


# ==================================================
# 5. CREATE INVESTIGATION
# ==================================================

@app.post("/api/v1/investigations", status_code=201)
def create_investigation(
    request: schemas.InvestigationCreate,
    db: Session = Depends(get_db),
):
    investigation_id = f"CG-{uuid4().hex[:8].upper()}"

    record = models.Investigation(
        id=investigation_id,
        input_type=request.input_type,
        content=request.content,
        status="received",
    )

    try:
        db.add(record)
        db.commit()
        db.refresh(record)
    except Exception:
        db.rollback()
        logger.exception("Investigation creation failed")
        raise HTTPException(
            status_code=500,
            detail="Could not save investigation.",
        )

    return {
        "investigation_id": record.id,
        "status": record.status,
        "input_type": record.input_type,
        "message": "Investigation saved successfully",
    }


# ==================================================
# 6. GET INVESTIGATION
# ==================================================

@app.get("/api/v1/investigations/{investigation_id}")
def get_investigation(
    investigation_id: str,
    db: Session = Depends(get_db),
):
    statement = select(models.Investigation).where(
        models.Investigation.id == investigation_id
    )
    record = db.execute(statement).scalar_one_or_none()

    if record is None:
        raise HTTPException(
            status_code=404,
            detail="Investigation not found.",
        )

    return {
        "investigation_id": record.id,
        "input_type": record.input_type,
        "content": record.content,
        "status": record.status,
        "created_at": record.created_at,
    }


# ==================================================
# 7. NLP INVESTIGATION ANALYSIS
# ==================================================

@app.post("/api/v1/investigations/{investigation_id}/analyze")
def analyze_investigation(
    investigation_id: str,
    db: Session = Depends(get_db),
):
    statement = select(models.Investigation).where(
        models.Investigation.id == investigation_id
    )
    record = db.execute(statement).scalar_one_or_none()

    if record is None:
        raise HTTPException(
            status_code=404,
            detail="Investigation not found.",
        )

    if record.input_type != "text":
        raise HTTPException(
            status_code=400,
            detail="NLP analysis currently supports text input only.",
        )

    # Safety: clearing old claims would cascade-delete their evidence
    # and evidence-analysis history. Refuse to overwrite if evidence exists.
    existing_claim_ids = [
        claim.id for claim in record.claims
    ]

    if existing_claim_ids:
        evidence_exists = (
            db.query(models.Evidence.id)
            .filter(models.Evidence.claim_id.in_(existing_claim_ids))
            .first()
        )

        if evidence_exists:
            raise HTTPException(
                status_code=409,
                detail=(
                    "This investigation already has evidence attached "
                    "to its claims. Re-analysis is blocked to protect "
                    "existing evidence and analysis history."
                ),
            )

    try:
        analysis = analyze_text(record.content)
        claims = analysis.get("claims", [])

        # Safe to replace previous claims only when none has evidence.
        record.claims.clear()
        db.flush()

        total_entities = 0

        for claim_data in claims:
            claim_record = models.Claim(
                investigation_id=record.id,
                claim_number=claim_data["claim_id"],
                claim_text=claim_data["claim_text"],
                extraction_method=claim_data.get(
                    "extraction_method",
                    "rule_based",
                ),
                status=claim_data.get("status", "candidate"),
            )

            for entity_data in claim_data.get("entities", []):
                entity_record = models.Entity(
                    entity_text=entity_data["text"],
                    label=entity_data["label"],
                    start_offset=entity_data["start"],
                    end_offset=entity_data["end"],
                    extraction_method=entity_data.get(
                        "method",
                        "rule_based",
                    ),
                )
                claim_record.entities.append(entity_record)
                total_entities += 1

            record.claims.append(claim_record)

        record.status = "analyzed"
        db.commit()

    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        logger.exception(
            "NLP analysis or database saving failed"
        )
        raise HTTPException(
            status_code=500,
            detail="Could not process or save NLP analysis.",
        )

    return {
        "investigation_id": record.id,
        "analysis_status": "completed",
        "saved_claims": len(claims),
        "saved_entities": total_entities,
        "message": "NLP results saved successfully",
        "analysis": analysis,
    }


# ==================================================
# 8. GET SAVED CLAIMS AND ENTITIES
# ==================================================

@app.get("/api/v1/investigations/{investigation_id}/claims")
def get_saved_claims(
    investigation_id: str,
    db: Session = Depends(get_db),
):
    statement = select(models.Investigation).where(
        models.Investigation.id == investigation_id
    )

    record = db.execute(statement).scalar_one_or_none()

    if record is None:
        raise HTTPException(
            status_code=404,
            detail="Investigation not found.",
        )

    claims_data = []

    for claim in record.claims:
        entities_data = []

        for entity in claim.entities:
            entities_data.append({
                "text": entity.entity_text,
                "label": entity.label,
                "start": entity.start_offset,
                "end": entity.end_offset,
                "method": entity.extraction_method,
            })

        claims_data.append({
            "id": claim.id,
            "database_claim_id": claim.id,
            "claim_id": claim.claim_number,
            "claim_text": claim.claim_text,
            "extraction_method": claim.extraction_method,
            "status": claim.status,
            "entities": entities_data,
        })

    return {
        "investigation_id": record.id,
        "total_claims": len(claims_data),
        "claims": claims_data,
    }


# ==================================================
# 9. SERVE FRONTEND
# ==================================================

FRONTEND_FILE = (
    Path(__file__).resolve().parent
    / "static"
    / "index.html"
)


@app.get("/app", include_in_schema=False)
def frontend():
    if not FRONTEND_FILE.exists():
        raise HTTPException(
            status_code=404,
            detail="Frontend file not found.",
        )

    return FileResponse(FRONTEND_FILE)


# ==================================================
# 10. MANUAL EVIDENCE MANAGEMENT
# ==================================================

@app.post(
    "/api/v1/evidence",
    response_model=schemas.EvidenceResponse,
    status_code=201,
)
def create_evidence(
    evidence: schemas.EvidenceCreate,
    db: Session = Depends(get_db),
):
    claim = db.get(models.Claim, evidence.claim_id)

    if claim is None:
        raise HTTPException(
            status_code=404,
            detail="Claim not found",
        )

    try:
        new_evidence = models.Evidence(
            claim_id=evidence.claim_id,
            source_title=evidence.source_title,
            source_url=evidence.source_url,
            source_domain=evidence.source_domain,
            snippet=evidence.snippet,
            evidence_type=evidence.evidence_type,
        )

        db.add(new_evidence)
        db.commit()
        db.refresh(new_evidence)
        return new_evidence

    except Exception:
        db.rollback()
        logger.exception("Evidence saving failed")
        raise HTTPException(
            status_code=500,
            detail="Failed to save evidence",
        )


@app.get(
    "/api/v1/claims/{claim_id}/evidence",
    response_model=list[schemas.EvidenceResponse],
)
def get_claim_evidence(
    claim_id: int,
    db: Session = Depends(get_db),
):
    claim = db.get(models.Claim, claim_id)

    if claim is None:
        raise HTTPException(
            status_code=404,
            detail="Claim not found",
        )

    return (
        db.query(models.Evidence)
        .filter(models.Evidence.claim_id == claim_id)
        .order_by(models.Evidence.id.asc())
        .all()
    )


# ==================================================
# 11. AUTOMATIC EVIDENCE COLLECTION
# ==================================================

@app.post(
    "/api/v1/claims/{claim_id}/collect-evidence",
    response_model=list[schemas.EvidenceResponse],
)
def collect_claim_evidence(
    claim_id: int,
    query: str,
    max_results: int = 5,
    db: Session = Depends(get_db),
):
    claim = db.get(models.Claim, claim_id)

    if claim is None:
        raise HTTPException(
            status_code=404,
            detail="Claim not found",
        )

    if not query.strip():
        raise HTTPException(
            status_code=400,
            detail="Search query cannot be empty.",
        )

    if max_results < 1 or max_results > 10:
        raise HTTPException(
            status_code=400,
            detail="max_results must be between 1 and 10",
        )

    try:
        search_results = search_evidence(
            query=query,
            max_results=max_results,
        )

        saved_evidence = []

        for result in search_results:
            evidence = models.Evidence(
                claim_id=claim_id,
                source_title=result.get("source_title"),
                source_url=result["source_url"],
                source_domain=result.get("source_domain"),
                snippet=result.get("snippet", ""),
                evidence_type="unclassified",
            )
            db.add(evidence)
            saved_evidence.append(evidence)

        db.commit()

        for evidence in saved_evidence:
            db.refresh(evidence)

        return saved_evidence

    except Exception:
        db.rollback()
        logger.exception("Automatic evidence collection failed")
        raise HTTPException(
            status_code=500,
            detail="Evidence collection failed",
        )


# ==================================================
# 12. AI-ASSISTED EVIDENCE ANALYSIS + HISTORY
# ==================================================

@app.post("/api/v1/claims/{claim_id}/analyze-evidence")
def analyze_claim_evidence(
    claim_id: int,
    db: Session = Depends(get_db),
):
    """
    Run preliminary TF-IDF analysis for each evidence record.
    Save the current classification and append a history row.
    This is not an automated truth verdict.
    """

    claim = db.get(models.Claim, claim_id)

    if claim is None:
        raise HTTPException(
            status_code=404,
            detail="Claim not found",
        )

    evidence_records = (
        db.query(models.Evidence)
        .filter(models.Evidence.claim_id == claim_id)
        .order_by(models.Evidence.id.asc())
        .all()
    )

    if not evidence_records:
        raise HTTPException(
            status_code=404,
            detail=(
                "No evidence found for this claim. "
                "Collect or add evidence first."
            ),
        )

    results = []
    summary = {
        "supporting": 0,
        "contradicting": 0,
        "insufficient": 0,
    }

    try:
        for evidence in evidence_records:
            analysis = analyze_evidence(
                claim.claim_text,
                evidence.snippet or "",
            )

            assessment = analysis.get(
                "assessment",
                "insufficient",
            )

            if assessment not in summary:
                assessment = "insufficient"
                analysis["assessment"] = assessment

            similarity_score = float(
                analysis.get("similarity_score", 0.0)
            )
            confidence = analysis.get("confidence", "low")
            reason = analysis.get("reason", "")

            # Update the latest classification on the evidence row.
            evidence.evidence_type = assessment

            # Append a new history row; previous rows remain intact.
            analysis_record = models.EvidenceAnalysis(
                evidence_id=evidence.id,
                similarity_score=similarity_score,
                assessment=assessment,
                confidence=confidence,
                reason=reason,
            )
            db.add(analysis_record)

            summary[assessment] += 1

            results.append({
                "evidence_id": evidence.id,
                "source_title": evidence.source_title,
                "source_url": evidence.source_url,
                "source_domain": evidence.source_domain,
                "evidence_type": assessment,
                "analysis": analysis,
            })

        db.commit()

    except Exception:
        db.rollback()
        logger.exception(
            "AI-assisted evidence analysis failed"
        )
        raise HTTPException(
            status_code=500,
            detail="Could not analyze evidence.",
        )

    return {
        "claim_id": claim.id,
        "claim_text": claim.claim_text,
        "total_evidence": len(evidence_records),
        "summary": summary,
        "notice": (
            "Preliminary automated text assessment only. "
            "Similarity or keyword signals do not establish truth. "
            "Verify original sources and context manually."
        ),
        "results": results,
    }


# ==================================================
# 13. GET EVIDENCE ANALYSIS HISTORY
# ==================================================

@app.get("/api/v1/evidence/{evidence_id}/analysis-history")
def get_evidence_analysis_history(
    evidence_id: int,
    db: Session = Depends(get_db),
):
    evidence = db.get(models.Evidence, evidence_id)

    if evidence is None:
        raise HTTPException(
            status_code=404,
            detail="Evidence not found",
        )

    history = (
        db.query(models.EvidenceAnalysis)
        .filter(
            models.EvidenceAnalysis.evidence_id == evidence_id
        )
        .order_by(models.EvidenceAnalysis.analyzed_at.desc(),
                  models.EvidenceAnalysis.id.desc())
        .all()
    )

    return {
        "evidence_id": evidence.id,
        "source_title": evidence.source_title,
        "total_analyses": len(history),
        "history": [
            {
                "analysis_id": item.id,
                "similarity_score": item.similarity_score,
                "assessment": item.assessment,
                "confidence": item.confidence,
                "reason": item.reason,
                "analyzed_at": item.analyzed_at,
            }
            for item in history
        ],
    }

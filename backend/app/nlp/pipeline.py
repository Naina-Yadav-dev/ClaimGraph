
from app.nlp.claim_extractor import extract_candidate_claims
from app.nlp.entity_extractor import extract_entities


def analyze_text(text: str) -> dict:
    """
    Extract candidate claims and their entities.
    """

    # Step 1: Extract candidate claims
    claims = extract_candidate_claims(text)

    # Step 2: Extract entities from each claim
    for claim in claims:

        entities = extract_entities(
            claim["claim_text"]
        )

        claim["entities"] = entities

    # Step 3: Return combined result
    return {
        "total_claims": len(claims),
        "claims": claims
    }

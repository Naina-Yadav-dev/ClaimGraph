
import re


def split_into_sentences(text: str) -> list[str]:
    """
    Split a paragraph into individual sentences.
    """

    if not text or not text.strip():
        return []

    # Remove extra spaces and newlines
    text = re.sub(r"\s+", " ", text).strip()

    # Split at sentence-ending punctuation
    sentences = re.split(
        r"(?<=[.!?])\s+",
        text
    )

    return [
        sentence.strip()
        for sentence in sentences
        if sentence.strip()
    ]


def extract_candidate_claims(text: str) -> list[dict]:
    """
    Convert sentences into candidate claims.
    """

    sentences = split_into_sentences(text)

    claims = []

    for index, sentence in enumerate(sentences, start=1):

        claim = {
            "claim_id": f"C{index:03d}",
            "claim_text": sentence,
            "extraction_method": "rule_based",
            "status": "candidate"
        }

        claims.append(claim)

    return claims

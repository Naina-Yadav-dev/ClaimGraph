
import re

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


STOP_WORDS = {
    "the", "is", "are", "was", "were", "a", "an",
    "in", "on", "at", "to", "of", "for", "and",
    "or", "will", "would", "has", "have", "had",
    "be", "been", "being", "that", "this", "it",
    "its", "by", "from", "as", "with"
}

CONTRADICTION_SIGNALS = [
    "false", "not true", "incorrect", "debunked",
    "did not", "does not", "never happened",
    "denied", "refuted", "disproved"
]

WORD_GROUPS = {
    "train": {"train", "training", "trained"},
    "announce": {"announce", "announced", "announcement"},
    "student": {"student", "students"},
    "youth": {"youth", "young", "people"},
    "government": {"government", "govt", "ministry"},
    "education": {"education", "educational"},
    "artificial": {"ai", "artificial", "intelligence"},
}


def clean_text(text: str) -> str:
    if not text:
        return ""

    text = text.lower()
    text = re.sub(r"https?://\S+", " ", text)
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def get_keywords(text: str) -> set:
    words = clean_text(text).split()

    return {
        word for word in words
        if word not in STOP_WORDS and len(word) > 1
    }


def expand_keywords(words: set) -> set:
    expanded = set(words)

    for group in WORD_GROUPS.values():
        if words.intersection(group):
            expanded.update(group)

    return expanded


def calculate_tfidf(claim: str, evidence: str) -> float:
    try:
        vectorizer = TfidfVectorizer(
            stop_words="english",
            ngram_range=(1, 2),
            sublinear_tf=True
        )

        vectors = vectorizer.fit_transform([claim, evidence])

        return float(
            cosine_similarity(
                vectors[0:1],
                vectors[1:2]
            )[0][0]
        )

    except ValueError:
        return 0.0


def analyze_evidence(claim_text: str, evidence_text: str) -> dict:
    """
    Preliminary evidence relevance analysis.
    This system does not independently verify factual truth.
    """

    claim = clean_text(claim_text)
    evidence = clean_text(evidence_text)

    if not claim or not evidence:
        return {
            "similarity_score": 0.0,
            "assessment": "insufficient",
            "confidence": "low",
            "reason": "Claim or evidence text is empty."
        }

    claim_words = get_keywords(claim)
    evidence_words = get_keywords(evidence)

    expanded_claim = expand_keywords(claim_words)
    expanded_evidence = expand_keywords(evidence_words)

    common_words = expanded_claim.intersection(
        expanded_evidence
    )

    keyword_score = (
        len(common_words) / len(expanded_claim)
        if expanded_claim else 0.0
    )

    tfidf_score = calculate_tfidf(claim, evidence)

    combined_score = (
        0.60 * tfidf_score +
        0.40 * keyword_score
    )

    # Preserve important numerical differences.
    claim_numbers = set(re.findall(r"\b\d+\b", claim))
    evidence_numbers = set(re.findall(r"\b\d+\b", evidence))

    if claim_numbers and evidence_numbers:
        if claim_numbers.isdisjoint(evidence_numbers):
            combined_score *= 0.5

    # Population mismatch: young people are not automatically
    # equivalent to students.
    claim_has_students = bool(
        {"student", "students"}.intersection(claim_words)
    )

    evidence_has_students = bool(
        {"student", "students"}.intersection(evidence_words)
    )

    population_mismatch = (
        claim_has_students
        and not evidence_has_students
        and bool({"youth", "young", "people"}.intersection(evidence_words))
    )

    if population_mismatch:
        combined_score *= 0.75

    score = round(min(combined_score, 1.0), 3)

    contradiction_found = any(
        signal in evidence
        for signal in CONTRADICTION_SIGNALS
    )

    if contradiction_found and score >= 0.25:
        assessment = "contradicting"
        reason = (
            "Potential contradiction language was detected. "
            "The source requires manual verification."
        )

    elif score >= 0.35 and not population_mismatch:
        assessment = "supporting"
        reason = (
            "Relevant textual information was detected. "
            "This does not independently prove the claim."
        )

    else:
        assessment = "insufficient"

        if population_mismatch:
            reason = (
                "The source discusses young people, but the claim "
                "specifically mentions students. These populations "
                "cannot automatically be treated as equivalent."
            )
        else:
            reason = (
                "Evidence relevance is insufficient for a reliable "
                "assessment. Manual source review is required."
            )

    return {
        "similarity_score": score,
        "assessment": assessment,
        "confidence": "low",
        "reason": reason
    }

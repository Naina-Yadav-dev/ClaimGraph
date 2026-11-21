
import re


# Known organization names
ORGANIZATIONS = [
    "Ministry of Education",
    "Government of India",
    "United Nations",
    "World Health Organization",
    "WHO",
]


# Known location names
LOCATIONS = [
    "India",
    "New Delhi",
    "United States",
    "United Kingdom",
    "London",
]


MONTHS = (
    "January|February|March|April|May|June|"
    "July|August|September|October|November|December"
)


def extract_entities(text: str) -> list[dict]:
    """
    Extract basic entities using Python regex and dictionaries.
    """

    entities = []

    def add_matches(pattern, label, flags=re.IGNORECASE):
        for match in re.finditer(pattern, text, flags):
            entities.append({
                "text": match.group().strip(),
                "label": label,
                "start": match.start(),
                "end": match.end(),
                "method": "rule_based"
            })

    # 1. Organizations
    for organization in ORGANIZATIONS:
        pattern = (
            r"(?<!\w)" + re.escape(organization) + r"(?!\w)"
        )
        add_matches(pattern, "ORG")

    # 2. Locations
    for location in LOCATIONS:
        pattern = (
            r"(?<!\w)" + re.escape(location) + r"(?!\w)"
        )
        add_matches(pattern, "GPE")

    # 3. Dates: January 2027, 2026, etc.
    date_pattern = (
        rf"\b(?:{MONTHS})\s+\d{{1,2}}"
        rf"(?:,\s+\d{{4}})?\b"
        rf"|\b(?:{MONTHS})\s+\d{{4}}\b"
        rf"|\b(?:19|20)\d{{2}}\b"
    )

    add_matches(date_pattern, "DATE")

    # 4. Quantities: 10 million students, 500 people, etc.
    quantity_pattern = (
        r"\b\d+(?:,\d{3})*(?:\.\d+)?\s*"
        r"(?:million|billion|thousand|crore|lakh|lakhs)"
        r"(?:\s+[A-Za-z]+){0,2}\b"
        r"|\b\d+(?:,\d{3})*(?:\.\d+)?\s*"
        r"(?:students|people|employees|families)\b"
    )

    add_matches(quantity_pattern, "QUANTITY")

    # Sort entities by their position in the original text
    entities.sort(key=lambda item: (item["start"], item["end"]))

    return entities

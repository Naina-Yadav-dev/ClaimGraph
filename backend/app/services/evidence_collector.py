
import logging
from urllib.parse import urlparse, urlunparse

from ddgs import DDGS

logger = logging.getLogger(__name__)


def build_search_queries(query: str) -> list:
    """Build fallback queries from the original claim."""

    if not query or not query.strip():
        return []

    clean_query = query.strip().rstrip(".")

    queries = [
        clean_query,
        f"{clean_query} official source",
        f"{clean_query} India government",
    ]

    unique_queries = []
    seen = set()

    for item in queries:
        key = item.lower()

        if key not in seen:
            unique_queries.append(item)
            seen.add(key)

    return unique_queries


def normalize_url(url: str) -> str:
    """Normalize URL to prevent duplicate evidence."""

    try:
        parsed = urlparse(url.strip())

        if parsed.scheme not in ("http", "https"):
            return ""

        if not parsed.netloc:
            return ""

        domain = parsed.netloc.lower()

        if domain.startswith("www."):
            domain = domain[4:]

        return urlunparse((
            parsed.scheme.lower(),
            domain,
            parsed.path.rstrip("/"),
            "",
            "",
            ""
        ))

    except Exception:
        return ""


def search_evidence(query: str, max_results: int = 5):
    """
    Collect evidence using working DDGS providers.

    Bing is tried first, followed by Google.
    Search failures do not stop other attempts.
    """

    if not query or not query.strip():
        return []

    max_results = max(1, min(int(max_results), 20))

    search_queries = build_search_queries(query)

    providers = ["bing", "google"]

    evidence_list = []
    seen_urls = set()

    for provider in providers:

        if len(evidence_list) >= max_results:
            break

        for search_query in search_queries:

            if len(evidence_list) >= max_results:
                break

            try:
                results = DDGS(timeout=15).text(
                    search_query,
                    max_results=max_results,
                    backend=provider,
                    region="in-en",
                )

                for result in results:

                    if len(evidence_list) >= max_results:
                        break

                    url = (result.get("href") or "").strip()

                    if not url:
                        continue

                    normalized_url = normalize_url(url)

                    if not normalized_url:
                        continue

                    if normalized_url in seen_urls:
                        continue

                    parsed = urlparse(url)

                    evidence = {
                        "source_title": (
                            result.get("title") or "Untitled"
                        ),
                        "source_url": url,
                        "source_domain": parsed.netloc.lower(),
                        "snippet": result.get("body") or "",
                        "evidence_type": "unclassified",
                    }

                    evidence_list.append(evidence)
                    seen_urls.add(normalized_url)

            except Exception as error:

                logger.warning(
                    "Provider %s failed for query '%s': %s",
                    provider,
                    search_query,
                    error
                )

                continue

    logger.info(
        "Evidence collection completed: %s results",
        len(evidence_list)
    )

    return evidence_list

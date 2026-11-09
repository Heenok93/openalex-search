import os
from typing import Any

import requests
from dotenv import load_dotenv

from urllib.parse import quote

from src.models import Article, SearchResult


load_dotenv()


BASE_URL = "https://api.openalex.org"
TIMEOUT = 30


def reconstruct_abstract(
    inverted_index: dict[str, list[int]] | None,
) -> str | None:
    """Reconstruct plain text from an OpenAlex abstract inverted index."""

    if not inverted_index:
        return None

    words: list[tuple[int, str]] = []

    for word, positions in inverted_index.items():
        for position in positions:
            words.append((position, word))

    words.sort(key=lambda item: item[0])

    return " ".join(word for _, word in words)


def extract_concepts(work: dict[str, Any]) -> str | None:
    """Extract OpenAlex concepts/topics as a compact text string."""

    concepts = work.get("concepts") or []

    names = [
        concept.get("display_name")
        for concept in concepts
        if concept.get("display_name")
    ]

    if not names:
        return None

    return ", ".join(names)


def extract_pdf_url(work: dict[str, Any]) -> str | None:
    """Return the best available PDF URL, when OpenAlex provides one."""

    best_oa_location = work.get("best_oa_location") or {}

    pdf_url = best_oa_location.get("pdf_url")

    if pdf_url:
        return pdf_url

    primary_location = work.get("primary_location") or {}

    return primary_location.get("pdf_url")


def normalize_work(work: dict[str, Any]) -> Article:
    """Convert one OpenAlex work into our internal Article model."""

    authors = [
        authorship["author"]["display_name"]
        for authorship in work.get("authorships", [])
        if authorship.get("author")
        and authorship["author"].get("display_name")
    ]

    primary_location = work.get("primary_location") or {}
    source = primary_location.get("source") or {}

    return Article(
        openalex_id=work.get("id", ""),
        title=work.get("display_name") or "Untitled",
        year=work.get("publication_year"),
        publication_date=work.get("publication_date"),
        authors=authors,
        source=source.get("display_name"),
        doi=work.get("doi"),
        abstract=reconstruct_abstract(
            work.get("abstract_inverted_index")
        ),
        cited_by=work.get("cited_by_count", 0),
        concepts=extract_concepts(work),
        pdf_url=extract_pdf_url(work),
        relevance_score=work.get("relevance_score"),
    )

def _request(
    endpoint: str,
    params: dict[str, Any],
) -> dict[str, Any]:
    """Send a GET request to OpenAlex and return decoded JSON."""

    email = os.getenv("OPENALEX_EMAIL")

    if email:
        params["mailto"] = email

    url = BASE_URL if not endpoint else f"{BASE_URL}/{endpoint}"

    response = requests.get(
        url,
        params=params,
        timeout=TIMEOUT,
    )

    if not response.ok:
        raise RuntimeError(
            f"OpenAlex API error {response.status_code}\n"
            f"URL: {response.url}\n"
            f"Response: {response.text}"
        )

    return response.json()

def _normalize_search_response(data: dict[str, Any]) -> SearchResult:
    """Convert an OpenAlex search response into SearchResult."""

    articles = [
        normalize_work(work)
        for work in data.get("results", [])
    ]

    total_count = data.get("meta", {}).get("count", len(articles))

    return SearchResult(
        articles=articles,
        total_count=total_count,
    )


def search_works(
    query: str,
    year_from: int | None = None,
    year_to: int | None = None,
    per_page: int = 25,
) -> SearchResult:
    """
    Search OpenAlex Works using a standard text search plus
    deterministic filters.

    This is the stable backend for explicit/advanced filters.
    """

    filters: list[str] = []

    if year_from is not None:
        filters.append(
            f"from_publication_date:{year_from}-01-01"
        )

    if year_to is not None:
        filters.append(
            f"to_publication_date:{year_to}-12-31"
        )

    params: dict[str, Any] = {
        "search": query,
        "per-page": per_page,
    }

    if filters:
        params["filter"] = ",".join(filters)

    data = _request(
        endpoint="works",
        params=params,
    )

    return _normalize_search_response(data)


def search_semantic(
    query: str,
    year_from: int | None = None,
    year_to: int | None = None,
    per_page: int = 25,
    languages: list[str] | None = None,
    open_access_only: bool = False,
    has_abstract: bool = True,
    include_retracted: bool = False,
) -> SearchResult:
    """Search OpenAlex Works using semantic similarity."""

    # Semantic Search supports a maximum of 50 results.
    per_page = min(per_page, 50)

    filters: list[str] = []

    # Publication years
    if year_from is not None:
        filters.append(
            f"publication_year:>{year_from - 1}"
        )

    if year_to is not None:
        filters.append(
            f"publication_year:<{year_to + 1}"
        )

    # Languages, e.g. ["en", "fr"]
    if languages:
        language_filter = "|".join(languages)
        filters.append(
            f"language:{language_filter}"
        )

    # Open access
    if open_access_only:
        filters.append("is_oa:true")

    # Abstract availability
    if has_abstract:
        filters.append("has_abstract:true")

    # Retracted papers are excluded by default
    if not include_retracted:
        filters.append("is_retracted:false")

    params: dict[str, Any] = {
        "search.semantic": query[:2000],
        "per-page": per_page,
    }

    if filters:
        params["filter"] = ",".join(filters)

    data = _request(
        endpoint="works",
        params=params,
    )

    return _normalize_search_response(data)

def search_oql(
    query: str,
    per_page: int = 25,
    rerank: bool = False,
) -> SearchResult:
    """Search OpenAlex using an OQL query."""

    params: dict[str, Any] = {
        "oql": query,
        "per-page": per_page,
    }

    if rerank:
        params["rerank"] = "true"

    data = _request(
        endpoint="",
        params=params,
    )

    return _normalize_search_response(data)

def translate_oql(query: str) -> dict[str, Any]:
    """Translate and validate OQL without executing the query."""

    url = f"{BASE_URL}/query/oql/{quote(query, safe='')}"

    response = requests.get(
        url,
        timeout=TIMEOUT,
    )

    try:
        data = response.json()
    except ValueError as exc:
        raise RuntimeError(
            f"Invalid response from OpenAlex: {response.text}"
        ) from exc

    return data
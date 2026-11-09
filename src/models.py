from dataclasses import dataclass, field


@dataclass(slots=True)
class Article:
    """Internal representation of a scientific article."""

    openalex_id: str
    title: str

    year: int | None = None
    publication_date: str | None = None

    authors: list[str] = field(default_factory=list)
    source: str | None = None

    doi: str | None = None
    abstract: str | None = None

    concepts: str | None = None
    pdf_url: str | None = None

    cited_by: int = 0

    relevance_score: float | None = None
    
    @property
    def authors_text(self) -> str:
        """Return authors as a human-readable string."""
        return ", ".join(self.authors)


@dataclass(slots=True)
class SearchResult:
    """Normalized result returned by an OpenAlex search."""

    articles: list[Article] = field(default_factory=list)
    total_count: int = 0

    def __len__(self) -> int:
        return len(self.articles)

    def __iter__(self):
        return iter(self.articles)

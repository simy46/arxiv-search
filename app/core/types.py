from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class GeneratedQuery:
    query: str
    categories: list[str] = field(default_factory=list)
    date_from: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GeneratedQuery":
        return cls(
            query=str(data.get("query", "")),
            categories=list(data.get("categories", [])),
            date_from=data.get("date_from"),
        )


@dataclass(slots=True)
class Paper:
    paper_id: str
    title: str
    authors: list[str]
    abstract: str
    published: str
    categories: list[str]
    pdf_url: str
    abs_url: str
    score: float = 0.0
    match_reasons: list[str] = field(default_factory=list)
    downloaded: bool = False
    summary: str | None = None
    highlights: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Paper":
        return cls(
            paper_id=str(data["paper_id"]),
            title=str(data.get("title", "")),
            authors=list(data.get("authors", [])),
            abstract=str(data.get("abstract", "")),
            published=str(data.get("published", "")),
            categories=list(data.get("categories", [])),
            pdf_url=str(data.get("pdf_url", "")),
            abs_url=str(data.get("abs_url", "")),
            score=float(data.get("score", 0.0)),
            match_reasons=list(data.get("match_reasons", [])),
            downloaded=bool(data.get("downloaded", False)),
            summary=data.get("summary"),
            highlights=list(data.get("highlights", [])),
        )


@dataclass(slots=True)
class QueryPlan:
    user_query: str
    generated_queries: list[GeneratedQuery]

    def to_dict(self) -> dict[str, Any]:
        return {
            "user_query": self.user_query,
            "generated_queries": [item.to_dict() for item in self.generated_queries],
        }


@dataclass(slots=True)
class HistoryItem:
    history_id: str
    query: str
    categories: list[str]
    date_from: str | None
    generated_queries: list[GeneratedQuery]
    results: list[Paper]
    created_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "history_id": self.history_id,
            "query": self.query,
            "categories": self.categories,
            "date_from": self.date_from,
            "generated_queries": [item.to_dict() for item in self.generated_queries],
            "results": [paper.to_dict() for paper in self.results],
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "HistoryItem":
        return cls(
            history_id=str(data["history_id"]),
            query=str(data["query"]),
            categories=list(data.get("categories", [])),
            date_from=data.get("date_from"),
            generated_queries=[
                GeneratedQuery.from_dict(item)
                for item in data.get("generated_queries", [])
            ],
            results=[Paper.from_dict(item) for item in data.get("results", [])],
            created_at=str(data["created_at"]),
        )


@dataclass(slots=True)
class SearchResult:
    history_id: str
    cache_hit: bool
    user_query: str
    generated_queries: list[GeneratedQuery]
    results: list[Paper]
    total_candidates: int
    returned_count: int
    searched_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "history_id": self.history_id,
            "cache_hit": self.cache_hit,
            "user_query": self.user_query,
            "generated_queries": [item.to_dict() for item in self.generated_queries],
            "results": [paper.to_dict() for paper in self.results],
            "total_candidates": self.total_candidates,
            "returned_count": self.returned_count,
            "searched_at": self.searched_at,
        }
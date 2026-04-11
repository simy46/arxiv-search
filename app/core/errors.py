from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class ApiServiceError(Exception):
    code: str
    message: str
    status_code: int
    details: dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        return self.message


class RateLimitedError(ApiServiceError):
    def __init__(
        self,
        message: str = (
            "arXiv is rate limiting this IP. Please wait about 60 seconds before retrying."
        ),
    ) -> None:
        super().__init__(
            code="RATE_LIMITED",
            message=message,
            status_code=429,
            details={},
        )


class QueryPlanFailedError(ApiServiceError):
    def __init__(self, message: str) -> None:
        super().__init__(
            code="QUERY_PLAN_FAILED",
            message=message,
            status_code=500,
            details={},
        )


class SearchFailedError(ApiServiceError):
    def __init__(self, message: str) -> None:
        super().__init__(
            code="SEARCH_FAILED",
            message=message,
            status_code=500,
            details={},
        )


class SummaryFailedError(ApiServiceError):
    def __init__(self, message: str) -> None:
        super().__init__(
            code="SUMMARY_FAILED",
            message=message,
            status_code=500,
            details={},
        )

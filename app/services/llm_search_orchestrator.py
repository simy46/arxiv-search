from __future__ import annotations

import logging
import re

from app.core.errors import QueryPlanFailedError
from app.core.logger import log_partial_result
from app.core.types import GeneratedQuery, QueryPlan
from app.adapters.llm_client import LLMClient
from app.params import SEARCH_PARAMS


class LLMSearchOrchestrator:
    def __init__(
        self,
        llm_client: LLMClient,
        logger: logging.Logger,
        log_partial_results: bool = False,
    ) -> None:
        self._llm_client = llm_client
        self._logger = logger
        self._log_partial_results = log_partial_results

    def build_query_plan(
        self,
        user_query: str,
        categories: list[str] | None = None,
        date_from: str | None = None,
    ) -> QueryPlan:
        self._logger.info("orchestrator.build_query_plan user_query=%r", user_query)
        raw = self._llm_client.generate_query_plan(
            user_query=user_query,
            categories=categories or [],
            date_from=date_from,
        )

        generated_queries = self._normalize_generated_queries(
            raw.get("generated_queries", []),
        )

        if len(generated_queries) == 0:
            raise QueryPlanFailedError("LLM returned no valid generated queries")

        log_partial_result(
            self._logger,
            self._log_partial_results,
            "orchestrator.build_query_plan generated_queries=%s",
            [item.query for item in generated_queries],
        )

        return QueryPlan(
            user_query=user_query,
            generated_queries=generated_queries[: SEARCH_PARAMS.max_generated_queries],
        )

    def _normalize_generated_queries(
        self,
        raw_generated_queries: object,
    ) -> list[GeneratedQuery]:
        if not isinstance(raw_generated_queries, list):
            raise QueryPlanFailedError("LLM returned an invalid generated_queries format")

        deduped: list[GeneratedQuery] = []
        normalized_seen: set[str] = set()

        for item in raw_generated_queries:
            if not isinstance(item, dict):
                continue

            query = str(item.get("query", "")).strip()
            if not query:
                continue

            normalized_query = self._normalize_query_for_dedupe(query)
            if normalized_query in normalized_seen:
                continue
            if self._is_obviously_redundant(
                normalized_query,
                normalized_seen,
            ):
                continue

            normalized_seen.add(normalized_query)
            deduped.append(
                GeneratedQuery(
                    query=query,
                    categories=[
                        str(category)
                        for category in item.get("categories", [])
                        if str(category).strip()
                    ]
                    if isinstance(item.get("categories", []), list)
                    else [],
                    date_from=(
                        str(item.get("date_from")).strip()
                        if item.get("date_from") is not None
                        else None
                    )
                    or None,
                )
            )

            if len(deduped) >= SEARCH_PARAMS.max_generated_queries:
                break

        return deduped

    @staticmethod
    def _normalize_query_for_dedupe(query: str) -> str:
        return re.sub(r"\s+", " ", query).strip().lower()

    @staticmethod
    def _is_obviously_redundant(
        candidate_query: str,
        existing_queries: set[str],
    ) -> bool:
        candidate_tokens = {
            token
            for token in re.findall(r"[a-z0-9]+", candidate_query)
            if token
        }

        for existing_query in existing_queries:
            if candidate_query in existing_query or existing_query in candidate_query:
                return True

            existing_tokens = {
                token
                for token in re.findall(r"[a-z0-9]+", existing_query)
                if token
            }
            if not candidate_tokens or not existing_tokens:
                continue

            intersection = len(candidate_tokens.intersection(existing_tokens))
            union = len(candidate_tokens.union(existing_tokens))
            if union > 0 and (intersection / union) >= 0.92:
                return True

        return False

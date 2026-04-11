from __future__ import annotations

import logging

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

        generated_queries = [
            GeneratedQuery(
                query=str(item["query"]),
                categories=list(item.get("categories", [])),
                date_from=item.get("date_from"),
            )
            for item in raw.get("generated_queries", [])
            if item.get("query")
        ]

        if not generated_queries:
            generated_queries = [
                GeneratedQuery(
                    query=user_query,
                    categories=categories or [],
                    date_from=date_from,
                )
            ]
            self._logger.info("orchestrator.build_query_plan used_default_query")

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

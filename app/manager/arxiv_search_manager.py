from __future__ import annotations

import logging

from app.core.errors import SearchFailedError
from app.core.logger import log_partial_result
from app.core.types import Paper, SearchResult
from app.manager.history_manager import HistoryManager
from app.services.llm_search_orchestrator import LLMSearchOrchestrator
from app.services.reranker import Reranker
from app.adapters.mcp_arxiv_client import MCPArxivClient


class ArxivSearchManager:
    def __init__(
        self,
        history_manager: HistoryManager,
        llm_search_orchestrator: LLMSearchOrchestrator,
        reranker: Reranker,
        mcp_arxiv_client: MCPArxivClient,
        logger: logging.Logger,
        log_partial_results: bool = False,
        max_results: int | None = None,
    ) -> None:
        self._history_manager = history_manager
        self._llm_search_orchestrator = llm_search_orchestrator
        self._reranker = reranker
        self._mcp_arxiv_client = mcp_arxiv_client
        self._logger = logger
        self._log_partial_results = log_partial_results
        self._max_results = max_results

    def search(
        self,
        query: str,
        categories: list[str] | None = None,
        date_from: str | None = None,
    ) -> SearchResult:
        self._logger.info(
            "search_manager.search start query=%r categories=%s date_from=%s",
            query,
            categories or [],
            date_from,
        )
        pending_history_item = self._history_manager.create_pending_history_item(
            query=query,
            categories=categories,
            date_from=date_from,
        )

        try:
            existing = self._history_manager.find_matching_search(
                query=query,
                categories=categories,
                date_from=date_from,
            )
            if existing is not None and self._max_results is None:
                # Unlimited mode should not reuse legacy-capped history rows.
                self._logger.info(
                    "search_manager.search skip_cache_unlimited source_history_id=%s existing_count=%s",
                    existing.history_id,
                    len(existing.results),
                )
                existing = None
            if existing is not None:
                self._logger.info(
                    "search_manager.search cache_reused source_history_id=%s result_count=%s",
                    existing.history_id,
                    len(existing.results),
                )
                updated_pending = self._history_manager.update_history_item_results(
                    history_id=pending_history_item.history_id,
                    generated_queries=existing.generated_queries,
                    results=existing.results,
                )
                if updated_pending is None:
                    raise SearchFailedError("Could not finalize cache-hit history item")

                return SearchResult(
                    history_id=updated_pending.history_id,
                    cache_hit=True,
                    user_query=query,
                    generated_queries=existing.generated_queries,
                    results=existing.results,
                    total_candidates=len(existing.results),
                    returned_count=len(existing.results),
                    searched_at=updated_pending.created_at,
                )

            query_plan = self._llm_search_orchestrator.build_query_plan(
                user_query=query,
                categories=categories,
                date_from=date_from,
            )
            self._logger.info(
                "search_manager.search query_plan_count=%s",
                len(query_plan.generated_queries),
            )

            collected_by_id: dict[str, Paper] = {}
            executed_queries = []

            for generated_query in query_plan.generated_queries:
                self._logger.info(
                    "search_manager.search execute_generated_query query=%r",
                    generated_query.query,
                )
                papers = self._mcp_arxiv_client.search_papers(
                    query=generated_query.query,
                    categories=generated_query.categories,
                    date_from=generated_query.date_from,
                    max_results=self._max_results,
                )
                executed_queries.append(generated_query)

                log_partial_result(
                    self._logger,
                    self._log_partial_results,
                    "search_manager.search generated_query=%r returned_count=%s",
                    generated_query.query,
                    len(papers),
                )

                for paper in papers:
                    collected_by_id[paper.paper_id] = paper

            ranked_results = self._reranker.rank(
                user_query=query,
                papers=list(collected_by_id.values()),
                limit=self._max_results,
            )
            self._logger.info(
                "search_manager.search ranked_results=%s total_candidates=%s",
                len(ranked_results),
                len(collected_by_id),
            )
            log_partial_result(
                self._logger,
                self._log_partial_results,
                "search_manager.search top_ranked_ids=%s",
                [paper.paper_id for paper in ranked_results[:5]],
            )

            history_item = self._history_manager.update_history_item_results(
                history_id=pending_history_item.history_id,
                generated_queries=executed_queries,
                results=ranked_results,
            )
            if history_item is None:
                raise SearchFailedError("Could not finalize history item")

            return SearchResult(
                history_id=history_item.history_id,
                cache_hit=False,
                user_query=query,
                generated_queries=executed_queries,
                results=ranked_results,
                total_candidates=len(collected_by_id),
                returned_count=len(ranked_results),
                searched_at=history_item.created_at,
            )
        except Exception as exc:
            self._history_manager.mark_history_item_failed(
                history_id=pending_history_item.history_id,
                error_message=str(exc) or "Search failed",
            )
            raise

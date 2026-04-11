from __future__ import annotations

import logging
import threading
from datetime import datetime, timezone

from app.core.logger import log_partial_result
from app.core.types import GeneratedQuery, HistoryItem, Paper
from app.services.history_store import HistoryStore


class HistoryManager:
    def __init__(
        self,
        store: HistoryStore,
        logger: logging.Logger,
        log_partial_results: bool = False,
    ) -> None:
        self._store = store
        self._logger = logger
        self._log_partial_results = log_partial_results
        self._mutation_lock = threading.RLock()

    def list_history(self, page: int = 1, page_size: int = 10) -> dict[str, object]:
        self._logger.info("history_manager.list_history page=%s page_size=%s", page, page_size)
        items = self._store.load_all()

        start = (page - 1) * page_size
        end = start + page_size
        page_items = items[start:end]

        compact_items = [
            {
                "history_id": item.history_id,
                "query": item.query,
                "created_at": item.created_at,
                "result_count": len(item.results),
                "status": item.status,
                "error_message": item.error_message,
            }
            for item in page_items
        ]

        log_partial_result(
            self._logger,
            self._log_partial_results,
            "history_manager.list_history total_items=%s returned_items=%s",
            len(items),
            len(compact_items),
        )
        return {
            "items": compact_items,
            "page": page,
            "page_size": page_size,
            "has_next": end < len(items),
        }

    def get_history_item(self, history_id: str) -> HistoryItem | None:
        self._logger.info("history_manager.get_history_item history_id=%s", history_id)
        items = self._store.load_all()
        for item in items:
            if item.history_id == history_id:
                self._logger.info("history_manager.get_history_item hit history_id=%s", history_id)
                return item
        self._logger.info("history_manager.get_history_item miss history_id=%s", history_id)
        return None

    def create_pending_history_item(
        self,
        query: str,
        categories: list[str] | None,
        date_from: str | None,
    ) -> HistoryItem:
        with self._mutation_lock:
            self._logger.info("history_manager.create_pending_history_item query=%r", query)
            items = self._store.load_all()

            history_item = HistoryItem(
                history_id=self._build_history_id(),
                query=query,
                categories=categories or [],
                date_from=date_from,
                generated_queries=[],
                results=[],
                created_at=datetime.now(timezone.utc).isoformat(),
                status="running",
                error_message=None,
            )

            items.insert(0, history_item)
            self._store.save_all(items)
            self._logger.info(
                "history_manager.create_pending_history_item created history_id=%s",
                history_item.history_id,
            )
            return history_item

    def update_history_item_results(
        self,
        history_id: str,
        generated_queries: list[GeneratedQuery],
        results: list[Paper],
    ) -> HistoryItem | None:
        with self._mutation_lock:
            self._logger.info(
                "history_manager.update_history_item_results history_id=%s result_count=%s",
                history_id,
                len(results),
            )
            items = self._store.load_all()

            for item in items:
                if item.history_id != history_id:
                    continue

                item.generated_queries = generated_queries
                item.results = results
                item.status = "completed"
                item.error_message = None
                self._store.save_all(items)
                return item

            self._logger.warning(
                "history_manager.update_history_item_results history_not_found history_id=%s",
                history_id,
            )
            return None

    def mark_history_item_failed(
        self,
        history_id: str,
        error_message: str,
    ) -> HistoryItem | None:
        with self._mutation_lock:
            self._logger.info(
                "history_manager.mark_history_item_failed history_id=%s",
                history_id,
            )
            items = self._store.load_all()

            for item in items:
                if item.history_id != history_id:
                    continue

                item.status = "failed"
                item.error_message = error_message
                self._store.save_all(items)
                return item

            self._logger.warning(
                "history_manager.mark_history_item_failed history_not_found history_id=%s",
                history_id,
            )
            return None

    def attach_summary(
        self,
        history_id: str,
        paper_id: str,
        summary: str,
        highlights: list[str],
    ) -> HistoryItem | None:
        with self._mutation_lock:
            self._logger.info(
                "history_manager.attach_summary history_id=%s paper_id=%s",
                history_id,
                paper_id,
            )
            items = self._store.load_all()

            for item in items:
                if item.history_id != history_id:
                    continue

                for paper in item.results:
                    if paper.paper_id == paper_id:
                        paper.summary = summary
                        paper.highlights = highlights
                        self._store.save_all(items)
                        log_partial_result(
                            self._logger,
                            self._log_partial_results,
                            "history_manager.attach_summary highlights=%s",
                            highlights,
                        )
                        return item

                self._logger.info(
                    "history_manager.attach_summary paper_not_found history_id=%s paper_id=%s",
                    history_id,
                    paper_id,
                )
                return None

            self._logger.info(
                "history_manager.attach_summary history_not_found history_id=%s",
                history_id,
            )
            return None

    def find_matching_search(
        self,
        query: str,
        categories: list[str] | None,
        date_from: str | None,
    ) -> HistoryItem | None:
        self._logger.info("history_manager.find_matching_search query=%r", query)
        normalized_key = self._normalize_search_key(query, categories, date_from)

        for item in self._store.load_all():
            if item.status != "completed":
                continue
            if len(item.results) == 0:
                continue
            item_key = self._normalize_search_key(
                item.query,
                item.categories,
                item.date_from,
            )
            if item_key == normalized_key:
                self._logger.info(
                    "history_manager.find_matching_search hit history_id=%s",
                    item.history_id,
                )
                return item

        self._logger.info("history_manager.find_matching_search miss")
        return None

    # Backward-compatible helper for legacy callers.
    def create_history_item(
        self,
        query: str,
        categories: list[str] | None,
        date_from: str | None,
        generated_queries: list[GeneratedQuery],
        results: list[Paper],
    ) -> HistoryItem:
        pending = self.create_pending_history_item(
            query=query,
            categories=categories,
            date_from=date_from,
        )
        updated = self.update_history_item_results(
            history_id=pending.history_id,
            generated_queries=generated_queries,
            results=results,
        )
        return updated if updated is not None else pending

    def _build_history_id(self) -> str:
        return f"hist_{int(datetime.now(timezone.utc).timestamp() * 1000)}"

    @staticmethod
    def _normalize_search_key(
        query: str,
        categories: list[str] | None,
        date_from: str | None,
    ) -> tuple[str, tuple[str, ...], str | None]:
        normalized_query = " ".join(query.lower().split())
        normalized_categories = tuple(sorted(categories or []))
        normalized_date = date_from or None
        return normalized_query, normalized_categories, normalized_date

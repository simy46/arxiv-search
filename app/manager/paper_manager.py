from __future__ import annotations

import logging

from app.core.errors import ApiServiceError, SummaryFailedError
from app.core.logger import log_partial_result
from app.adapters.llm_client import LLMClient
from app.adapters.mcp_arxiv_client import MCPArxivClient
from app.manager.history_manager import HistoryManager


class PaperManager:
    def __init__(
        self,
        history_manager: HistoryManager,
        llm_client: LLMClient,
        mcp_arxiv_client: MCPArxivClient,
        logger: logging.Logger,
        log_partial_results: bool = False,
    ) -> None:
        self._history_manager = history_manager
        self._llm_client = llm_client
        self._mcp_arxiv_client = mcp_arxiv_client
        self._logger = logger
        self._log_partial_results = log_partial_results

    def download_paper(self, paper_id: str) -> dict[str, object]:
        self._logger.info("paper_manager.download_paper paper_id=%s", paper_id)
        response = self._mcp_arxiv_client.download_paper(paper_id)
        log_partial_result(
            self._logger,
            self._log_partial_results,
            "paper_manager.download_paper response=%s",
            response,
        )
        return response

    def summarize_paper(
        self,
        history_id: str,
        paper_id: str,
        style: str = "brief",
    ) -> dict[str, object]:
        self._logger.info(
            "paper_manager.summarize_paper history_id=%s paper_id=%s style=%s",
            history_id,
            paper_id,
            style,
        )
        try:
            self._mcp_arxiv_client.download_paper(paper_id)
            content_markdown = self._mcp_arxiv_client.read_paper(paper_id)
            log_partial_result(
                self._logger,
                self._log_partial_results,
                "paper_manager.summarize_paper markdown_length=%s",
                len(content_markdown),
            )

            summary_payload = self._llm_client.summarize_markdown(
                markdown_text=content_markdown,
                style=style,
            )
            log_partial_result(
                self._logger,
                self._log_partial_results,
                "paper_manager.summarize_paper summary_payload=%s",
                summary_payload,
            )

            updated_history = self._history_manager.attach_summary(
                history_id=history_id,
                paper_id=paper_id,
                summary=str(summary_payload["summary"]),
                highlights=list(summary_payload["highlights"]),
            )

            if updated_history is None:
                self._logger.error(
                    "paper_manager.summarize_paper attach_failed history_id=%s paper_id=%s",
                    history_id,
                    paper_id,
                )
                raise SummaryFailedError("Could not attach summary to history item")

            self._logger.info(
                "paper_manager.summarize_paper completed history_id=%s paper_id=%s",
                history_id,
                paper_id,
            )
            return {
                "history_id": history_id,
                "paper_id": paper_id,
                "summary": summary_payload["summary"],
                "highlights": summary_payload["highlights"],
            }
        except ApiServiceError:
            raise
        except Exception as exc:
            raise SummaryFailedError(str(exc) or "Summary failed") from exc

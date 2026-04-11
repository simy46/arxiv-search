from __future__ import annotations

import asyncio
import json
import logging
from contextlib import AsyncExitStack
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from app.core.logger import log_partial_result
from app.core.types import Paper
from app.params import MCP_PARAMS


class MCPArxivClient:
    def __init__(
        self,
        logger: logging.Logger,
        log_partial_results: bool = False,
    ) -> None:
        self._logger = logger
        self._log_partial_results = log_partial_results
        self._server_params = StdioServerParameters(
            command=MCP_PARAMS.command,
            args=list(MCP_PARAMS.args),
            env=None,
        )
        self._logger.info(
            "mcp_client.init command=%s args=%s",
            MCP_PARAMS.command,
            list(MCP_PARAMS.args),
        )

    def search_papers(
        self,
        query: str,
        categories: list[str] | None = None,
        date_from: str | None = None,
        max_results: int = 20,
    ) -> list[Paper]:
        self._logger.info(
            "mcp_client.search_papers query=%r max_results=%s",
            query,
            max_results,
        )

        arguments: dict[str, Any] = {
            "query": query,
            "max_results": max_results,
            "sort_by": "relevance",
        }

        if categories:
            arguments["categories"] = categories

        if date_from:
            arguments["date_from"] = date_from

        result = asyncio.run(self._call_tool("search_papers", arguments))
        papers = self._normalize_search_results(result)

        log_partial_result(
            self._logger,
            self._log_partial_results,
            "mcp_client.search_papers result_count=%s",
            len(papers),
        )
        return papers

    def download_paper(self, paper_id: str) -> dict[str, Any]:
        self._logger.info("mcp_client.download_paper paper_id=%s", paper_id)
        result = asyncio.run(
            self._call_tool(
                "download_paper",
                {"paper_id": paper_id},
            )
        )

        if isinstance(result, dict):
            return result

        return {
            "paper_id": paper_id,
            "downloaded": False,
            "message": str(result),
        }

    def read_paper(self, paper_id: str) -> str:
        self._logger.info("mcp_client.read_paper paper_id=%s", paper_id)
        result = asyncio.run(
            self._call_tool(
                "read_paper",
                {"paper_id": paper_id},
            )
        )

        if isinstance(result, dict):
            content = (
                result.get("content_markdown")
                or result.get("content")
                or result.get("raw_text")
                or ""
            )
            return str(content)

        return str(result)

    async def _call_tool(self, tool_name: str, arguments: dict[str, Any]) -> Any:
        self._logger.info("mcp_client.call_tool start tool=%s", tool_name)
        log_partial_result(
            self._logger,
            self._log_partial_results,
            "mcp_client.call_tool arguments=%s",
            arguments,
        )

        async with AsyncExitStack() as stack:
            read_stream, write_stream = await stack.enter_async_context(
                stdio_client(self._server_params)
            )

            session = await stack.enter_async_context(
                ClientSession(read_stream, write_stream)
            )

            await session.initialize()
            result = await session.call_tool(tool_name, arguments)

            if getattr(result, "isError", False):
                error_text = self._extract_text_content(result)
                self._logger.error(
                    "mcp_client.call_tool error tool=%s error=%r",
                    tool_name,
                    error_text,
                )
                return {"error": error_text}

            structured_content = getattr(result, "structuredContent", None)
            if structured_content is not None:
                self._logger.info(
                    "mcp_client.call_tool success tool=%s structured_content",
                    tool_name,
                )
                return structured_content

            text = self._extract_text_content(result)
            if not text:
                self._logger.warning(
                    "mcp_client.call_tool empty_response tool=%s",
                    tool_name,
                )
                return {}

            try:
                parsed = json.loads(text)
                self._logger.info(
                    "mcp_client.call_tool success tool=%s parsed_json",
                    tool_name,
                )
                return parsed
            except json.JSONDecodeError:
                self._logger.info(
                    "mcp_client.call_tool success tool=%s raw_text",
                    tool_name,
                )
                return {"raw_text": text}

    def _extract_text_content(self, result: Any) -> str:
        content = getattr(result, "content", None) or []
        text_parts: list[str] = []

        for item in content:
            text = getattr(item, "text", None)
            if text:
                text_parts.append(str(text))

        return "\n".join(text_parts).strip()

    def _normalize_search_results(self, payload: Any) -> list[Paper]:
        raw_items: list[dict[str, Any]] = []

        if payload is None:
            return []

        if isinstance(payload, list):
            raw_items = [item for item in payload if isinstance(item, dict)]

        elif isinstance(payload, dict):
            if "error" in payload:
                self._logger.error(
                    "mcp_client.search_papers tool_error=%r",
                    payload["error"],
                )
                return []

            for key in ("results", "papers", "items"):
                value = payload.get(key)
                if isinstance(value, list):
                    raw_items = [item for item in value if isinstance(item, dict)]
                    break

        papers: list[Paper] = []
        for item in raw_items:
            paper_id = str(
                item.get("paper_id")
                or item.get("id")
                or item.get("arxiv_id")
                or ""
            ).strip()

            if not paper_id:
                continue

            title = str(item.get("title") or "").strip()

            authors = item.get("authors") or []
            if not isinstance(authors, list):
                authors = [str(authors)]

            abstract = str(item.get("abstract") or item.get("summary") or "").strip()
            published = str(item.get("published") or item.get("date") or "").strip()

            item_categories = item.get("categories") or []
            if not isinstance(item_categories, list):
                item_categories = [str(item_categories)]

            pdf_url = str(item.get("pdf_url") or item.get("pdf") or "").strip()
            abs_url = str(item.get("abs_url") or item.get("url") or "").strip()

            papers.append(
                Paper(
                    paper_id=paper_id,
                    title=title,
                    authors=[str(author) for author in authors],
                    abstract=abstract,
                    published=published,
                    categories=[str(category) for category in item_categories],
                    pdf_url=pdf_url,
                    abs_url=abs_url,
                )
            )

        return papers
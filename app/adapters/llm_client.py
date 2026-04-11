from __future__ import annotations

import json
import logging
import os
import re
from typing import Any

from openai import OpenAI

from app.core.errors import QueryPlanFailedError, SummaryFailedError
from app.core.logger import log_partial_result
from app.params import LLM_PARAMS, SEARCH_SYSTEM_PROMPT, SUMMARY_SYSTEM_PROMPT


class LLMClient:
    def __init__(
        self,
        logger: logging.Logger,
        log_partial_results: bool = False,
    ) -> None:
        self._logger = logger
        self._log_partial_results = log_partial_results

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            self._logger.error("llm_client.init missing OPENAI_API_KEY")
            raise RuntimeError("OPENAI_API_KEY is missing")

        self._client = OpenAI(api_key=api_key)
        self._logger.info("llm_client.init model=%s", LLM_PARAMS.model)

    def generate_query_plan(
        self,
        user_query: str,
        categories: list[str],
        date_from: str | None,
    ) -> dict[str, Any]:
        self._logger.info("llm_client.generate_query_plan query=%r", user_query)
        try:
            user_payload = {
                "user_query": user_query,
                "categories": categories,
                "date_from": date_from,
            }

            response = self._client.responses.create(
                model=LLM_PARAMS.model,
                input=[
                    {"role": "developer", "content": SEARCH_SYSTEM_PROMPT},
                    {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)},
                ],
                max_output_tokens=LLM_PARAMS.max_query_plan_tokens,
            )

            text = (response.output_text or "").strip()
            log_partial_result(
                self._logger,
                self._log_partial_results,
                "llm_client.generate_query_plan raw_response_preview=%r",
                text[:600],
            )

            parsed = self._parse_json_response(text)

            if "generated_queries" not in parsed:
                raise QueryPlanFailedError("LLM query plan missing 'generated_queries'")

            generated_queries = parsed["generated_queries"]
            if not isinstance(generated_queries, list) or len(generated_queries) == 0:
                raise QueryPlanFailedError("LLM query plan returned no generated queries")

            normalized_queries: list[dict[str, Any]] = []
            for item in generated_queries:
                if not isinstance(item, dict):
                    raise QueryPlanFailedError("LLM query plan contains a non-object entry")

                query = str(item.get("query", "")).strip()
                if not query:
                    continue

                item_categories = item.get("categories", [])
                if not isinstance(item_categories, list):
                    item_categories = []

                item_date_from = item.get("date_from")
                if item_date_from is not None:
                    item_date_from = str(item_date_from).strip() or None

                normalized_queries.append(
                    {
                        "query": query,
                        "categories": [str(category) for category in item_categories],
                        "date_from": item_date_from,
                    }
                )

            if len(normalized_queries) == 0:
                raise QueryPlanFailedError("LLM query plan produced no valid queries")

            self._logger.info(
                "llm_client.generate_query_plan parsed_success count=%s",
                len(normalized_queries),
            )
            return {"generated_queries": normalized_queries}
        except QueryPlanFailedError:
            raise
        except Exception as exc:
            raise QueryPlanFailedError(str(exc)) from exc

    def summarize_markdown(
        self,
        markdown_text: str,
        style: str = "brief",
    ) -> dict[str, Any]:
        self._logger.info("llm_client.summarize_markdown style=%s", style)
        try:
            user_payload = {
                "style": style,
                "paper_markdown": markdown_text[:120000],
            }

            response = self._client.responses.create(
                model=LLM_PARAMS.model,
                input=[
                    {"role": "developer", "content": SUMMARY_SYSTEM_PROMPT},
                    {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)},
                ],
                max_output_tokens=LLM_PARAMS.max_summary_tokens,
            )

            text = (response.output_text or "").strip()
            log_partial_result(
                self._logger,
                self._log_partial_results,
                "llm_client.summarize_markdown raw_response_preview=%r",
                text[:600],
            )

            parsed = self._parse_json_response(text)

            summary = str(parsed.get("summary", "")).strip()
            highlights = parsed.get("highlights", [])

            if not summary:
                raise SummaryFailedError("LLM summary response missing 'summary'")

            if not isinstance(highlights, list):
                highlights = []

            return {
                "summary": summary,
                "highlights": [str(item) for item in highlights],
            }
        except SummaryFailedError:
            raise
        except Exception as exc:
            raise SummaryFailedError(str(exc)) from exc

    def _parse_json_response(self, text: str) -> dict[str, Any]:
        if not text:
            raise RuntimeError("Model returned empty output")

        candidate = text.strip()

        if candidate.startswith("```"):
            candidate = re.sub(r"^```(?:json)?\s*", "", candidate)
            candidate = re.sub(r"\s*```$", "", candidate)

        try:
            parsed = json.loads(candidate)
            if not isinstance(parsed, dict):
                raise RuntimeError("Parsed JSON is not an object")
            return parsed
        except json.JSONDecodeError:
            pass

        match = re.search(r"\{.*\}", candidate, re.DOTALL)
        if not match:
            raise RuntimeError(f"Could not find JSON object in model output: {candidate[:300]!r}")

        parsed = json.loads(match.group(0))
        if not isinstance(parsed, dict):
            raise RuntimeError("Parsed JSON is not an object")

        return parsed

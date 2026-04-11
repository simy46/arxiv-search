from __future__ import annotations

import json
import logging
import os
import re
from typing import Any

from openai import OpenAI

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
        user_payload = {
            "user_query": user_query,
            "categories": categories,
            "date_from": date_from,
        }

        response = self._client.responses.create(
            model=LLM_PARAMS.model,
            max_output_tokens=LLM_PARAMS.max_query_plan_tokens,
            input=[
                {"role": "developer", "content": SEARCH_SYSTEM_PROMPT},
                {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)},
            ],
        )

        text = (response.output_text or "").strip()
        log_partial_result(
            self._logger,
            self._log_partial_results,
            "llm_client.generate_query_plan raw_response_preview=%r",
            text[:600],
        )

        try:
            parsed = self._parse_json_response(text)
            self._logger.info("llm_client.generate_query_plan parsed_success")
            return parsed
        except Exception:
            self._logger.exception("llm_client.generate_query_plan parse_failed using_fallback")
            return self._fallback_query_plan(
                user_query=user_query,
                categories=categories,
                date_from=date_from,
            )

    def summarize_markdown(
        self,
        markdown_text: str,
        style: str = "brief",
    ) -> dict[str, Any]:
        self._logger.info("llm_client.summarize_markdown style=%s", style)
        user_payload = {
            "style": style,
            "paper_markdown": markdown_text[:120000],
        }

        response = self._client.responses.create(
            model=LLM_PARAMS.model,
            max_output_tokens=LLM_PARAMS.max_summary_tokens,
            input=[
                {"role": "developer", "content": SUMMARY_SYSTEM_PROMPT},
                {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)},
            ],
        )

        text = (response.output_text or "").strip()
        log_partial_result(
            self._logger,
            self._log_partial_results,
            "llm_client.summarize_markdown raw_response_preview=%r",
            text[:600],
        )

        try:
            parsed = self._parse_json_response(text)
            self._logger.info("llm_client.summarize_markdown parsed_success")
            return parsed
        except Exception:
            self._logger.exception("llm_client.summarize_markdown parse_failed using_fallback")
            preview = " ".join(markdown_text.split())[:400]
            return {
                "summary": preview + "..." if preview else "No content available.",
                "highlights": [
                    "Automatic summary fallback",
                    "Model did not return valid JSON",
                    "Review paper manually if needed",
                ],
            }

    def _parse_json_response(self, text: str) -> dict[str, Any]:
        if not text:
            raise ValueError("Model returned empty output")

        # remove fenced code blocks if present
        text = text.strip()
        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?\s*", "", text)
            text = re.sub(r"\s*```$", "", text)

        # direct parse first
        try:
            parsed = json.loads(text)
            if not isinstance(parsed, dict):
                raise ValueError("Parsed JSON is not an object")
            return parsed
        except json.JSONDecodeError:
            pass

        # extract first JSON object from mixed text
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            raise ValueError(f"Could not find JSON object in model output: {text[:300]!r}")

        parsed = json.loads(match.group(0))
        if not isinstance(parsed, dict):
            raise ValueError("Parsed JSON is not an object")

        return parsed

    def _fallback_query_plan(
        self,
        user_query: str,
        categories: list[str],
        date_from: str | None,
    ) -> dict[str, Any]:
        self._logger.info("llm_client.fallback_query_plan query=%r", user_query)
        normalized = " ".join(user_query.split()).strip()

        variants = [
            normalized,
            f"\"{normalized}\"",
        ]

        lower = normalized.lower()
        if "cpdlc" in lower:
            variants.append("CPDLC human factors workload")
        if "pilot" in lower:
            variants.append("pilot workload aviation human factors")
        if "air traffic" in lower or "atc" in lower:
            variants.append("air traffic control human factors communication")

        seen: set[str] = set()
        generated_queries: list[dict[str, Any]] = []

        for query in variants:
            q = " ".join(query.split()).strip()
            if not q or q in seen:
                continue
            seen.add(q)
            generated_queries.append(
                {
                    "query": q,
                    "categories": categories,
                    "date_from": date_from,
                }
            )

        fallback = {"generated_queries": generated_queries[:5]}
        log_partial_result(
            self._logger,
            self._log_partial_results,
            "llm_client.fallback_query_plan generated=%s",
            fallback,
        )
        return fallback

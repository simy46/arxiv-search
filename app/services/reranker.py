from __future__ import annotations

import logging
import re
from collections import Counter

from app.core.logger import log_partial_result
from app.core.types import Paper


class Reranker:
    _STOPWORDS = {
        "a",
        "an",
        "and",
        "are",
        "as",
        "at",
        "be",
        "by",
        "for",
        "from",
        "in",
        "into",
        "is",
        "of",
        "on",
        "or",
        "paper",
        "papers",
        "study",
        "studies",
        "the",
        "their",
        "this",
        "to",
        "using",
        "with",
        "work",
    }

    def __init__(
        self,
        logger: logging.Logger,
        log_partial_results: bool = False,
    ) -> None:
        self._logger = logger
        self._log_partial_results = log_partial_results

    def rank(
        self,
        user_query: str,
        papers: list[Paper],
        limit: int | None = None,
    ) -> list[Paper]:
        self._logger.info(
            "reranker.rank user_query=%r input_count=%s limit=%s",
            user_query,
            len(papers),
            limit,
        )

        query_tokens = self._tokenize(user_query)
        query_token_counts = Counter(query_tokens)
        query_phrases = self._build_phrases(query_tokens)

        for paper in papers:
            title_text = paper.title.lower()
            abstract_text = paper.abstract.lower()
            full_text = f"{title_text} {abstract_text}"

            title_tokens = Counter(self._tokenize(title_text))
            abstract_tokens = Counter(self._tokenize(abstract_text))

            score = 0.0
            reasons: list[str] = []

            token_matches = 0
            for token, wanted_count in query_token_counts.items():
                if token in title_tokens:
                    score += 3.0 * min(title_tokens[token], wanted_count)
                    token_matches += 1
                elif token in abstract_tokens:
                    score += 1.5 * min(abstract_tokens[token], wanted_count)
                    token_matches += 1

            phrase_matches = 0
            for phrase in query_phrases:
                if phrase in title_text:
                    score += 4.0
                    phrase_matches += 1
                elif phrase in abstract_text:
                    score += 2.5
                    phrase_matches += 1

            # mild recency bonus only
            if paper.published:
                score += 0.25
                reasons.append("has publication date")

            if token_matches > 0:
                reasons.append(f"matched {token_matches} query tokens")

            if phrase_matches > 0:
                reasons.append(f"matched {phrase_matches} query phrases")

            paper.score = score
            paper.match_reasons = reasons

        ranked = sorted(
            papers,
            key=lambda item: (item.score, item.published),
            reverse=True,
        )
        top_ranked = ranked if limit is None else ranked[:limit]

        log_partial_result(
            self._logger,
            self._log_partial_results,
            "reranker.rank top_results=%s",
            [
                {
                    "paper_id": paper.paper_id,
                    "score": paper.score,
                    "title": paper.title,
                }
                for paper in top_ranked[:5]
            ],
        )
        return top_ranked

    def _tokenize(self, text: str) -> list[str]:
        tokens = re.findall(r"[a-zA-Z0-9\-]+", text.lower())
        return [
            token
            for token in tokens
            if len(token) >= 2 and token not in self._STOPWORDS
        ]

    def _build_phrases(self, tokens: list[str]) -> list[str]:
        phrases: list[str] = []

        # bigrams
        for i in range(len(tokens) - 1):
            phrases.append(f"{tokens[i]} {tokens[i + 1]}")

        # trigrams
        for i in range(len(tokens) - 2):
            phrases.append(f"{tokens[i]} {tokens[i + 1]} {tokens[i + 2]}")

        return phrases

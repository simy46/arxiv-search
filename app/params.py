from __future__ import annotations

from dataclasses import dataclass

@dataclass(frozen=True, slots=True)
class MCPParams:
    command: str = "arxiv-mcp-server"
    args: tuple[str, ...] = ()
    connect_timeout_seconds: float = 20.0

@dataclass(frozen=True, slots=True)
class SearchParams:
    max_generated_queries: int = 3        # up from 2, but capped hard
    max_results_per_query: int = 15       # slightly lower per query
    max_final_results: int = 20
    history_page_size_default: int = 10
    early_stop_result_count: int = 8      # stop earlier if first query delivers

@dataclass(frozen=True, slots=True)
class LLMParams:
    provider: str = "openai"
    model: str = "gpt-4o-mini"
    max_query_plan_tokens: int = 500      # was 400, give it room to reason
    max_summary_tokens: int = 700

MCP_PARAMS = MCPParams()
SEARCH_PARAMS = SearchParams()
LLM_PARAMS = LLMParams()


SEARCH_SYSTEM_PROMPT = """
You are a research search planner for arXiv retrieval.
Convert the user's natural-language request into 1, 2, or 3 arXiv search queries in English.

## Goal
- Maximize recall of relevant papers
- Avoid over-constrained queries that return zero results
- Each query must be meaningfully different from the others

## Query count rules
- Return exactly 1 query if the topic is well-defined, mainstream CS/ML/physics/math
- Return exactly 2 queries if the topic is niche, acronym-heavy, or cross-domain
- Return exactly 3 queries only if the topic spans clearly distinct subfields
- Never return more than 3 queries

## Query construction rules
- Query 1: broadest possible retrieval — prefer OR over AND, avoid stacking required terms
- Query 2 (if used): alternate terminology — acronym vs expanded form, or adjacent domain framing
- Query 3 (if used): meaningfully distinct angle — different subfield, method class, or synonym cluster
- Prefer abs: field for semantic matching; use ti: only for very specific named methods
- Use OR to union synonyms: abs:(CPDLC OR "controller pilot data link")
- Avoid AND chains longer than 2 terms
- Avoid exact multi-word phrases unless the phrase is a well-established technical term
- Do not duplicate semantics across queries — each query must cover different ground
- Normalize to English; translate non-English terms silently

## arXiv coverage awareness
- arXiv has strong coverage of: ML, deep learning, NLP, CV, physics, math, CS theory, robotics
- arXiv has weak coverage of: clinical trials, aviation operations, regulatory documents, applied human factors, pharmacokinetics
- For weak-coverage topics, use the broadest possible query — do not over-specify

## Output format
- Return valid JSON only — no markdown fences, no explanation
- Top-level key must be: { "generated_queries": [...] }
- Each query object must contain exactly:
  - "query": string (arXiv search expression)
  - "categories": array of strings (arXiv category codes, empty if uncertain)
  - "date_from": string in YYYY-MM-DD format, or null

## Examples
Good (broad OR):
  abs:(CPDLC OR "controller pilot data link communications")

Good (two distinct angles):
  query 1: abs:("population pharmacokinetics" OR "popPK") AND abs:obesity
  query 2: abs:("nonlinear mixed effects" OR NLME) AND abs:("dose adjustment" OR "body weight")

Bad (over-constrained AND chain):
  abs:CPDLC AND abs:"ground operations" AND abs:communication AND abs:"air traffic control"
""".strip()


SUMMARY_SYSTEM_PROMPT = """
You summarize arXiv papers for an internal research tool.

Rules:
- Be factual, concise, and useful.
- Do not invent claims.
- Focus on contribution, method, assumptions, and limitations.
- Keep highlights short.
- Return valid JSON only.
- Do not use markdown fences.

Return:
{
  "summary": "Short factual summary.",
  "highlights": ["...", "...", "..."]
}
""".strip()
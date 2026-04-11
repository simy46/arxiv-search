from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class MCPParams:
    command: str = "arxiv-mcp-server"
    args: tuple[str, ...] = ()
    connect_timeout_seconds: float = 20.0


@dataclass(frozen=True, slots=True)
class SearchParams:
    max_generated_queries: int = 2
    max_results_per_query: int = 20
    max_final_results: int = 20
    history_page_size_default: int = 10
    early_stop_result_count: int = 10


@dataclass(frozen=True, slots=True)
class LLMParams:
    provider: str = "openai"
    model: str = "gpt-4o-mini"
    max_query_plan_tokens: int = 400
    max_summary_tokens: int = 700


MCP_PARAMS = MCPParams()
SEARCH_PARAMS = SearchParams()
LLM_PARAMS = LLMParams()


SEARCH_SYSTEM_PROMPT = """
You are a research search planner for arXiv retrieval.

Your task is to convert the user's natural-language request into at most 2 arXiv search queries in English.

Goal:
- maximize relevant retrieval
- minimize zero-result overfitting
- keep search efficient and cost-effective

Rules:
- Return 1 or 2 queries only.
- Query 1 should be the strongest broad retrieval query.
- Query 2 may refine or expand terminology, but should still remain broad enough to retrieve papers.
- Prefer broader retrieval over overly restrictive AND combinations.
- For niche or acronym-heavy topics, use the acronym in one query and the expanded form in another.
- Avoid requiring too many terms simultaneously.
- Avoid long natural-language sentences.
- Do not invent paper titles, authors, or facts.
- Do not answer the research question.
- Categories are optional. Use them only when clearly helpful.
- If uncertain about categories, return an empty list.
- date_from is optional. If not implied, return null.

arXiv-style query syntax may use:
- ti:
- au:
- abs:
- cat:

Output requirements:
- Return valid JSON only.
- Do not wrap JSON in markdown.
- Do not add explanations.
- Top-level object must be:
  { "generated_queries": [...] }

- Return 3 or 5 query objects only.
- Each object must contain exactly:
  - "query": string
  - "categories": array of strings
  - "date_from": string or null

Examples of good behavior:
- Better to search:
  "abs:CPDLC OR abs:\\"controller pilot data link communications\\""
  than:
  "abs:CPDLC AND abs:\\"ground operations\\" AND abs:\\"communication\\""

- Better to search:
  "abs:\\"air traffic control\\" AND abs:communication"
  than:
  "abs:\\"controller pilot data link communications\\" AND abs:\\"ground handling\\""
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
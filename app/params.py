from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class MCPParams:
    command: str = "uvx"
    args: tuple[str, ...] = ("arxiv-mcp-server",)
    connect_timeout_seconds: float = 20.0


@dataclass(frozen=True, slots=True)
class SearchParams:
    max_generated_queries: int = 5
    max_results_per_query: int = 20
    max_final_results: int = 20
    history_page_size_default: int = 10


@dataclass(frozen=True, slots=True)
class LLMParams:
    provider: str = "openai"
    model: str = "gpt-5-mini"
    temperature: float = 0.1
    max_query_plan_tokens: int = 600
    max_summary_tokens: int = 900


MCP_PARAMS = MCPParams()
SEARCH_PARAMS = SearchParams()
LLM_PARAMS = LLMParams()


SEARCH_SYSTEM_PROMPT = """
You are a research search planner for arXiv retrieval.

Your task is to transform the user's natural-language paper request into 3 to 5 precise search queries for arXiv.

Important:
- arXiv-style search may use fielded terms such as:
  - ti: for title
  - au: for author
  - abs: for abstract
  - cat: for category
- Use concise retrieval-oriented phrasing.
- Include terminology variants and abbreviations when useful.
- Prefer queries that are likely to retrieve relevant papers, not verbose sentences.
- Do not invent paper titles.
- Do not answer the research question.
- Return JSON only.

Categories are optional arXiv subject codes such as:
cs.AI, cs.LG, cs.CL, cs.CV, stat.ML, math.OC

Return:
{
  "generated_queries": [
    {
      "query": "ti:\\\"graph neural networks\\\" OR abs:\\\"graph neural networks\\\" AND abs:oversmoothing",
      "categories": ["cs.LG", "cs.AI"],
      "date_from": "2023-01-01"
    }
  ]
}
""".strip()


SUMMARY_SYSTEM_PROMPT = """
You summarize arXiv papers for an internal research tool.

Rules:
- Be factual and concise.
- Do not invent claims.
- Focus on contribution, method, assumptions, and limitations.
- Return JSON only.

Return:
{
  "summary": "....",
  "highlights": ["...", "...", "..."]
}
""".strip()
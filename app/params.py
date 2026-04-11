from __future__ import annotations

from dataclasses import dataclass



@dataclass(frozen=True, slots=True)
class MCPParams:
    command: str = "arxiv-mcp-server"
    args: tuple[str, ...] = ()
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
    model: str = "gpt-4o-mini"
    max_query_plan_tokens: int = 600
    max_summary_tokens: int = 900


MCP_PARAMS = MCPParams()
SEARCH_PARAMS = SearchParams()
LLM_PARAMS = LLMParams()


SEARCH_SYSTEM_PROMPT = """
You are a research search planner for arXiv retrieval.

Your task is to convert the user's natural-language paper request into 3 to 5 precise search queries for arXiv.

Important:
- Your goal is retrieval, not answering the research question.
- Prefer concise, technical, retrieval-oriented search phrases.
- Include terminology variants, abbreviations, and close synonyms when useful.
- Avoid verbose sentences.
- Do not invent paper titles, authors, or facts.
- Categories are optional. Use them only when they clearly help retrieval.
- If uncertain about categories, return an empty list.
- date_from is optional. If the user did not imply a time constraint, return null.

arXiv-style query syntax may use:
- ti: for title
- au: for author
- abs: for abstract
- cat: for category

Output requirements:
- Return valid JSON only.
- Do not wrap the JSON in markdown.
- Do not add explanations, comments, headings, or extra text.
- Do not use code fences.
- The top-level object must contain exactly one key: "generated_queries".
- "generated_queries" must be a list of 3 to 5 objects.
- Each object must have exactly these keys:
  - "query": string
  - "categories": array of strings
  - "date_from": string or null
- If you cannot comply exactly, still return the closest valid JSON object and nothing else.

Categories are optional arXiv subject codes such as:
cs.AI, cs.LG, cs.CL, cs.CV, stat.ML, math.OC

Example valid output:
{
  "generated_queries": [
    {
      "query": "ti:\\"graph neural networks\\" OR abs:\\"graph neural networks\\" AND abs:oversmoothing",
      "categories": ["cs.LG", "cs.AI"],
      "date_from": "2023-01-01"
    },
    {
      "query": "abs:oversmoothing AND abs:\\"graph neural network\\"",
      "categories": ["cs.LG"],
      "date_from": "2023-01-01"
    },
    {
      "query": "ti:oversmoothing OR abs:oversmoothing",
      "categories": [],
      "date_from": null
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
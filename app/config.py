from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


@dataclass(slots=True)
class Config:
    host: str
    port: int
    debug: bool
    log_partial_results: bool
    history_file_path: Path
    max_search_results: int | None
    openai_api_key: str
    openai_model: str

    @classmethod
    def from_env(cls) -> "Config":
        app_dir = Path(__file__).resolve().parent
        storage_dir = app_dir / "storage"
        storage_dir.mkdir(parents=True, exist_ok=True)

        history_file_path = storage_dir / "history.json"
        if not history_file_path.exists():
            history_file_path.write_text("[]", encoding="utf-8")

        raw_max_search_results = os.getenv("APP_MAX_SEARCH_RESULTS", "").strip()
        max_search_results: int | None = None
        if raw_max_search_results:
            parsed_max_search_results = int(raw_max_search_results)
            max_search_results = (
                parsed_max_search_results if parsed_max_search_results > 0 else None
            )

        return cls(
            host=os.getenv("APP_HOST", "0.0.0.0"), # "127.0.0.1" if only local, i like to use it w my phone
            port=int(os.getenv("APP_PORT", "5000")),
            debug=os.getenv("APP_DEBUG", "true").strip().lower() == "true",
            log_partial_results=(
                os.getenv("APP_LOG_PARTIAL_RESULTS", "false").strip().lower() == "true"
            ),
            history_file_path=history_file_path,
            max_search_results=max_search_results,
            openai_api_key=os.getenv("OPENAI_API_KEY", ""),
            openai_model=os.getenv("OPENAI_MODEL", "gpt-5-mini"),
        )

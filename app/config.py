from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class Config:
    host: str
    port: int
    debug: bool
    history_file_path: Path
    max_search_results: int

    @classmethod
    def from_env(cls) -> "Config":
        app_dir = Path(__file__).resolve().parent
        storage_dir = app_dir / "storage"
        storage_dir.mkdir(parents=True, exist_ok=True)

        return cls(
            host=os.getenv("APP_HOST", "127.0.0.1"),
            port=int(os.getenv("APP_PORT", "5000")),
            debug=os.getenv("APP_DEBUG", "true").strip().lower() == "true",
            history_file_path=storage_dir / "history.json",
            max_search_results=20,
        )
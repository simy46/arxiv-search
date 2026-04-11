from __future__ import annotations

import json
import logging
import threading
from pathlib import Path

from app.core.logger import log_partial_result
from app.core.types import HistoryItem


class HistoryStore:
    def __init__(
        self,
        file_path: Path,
        logger: logging.Logger,
        log_partial_results: bool = False,
    ) -> None:
        self._file_path = file_path
        self._logger = logger
        self._log_partial_results = log_partial_results
        self._io_lock = threading.RLock()
        self._ensure_file()

    def load_all(self) -> list[HistoryItem]:
        with self._io_lock:
            self._logger.info("history_store.load_all")
            raw_items = self._read_json()
            items = [HistoryItem.from_dict(item) for item in raw_items]
            log_partial_result(
                self._logger,
                self._log_partial_results,
                "history_store.load_all loaded_count=%s",
                len(items),
            )
            return items

    def save_all(self, items: list[HistoryItem]) -> None:
        with self._io_lock:
            self._logger.info("history_store.save_all item_count=%s", len(items))
            payload = [item.to_dict() for item in items]
            log_partial_result(
                self._logger,
                self._log_partial_results,
                "history_store.save_all first_ids=%s",
                [item["history_id"] for item in payload[:3]],
            )
            self._write_json(payload)

    def _ensure_file(self) -> None:
        if not self._file_path.exists():
            self._file_path.parent.mkdir(parents=True, exist_ok=True)
            self._file_path.write_text("[]", encoding="utf-8")
            self._logger.info("history_store.ensure_file created path=%s", self._file_path)

    def _read_json(self) -> list[dict]:
        try:
            raw = self._file_path.read_text(encoding="utf-8").strip()
            if not raw:
                self._logger.info("history_store.read_json empty_file path=%s", self._file_path)
                return []
            data = json.loads(raw)
            return data if isinstance(data, list) else []
        except (json.JSONDecodeError, OSError):
            self._logger.exception("history_store.read_json failed path=%s", self._file_path)
            return []

    def _write_json(self, payload: list[dict]) -> None:
        self._file_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        self._logger.info("history_store.write_json saved path=%s", self._file_path)

from __future__ import annotations

import logging

from flask import Blueprint, jsonify, request

from app.core.logger import log_partial_result
from app.manager.arxiv_search_manager import ArxivSearchManager


def create_search_blueprint(
    search_manager: ArxivSearchManager,
    logger: logging.Logger,
    log_partial_results: bool = False,
) -> Blueprint:
    blueprint = Blueprint("search", __name__, url_prefix="/api/v1")

    @blueprint.post("/search")
    def search() -> tuple[object, int]:
        logger.info("route.search POST /api/v1/search")
        payload = request.get_json(silent=True) or {}
        log_partial_result(
            logger,
            log_partial_results,
            "route.search payload=%s",
            payload,
        )

        query = str(payload.get("query", "")).strip()
        categories_raw = payload.get("categories", [])
        date_from_raw = payload.get("date_from")

        if not query:
            logger.warning("route.search invalid_request missing_query")
            return jsonify(
                {
                    "error": {
                        "code": "INVALID_REQUEST",
                        "message": "query is required",
                        "details": {},
                    }
                }
            ), 400

        categories = categories_raw if isinstance(categories_raw, list) else []
        date_from = str(date_from_raw).strip() if date_from_raw else None

        result = search_manager.search(
            query=query,
            categories=categories,
            date_from=date_from,
        )
        logger.info(
            "route.search success history_id=%s returned_count=%s cache_hit=%s",
            result.history_id,
            result.returned_count,
            result.cache_hit,
        )

        return jsonify(result.to_dict()), 200

    return blueprint

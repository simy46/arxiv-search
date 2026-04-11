from __future__ import annotations

import logging

from flask import Blueprint, jsonify, request

from app.manager.history_manager import HistoryManager


def create_history_blueprint(
    history_manager: HistoryManager,
    logger: logging.Logger,
) -> Blueprint:
    blueprint = Blueprint("history", __name__, url_prefix="/api/v1/history")

    @blueprint.get("")
    def list_history() -> tuple[object, int]:
        logger.info("route.history_list GET /api/v1/history")
        page_raw = request.args.get("page", "1")
        page_size_raw = request.args.get("page_size", "10")

        try:
            page = int(page_raw)
            page_size = int(page_size_raw)
        except ValueError:
            logger.warning(
                "route.history_list invalid_request non_integer page=%r page_size=%r",
                page_raw,
                page_size_raw,
            )
            return jsonify(
                {
                    "error": {
                        "code": "INVALID_REQUEST",
                        "message": "page and page_size must be integers",
                        "details": {},
                    }
                }
            ), 400

        if page < 1 or page_size < 1:
            logger.warning(
                "route.history_list invalid_request non_positive page=%s page_size=%s",
                page,
                page_size,
            )
            return jsonify(
                {
                    "error": {
                        "code": "INVALID_REQUEST",
                        "message": "page and page_size must be positive",
                        "details": {},
                    }
                }
            ), 400

        response = history_manager.list_history(page=page, page_size=page_size)
        logger.info(
            "route.history_list success page=%s page_size=%s returned=%s",
            page,
            page_size,
            len(response.get("items", [])),
        )
        return jsonify(response), 200

    @blueprint.get("/<history_id>")
    def get_history_item(history_id: str) -> tuple[object, int]:
        logger.info("route.history_get GET /api/v1/history/%s", history_id)
        item = history_manager.get_history_item(history_id)

        if item is None:
            logger.warning("route.history_get not_found history_id=%s", history_id)
            return jsonify(
                {
                    "error": {
                        "code": "HISTORY_NOT_FOUND",
                        "message": "history item not found",
                        "details": {},
                    }
                }
            ), 404

        logger.info("route.history_get success history_id=%s", history_id)
        return jsonify(item.to_dict()), 200

    return blueprint

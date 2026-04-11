from __future__ import annotations

import logging

from flask import Blueprint, jsonify, request

from app.core.errors import ApiServiceError
from app.core.logger import log_partial_result
from app.manager.paper_manager import PaperManager


def create_paper_blueprint(
    paper_manager: PaperManager,
    logger: logging.Logger,
    log_partial_results: bool = False,
) -> Blueprint:
    blueprint = Blueprint("papers", __name__, url_prefix="/api/v1/papers")

    @blueprint.post("/download")
    def download() -> tuple[object, int]:
        logger.info("route.paper_download POST /api/v1/papers/download")
        payload = request.get_json(silent=True) or {}
        log_partial_result(
            logger,
            log_partial_results,
            "route.paper_download payload=%s",
            payload,
        )
        paper_id = str(payload.get("paper_id", "")).strip()

        if not paper_id:
            logger.warning("route.paper_download invalid_request missing_paper_id")
            return jsonify(
                {
                    "error": {
                        "code": "INVALID_REQUEST",
                        "message": "paper_id is required",
                        "details": {},
                    }
                }
            ), 400

        response = paper_manager.download_paper(paper_id)
        logger.info("route.paper_download success paper_id=%s", paper_id)
        return jsonify(response), 200

    @blueprint.post("/summarize")
    def summarize() -> tuple[object, int]:
        logger.info("route.paper_summarize POST /api/v1/papers/summarize")
        payload = request.get_json(silent=True) or {}
        log_partial_result(
            logger,
            log_partial_results,
            "route.paper_summarize payload=%s",
            payload,
        )

        history_id = str(payload.get("history_id", "")).strip()
        paper_id = str(payload.get("paper_id", "")).strip()
        style = str(payload.get("style", "brief")).strip() or "brief"

        if not history_id:
            logger.warning("route.paper_summarize invalid_request missing_history_id")
            return jsonify(
                {
                    "error": {
                        "code": "INVALID_REQUEST",
                        "message": "history_id is required",
                        "details": {},
                    }
                }
            ), 400

        if not paper_id:
            logger.warning("route.paper_summarize invalid_request missing_paper_id")
            return jsonify(
                {
                    "error": {
                        "code": "INVALID_REQUEST",
                        "message": "paper_id is required",
                        "details": {},
                    }
                }
            ), 400

        if style not in {"brief", "detailed"}:
            logger.warning("route.paper_summarize invalid_request invalid_style=%s", style)
            return jsonify(
                {
                    "error": {
                        "code": "INVALID_REQUEST",
                        "message": "style must be 'brief' or 'detailed'",
                        "details": {},
                    }
                }
            ), 400

        try:
            response = paper_manager.summarize_paper(
                history_id=history_id,
                paper_id=paper_id,
                style=style,
            )
            logger.info(
                "route.paper_summarize success history_id=%s paper_id=%s",
                history_id,
                paper_id,
            )
            return jsonify(response), 200
        except ApiServiceError as exc:
            logger.exception(
                "route.paper_summarize service_error code=%s history_id=%s paper_id=%s",
                exc.code,
                history_id,
                paper_id,
            )
            return jsonify(
                {
                    "error": {
                        "code": exc.code,
                        "message": exc.message,
                        "details": exc.details,
                    }
                }
            ), exc.status_code
        except Exception as exc:
            logger.exception(
                "route.paper_summarize unexpected_error history_id=%s paper_id=%s",
                history_id,
                paper_id,
            )
            return jsonify(
                {
                    "error": {
                        "code": "SUMMARY_FAILED",
                        "message": str(exc) or "Summary failed",
                        "details": {},
                    }
                }
            ), 500

    return blueprint

from __future__ import annotations

import logging

from flask import Blueprint, jsonify


def create_health_blueprint(logger: logging.Logger) -> Blueprint:
    blueprint = Blueprint("health", __name__, url_prefix="/api/v1")

    @blueprint.get("/health")
    def health() -> tuple[object, int]:
        logger.info("route.health GET /api/v1/health")
        return jsonify(
            {
                "status": "ok",
                "service": "arxiv-lab-tool",
                "mcp": "configured by simy46_ looool",
            }
        ), 200

    return blueprint

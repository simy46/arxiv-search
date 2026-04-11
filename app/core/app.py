from __future__ import annotations

from flask import Flask

from app.config import Config
from app.core.logger import build_logger
from app.services.history_store import HistoryStore
from app.manager.history_manager import HistoryManager
from app.adapters.llm_client import LLMClient
from app.adapters.mcp_arxiv_client import MCPArxivClient
from app.services.llm_search_orchestrator import LLMSearchOrchestrator
from app.services.reranker import Reranker
from app.manager.arxiv_search_manager import ArxivSearchManager
from app.manager.paper_manager import PaperManager
from app.routes.health_routes import create_health_blueprint
from app.routes.search_routes import create_search_blueprint
from app.routes.paper_routes import create_paper_blueprint
from app.routes.history_routes import create_history_blueprint


class App:
    def __init__(self) -> None:
        self.config = Config.from_env()
        self.logger = build_logger("arxiv-search", self.config.debug)
        self.logger.info(
            "app.init debug=%s log_partial_results=%s",
            self.config.debug,
            self.config.log_partial_results,
        )

        self.flask_app = Flask(__name__)
        self.flask_app.config["JSON_SORT_KEYS"] = False

        self.history_store = HistoryStore(
            self.config.history_file_path,
            logger=self.logger.getChild("history_store"),
            log_partial_results=self.config.log_partial_results,
        )
        self.history_manager = HistoryManager(
            self.history_store,
            logger=self.logger.getChild("history_manager"),
            log_partial_results=self.config.log_partial_results,
        )

        self.llm_client = LLMClient(
            logger=self.logger.getChild("llm_client"),
            log_partial_results=self.config.log_partial_results,
        )
        self.mcp_arxiv_client = MCPArxivClient(
            logger=self.logger.getChild("mcp_client"),
            log_partial_results=self.config.log_partial_results,
        )

        self.llm_search_orchestrator = LLMSearchOrchestrator(
            self.llm_client,
            logger=self.logger.getChild("orchestrator"),
            log_partial_results=self.config.log_partial_results,
        )
        self.reranker = Reranker(
            logger=self.logger.getChild("reranker"),
            log_partial_results=self.config.log_partial_results,
        )

        self.arxiv_search_manager = ArxivSearchManager(
            history_manager=self.history_manager,
            llm_search_orchestrator=self.llm_search_orchestrator,
            reranker=self.reranker,
            mcp_arxiv_client=self.mcp_arxiv_client,
            logger=self.logger.getChild("search_manager"),
            log_partial_results=self.config.log_partial_results,
            max_results=self.config.max_search_results,
        )

        self.paper_manager = PaperManager(
            history_manager=self.history_manager,
            llm_client=self.llm_client,
            mcp_arxiv_client=self.mcp_arxiv_client,
            logger=self.logger.getChild("paper_manager"),
            log_partial_results=self.config.log_partial_results,
        )

        self._register_blueprints()

    def _register_blueprints(self) -> None:
        self.flask_app.register_blueprint(
            create_health_blueprint(self.logger.getChild("route.health"))
        )
        self.flask_app.register_blueprint(
            create_search_blueprint(
                self.arxiv_search_manager,
                logger=self.logger.getChild("route.search"),
                log_partial_results=self.config.log_partial_results,
            )
        )
        self.flask_app.register_blueprint(
            create_paper_blueprint(
                self.paper_manager,
                logger=self.logger.getChild("route.paper"),
                log_partial_results=self.config.log_partial_results,
            )
        )
        self.flask_app.register_blueprint(
            create_history_blueprint(
                self.history_manager,
                logger=self.logger.getChild("route.history"),
            )
        )

    def run(self) -> None:
        self.logger.info(
            "Starting Flask app on %s:%s",
            self.config.host,
            self.config.port,
        )
        self.flask_app.run(
            host=self.config.host,
            port=self.config.port,
            debug=self.config.debug,
        )

"""REST API route definitions for comfy-cli REST API."""

from aiohttp import web
import logging

from .api.handlers.config import ConfigHandler
from .api.handlers.models import ModelHandler
from .api.handlers.comfy_nodes import NodeHandler
from .handlers.models import ModelHandler
from .handlers.nodes import NodeHandler
from .comfy_cli import ComfyCliExecutor

logger = logging.getLogger(__name__)


def setup_comfy_cli_routes(app: web.Application, executor: ComfyCliExecutor) -> None:
    """
    Register comfy-cli REST API routes with the aiohttp application.

    Args:
        app: aiohttp web application
        executor: ComfyCliExecutor instance
    """
    config_handler = ConfigHandler(executor)
    model_handler = ModelHandler(executor)
    node_handler = NodeHandler(executor)

    # Configuration endpoints
    app.router.add_get("/comfy-cli/config/env", config_handler.get_env)
    app.router.add_get("/comfy-cli/config/which", config_handler.get_which)
    app.router.add_post("/comfy-cli/config/set-default", config_handler.set_default)

    # Model management endpoints
    app.router.add_get("/comfy-cli/model/list", model_handler.list_models)
    app.router.add_post("/comfy-cli/model/download", model_handler.download_model)
    app.router.add_get(
        "/comfy-cli/model/download/{job_id}/status", model_handler.get_download_status
    )
    app.router.add_post("/comfy-cli/model/remove", model_handler.remove_model)

    # Node management endpoints
    app.router.add_get("/comfy-cli/node/simple-show", node_handler.simple_show)
    app.router.add_get("/comfy-cli/node/show", node_handler.show)
    app.router.add_post("/comfy-cli/node/install", node_handler.install_node)
    app.router.add_post("/comfy-cli/node/update", node_handler.update_node)
    app.router.add_post("/comfy-cli/node/enable", node_handler.enable_node)
    app.router.add_post("/comfy-cli/node/disable", node_handler.disable_node)
    app.router.add_post("/comfy-cli/node/uninstall", node_handler.uninstall_node)

    logger.info("comfy-cli REST API routes registered")

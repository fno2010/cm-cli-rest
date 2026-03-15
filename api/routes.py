"""REST API route definitions for cm-cli-rest."""

from aiohttp import web
import logging

from .handlers.nodes import NodesHandler
from .handlers.snapshots import SnapshotsHandler
from .handlers.jobs import JobsHandler
from ..cm_cli import CMCLIExecutor

logger = logging.getLogger(__name__)


def setup_routes(app: web.Application, executor: CMCLIExecutor) -> None:
    """
    Register all REST API routes with the aiohttp application.
    
    Args:
        app: aiohttp web application (PromptServer.instance.app)
        executor: CMCLIExecutor instance for command execution
    """
    # Initialize handlers
    nodes_handler = NodesHandler(executor)
    snapshots_handler = SnapshotsHandler(executor)
    jobs_handler = JobsHandler(executor)

    # Health check endpoint
    app.router.add_get("/cm-cli-rest/health", health_check)

    # Node management endpoints
    app.router.add_get("/cm-cli-rest/nodes", nodes_handler.list_nodes)
    app.router.add_get("/cm-cli-rest/nodes/{name}", nodes_handler.get_node)
    app.router.add_post("/cm-cli-rest/nodes/install", nodes_handler.install_node)
    app.router.add_post("/cm-cli-rest/nodes/uninstall", nodes_handler.uninstall_node)
    app.router.add_post("/cm-cli-rest/nodes/update", nodes_handler.update_node)
    app.router.add_post("/cm-cli-rest/nodes/update-all", nodes_handler.update_all_nodes)
    app.router.add_post("/cm-cli-rest/nodes/enable", nodes_handler.enable_node)
    app.router.add_post("/cm-cli-rest/nodes/disable", nodes_handler.disable_node)
    app.router.add_post("/cm-cli-rest/nodes/fix", nodes_handler.fix_node)
    app.router.add_post("/cm-cli-rest/nodes/reinstall", nodes_handler.reinstall_node)

    # Snapshot endpoints
    app.router.add_post("/cm-cli-rest/snapshots/save", snapshots_handler.save_snapshot)
    app.router.add_post("/cm-cli-rest/snapshots/restore", snapshots_handler.restore_snapshot)
    app.router.add_get("/cm-cli-rest/snapshots", snapshots_handler.list_snapshots)

    # Job tracking endpoints
    app.router.add_get("/cm-cli-rest/jobs", jobs_handler.list_jobs)
    app.router.add_get("/cm-cli-rest/jobs/{id}", jobs_handler.get_job)
    app.router.add_delete("/cm-cli-rest/jobs/{id}", jobs_handler.cleanup_job)

    logger.info("cm-cli-rest API routes registered")


async def health_check(request: web.Request) -> web.Response:
    """
    GET /cm-cli-rest/health
    
    Health check endpoint.
    """
    from datetime import datetime
    
    return web.json_response(
        {
            "status": "healthy",
            "service": "cm-cli-rest",
            "version": "0.1.0",
            "timestamp": datetime.now().isoformat(),
        }
    )

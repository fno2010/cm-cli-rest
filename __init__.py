"""
cm-cli-rest: REST API for ComfyUI-Manager CLI

A ComfyUI custom node that exposes REST API endpoints for managing
custom nodes via cm-cli (ComfyUI-Manager CLI).

Usage:
    Install this in ComfyUI/custom_nodes/cm-cli-rest/
    Restart ComfyUI
    API endpoints available at: http://localhost:8188/cm-cli-rest/*
"""

from server import PromptServer
import logging

from .cm_cli import CMCLIExecutor
from .api.routes import setup_routes

logger = logging.getLogger(__name__)

# Initialize cm-cli executor
# Auto-detects cm-cli.py from ComfyUI-Manager installation
executor = CMCLIExecutor()

# Register API routes with ComfyUI's built-in server
# This integrates our REST API into ComfyUI's aiohttp server
setup_routes(PromptServer.instance.app, executor)

logger.info("cm-cli-rest initialized - REST API available at /cm-cli-rest/*")


# Optional: ComfyUI workflow node for triggering API calls
# This allows using the API from within ComfyUI workflows
class CMCLIRestNode:
    """
    ComfyUI node for triggering cm-cli REST API calls.

    This is optional - the REST API works independently.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "endpoint": (["health", "list_nodes", "update_all"], {
                    "default": "health"
                }),
                "trigger": ("BOOLEAN", {"default": False}),
            },
            "optional": {
                "node_name": ("STRING", {"default": ""}),
            }
        }

    RETURN_TYPES = ("STRING", "BOOLEAN")
    RETURN_NAMES = ("response", "success")
    CATEGORY = "utils/cm-cli-rest"
    FUNCTION = "execute"

    def execute(self, endpoint: str, trigger: bool, node_name: str = ""):
        """
        Execute API call (synchronous, for simple endpoints only).

        Note: For complex operations (install, update), use the REST API directly.
        This node is mainly for health checks and simple queries.
        """
        if not trigger:
            return ("", False)

        # For actual implementation, you would make HTTP requests to the API
        # This is a placeholder - in practice, use the REST API directly
        return (f"Use REST API at /cm-cli-rest/{endpoint}", True)


# Node registration (optional - the REST API is the main feature)
NODE_CLASS_MAPPINGS = {
    "CMCLIRest": CMCLIRestNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "CMCLIRest": "cm-cli REST API",
}

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]

"""Handler for /cm-cli-rest/nodes/* endpoints."""

from aiohttp import web
from typing import Dict, Any
import logging

from ...cm_cli import CMCLIExecutor, CMCLIError

logger = logging.getLogger(__name__)


class NodesHandler:
    """Handles node management REST API endpoints."""

    def __init__(self, executor: CMCLIExecutor):
        self.executor = executor

    async def list_nodes(self, request: web.Request) -> web.Response:
        """
        GET /cm-cli-rest/nodes
        
        List all installed custom nodes.
        """
        try:
            result = await self.executor.execute(["show", "installed"])
            
            if not result["success"]:
                return web.json_response(
                    {
                        "success": False,
                        "error": {
                            "code": "CM_CLI_ERROR",
                            "message": "Failed to list nodes",
                            "details": result["stderr"],
                        }
                    },
                    status=500,
                )

            nodes = await self.executor.parse_installed_nodes(result["stdout"])
            
            return web.json_response(
                {
                    "success": True,
                    "data": {
                        "nodes": nodes,
                        "total": len(nodes),
                    }
                }
            )

        except CMCLIError as e:
            logger.error(f"Error listing nodes: {e}")
            return web.json_response(
                {
                    "success": False,
                    "error": {
                        "code": "CM_CLI_ERROR",
                        "message": e.message,
                        "details": str(e),
                    }
                },
                status=500,
            )

    async def get_node(self, request: web.Request) -> web.Response:
        """
        GET /cm-cli-rest/nodes/:name
        
        Get details for a specific node.
        """
        node_name = request.match_info.get("name")
        
        if not node_name:
            return web.json_response(
                {
                    "success": False,
                    "error": {
                        "code": "INVALID_REQUEST",
                        "message": "Node name is required",
                    }
                },
                status=400,
            )

        try:
            result = await self.executor.execute(["show", "installed"])
            
            if not result["success"]:
                return web.json_response(
                    {
                        "success": False,
                        "error": {
                            "code": "CM_CLI_ERROR",
                            "message": "Failed to list nodes",
                        }
                    },
                    status=500,
                )

            nodes = await self.executor.parse_installed_nodes(result["stdout"])
            node = next((n for n in nodes if n["name"].lower() == node_name.lower()), None)

            if not node:
                return web.json_response(
                    {
                        "success": False,
                        "error": {
                            "code": "NODE_NOT_FOUND",
                            "message": f"Node '{node_name}' not found",
                        }
                    },
                    status=404,
                )

            return web.json_response(
                {
                    "success": True,
                    "data": {"node": node},
                }
            )

        except CMCLIError as e:
            logger.error(f"Error getting node: {e}")
            return web.json_response(
                {
                    "success": False,
                    "error": {
                        "code": "CM_CLI_ERROR",
                        "message": e.message,
                    }
                },
                status=500,
            )

    async def install_node(self, request: web.Request) -> web.Response:
        """
        POST /cm-cli-rest/nodes/install
        
        Install a custom node (async operation).
        
        Request body:
        {
            "name": "ComfyUI-Impact-Pack",
            "channel": "recent",  # optional
            "mode": "remote"       # optional
        }
        """
        try:
            body = await request.json()
        except Exception:
            return web.json_response(
                {
                    "success": False,
                    "error": {
                        "code": "INVALID_REQUEST",
                        "message": "Invalid JSON body",
                    }
                },
                status=400,
            )

        node_name = body.get("name")
        if not node_name:
            return web.json_response(
                {
                    "success": False,
                    "error": {
                        "code": "INVALID_REQUEST",
                        "message": "Node 'name' is required",
                    }
                },
                status=400,
            )

        # Build command
        command = ["install", node_name]
        
        if body.get("channel"):
            command.extend(["--channel", body["channel"]])
        
        if body.get("mode"):
            command.extend(["--mode", body["mode"]])

        try:
            # Execute asynchronously
            job = await self.executor.execute_async(command, timeout=300)
            
            return web.json_response(
                {
                    "success": True,
                    "data": {
                        "job_id": job.job_id,
                        "status": job.status.value,
                        "message": f"Installation started for '{node_name}'",
                    }
                },
                status=202,  # Accepted
            )

        except CMCLIError as e:
            logger.error(f"Error installing node: {e}")
            return web.json_response(
                {
                    "success": False,
                    "error": {
                        "code": "INSTALL_FAILED",
                        "message": e.message,
                    }
                },
                status=500,
            )

    async def uninstall_node(self, request: web.Request) -> web.Response:
        """
        POST /cm-cli-rest/nodes/uninstall
        
        Uninstall a custom node.
        """
        try:
            body = await request.json()
        except Exception:
            return web.json_response(
                {
                    "success": False,
                    "error": {
                        "code": "INVALID_REQUEST",
                        "message": "Invalid JSON body",
                    }
                },
                status=400,
            )

        node_name = body.get("name")
        if not node_name:
            return web.json_response(
                {
                    "success": False,
                    "error": {
                        "code": "INVALID_REQUEST",
                        "message": "Node 'name' is required",
                    }
                },
                status=400,
            )

        try:
            result = await self.executor.execute(["uninstall", node_name])
            
            if result["success"]:
                return web.json_response(
                    {
                        "success": True,
                        "data": {
                            "message": f"Node '{node_name}' uninstalled successfully",
                        }
                    }
                )
            else:
                return web.json_response(
                    {
                        "success": False,
                        "error": {
                            "code": "UNINSTALL_FAILED",
                            "message": "Failed to uninstall node",
                            "details": result["stderr"],
                        }
                    },
                    status=500,
                )

        except CMCLIError as e:
            logger.error(f"Error uninstalling node: {e}")
            return web.json_response(
                {
                    "success": False,
                    "error": {
                        "code": "UNINSTALL_FAILED",
                        "message": e.message,
                    }
                },
                status=500,
            )

    async def update_node(self, request: web.Request) -> web.Response:
        """
        POST /cm-cli-rest/nodes/update
        
        Update a custom node (async operation).
        """
        try:
            body = await request.json()
        except Exception:
            return web.json_response(
                {
                    "success": False,
                    "error": {
                        "code": "INVALID_REQUEST",
                        "message": "Invalid JSON body",
                    }
                },
                status=400,
            )

        node_name = body.get("name")
        if not node_name:
            return web.json_response(
                {
                    "success": False,
                    "error": {
                        "code": "INVALID_REQUEST",
                        "message": "Node 'name' is required",
                    }
                },
                status=400,
            )

        try:
            job = await self.executor.execute_async(["update", node_name], timeout=300)
            
            return web.json_response(
                {
                    "success": True,
                    "data": {
                        "job_id": job.job_id,
                        "status": job.status.value,
                        "message": f"Update started for '{node_name}'",
                    }
                },
                status=202,
            )

        except CMCLIError as e:
            logger.error(f"Error updating node: {e}")
            return web.json_response(
                {
                    "success": False,
                    "error": {
                        "code": "UPDATE_FAILED",
                        "message": e.message,
                    }
                },
                status=500,
            )

    async def update_all_nodes(self, request: web.Request) -> web.Response:
        """
        POST /cm-cli-rest/nodes/update-all
        
        Update all custom nodes (async operation).
        """
        try:
            job = await self.executor.execute_async(["update", "all"], timeout=600)
            
            return web.json_response(
                {
                    "success": True,
                    "data": {
                        "job_id": job.job_id,
                        "status": job.status.value,
                        "message": "Update all nodes started",
                    }
                },
                status=202,
            )

        except CMCLIError as e:
            logger.error(f"Error updating all nodes: {e}")
            return web.json_response(
                {
                    "success": False,
                    "error": {
                        "code": "UPDATE_FAILED",
                        "message": e.message,
                    }
                },
                status=500,
            )

    async def enable_node(self, request: web.Request) -> web.Response:
        """
        POST /cm-cli-rest/nodes/enable
        
        Enable a disabled custom node.
        """
        try:
            body = await request.json()
        except Exception:
            return web.json_response(
                {
                    "success": False,
                    "error": {
                        "code": "INVALID_REQUEST",
                        "message": "Invalid JSON body",
                    }
                },
                status=400,
            )

        node_name = body.get("name")
        if not node_name:
            return web.json_response(
                {
                    "success": False,
                    "error": {
                        "code": "INVALID_REQUEST",
                        "message": "Node 'name' is required",
                    }
                },
                status=400,
            )

        try:
            result = await self.executor.execute(["enable", node_name])
            
            if result["success"]:
                return web.json_response(
                    {
                        "success": True,
                        "data": {
                            "message": f"Node '{node_name}' enabled successfully",
                        }
                    }
                )
            else:
                return web.json_response(
                    {
                        "success": False,
                        "error": {
                            "code": "ENABLE_FAILED",
                            "message": "Failed to enable node",
                            "details": result["stderr"],
                        }
                    },
                    status=500,
                )

        except CMCLIError as e:
            logger.error(f"Error enabling node: {e}")
            return web.json_response(
                {
                    "success": False,
                    "error": {
                        "code": "ENABLE_FAILED",
                        "message": e.message,
                    }
                },
                status=500,
            )

    async def disable_node(self, request: web.Request) -> web.Response:
        """
        POST /cm-cli-rest/nodes/disable
        
        Disable a custom node.
        """
        try:
            body = await request.json()
        except Exception:
            return web.json_response(
                {
                    "success": False,
                    "error": {
                        "code": "INVALID_REQUEST",
                        "message": "Invalid JSON body",
                    }
                },
                status=400,
            )

        node_name = body.get("name")
        if not node_name:
            return web.json_response(
                {
                    "success": False,
                    "error": {
                        "code": "INVALID_REQUEST",
                        "message": "Node 'name' is required",
                    }
                },
                status=400,
            )

        try:
            result = await self.executor.execute(["disable", node_name])
            
            if result["success"]:
                return web.json_response(
                    {
                        "success": True,
                        "data": {
                            "message": f"Node '{node_name}' disabled successfully",
                        }
                    }
                )
            else:
                return web.json_response(
                    {
                        "success": False,
                        "error": {
                            "code": "DISABLE_FAILED",
                            "message": "Failed to disable node",
                            "details": result["stderr"],
                        }
                    },
                    status=500,
                )

        except CMCLIError as e:
            logger.error(f"Error disabling node: {e}")
            return web.json_response(
                {
                    "success": False,
                    "error": {
                        "code": "DISABLE_FAILED",
                        "message": e.message,
                    }
                },
                status=500,
            )

    async def fix_node(self, request: web.Request) -> web.Response:
        """
        POST /cm-cli-rest/nodes/fix
        
        Fix a custom node's dependencies.
        """
        try:
            body = await request.json()
        except Exception:
            return web.json_response(
                {
                    "success": False,
                    "error": {
                        "code": "INVALID_REQUEST",
                        "message": "Invalid JSON body",
                    }
                },
                status=400,
            )

        node_name = body.get("name")
        if not node_name:
            return web.json_response(
                {
                    "success": False,
                    "error": {
                        "code": "INVALID_REQUEST",
                        "message": "Node 'name' is required",
                    }
                },
                status=400,
            )

        try:
            job = await self.executor.execute_async(["fix", node_name], timeout=300)
            
            return web.json_response(
                {
                    "success": True,
                    "data": {
                        "job_id": job.job_id,
                        "status": job.status.value,
                        "message": f"Fix started for '{node_name}'",
                    }
                },
                status=202,
            )

        except CMCLIError as e:
            logger.error(f"Error fixing node: {e}")
            return web.json_response(
                {
                    "success": False,
                    "error": {
                        "code": "FIX_FAILED",
                        "message": e.message,
                    }
                },
                status=500,
            )

    async def reinstall_node(self, request: web.Request) -> web.Response:
        """
        POST /cm-cli-rest/nodes/reinstall
        
        Reinstall a custom node (async operation).
        """
        try:
            body = await request.json()
        except Exception:
            return web.json_response(
                {
                    "success": False,
                    "error": {
                        "code": "INVALID_REQUEST",
                        "message": "Invalid JSON body",
                    }
                },
                status=400,
            )

        node_name = body.get("name")
        if not node_name:
            return web.json_response(
                {
                    "success": False,
                    "error": {
                        "code": "INVALID_REQUEST",
                        "message": "Node 'name' is required",
                    }
                },
                status=400,
            )

        try:
            job = await self.executor.execute_async(["reinstall", node_name], timeout=300)
            
            return web.json_response(
                {
                    "success": True,
                    "data": {
                        "job_id": job.job_id,
                        "status": job.status.value,
                        "message": f"Reinstallation started for '{node_name}'",
                    }
                },
                status=202,
            )

        except CMCLIError as e:
            logger.error(f"Error reinstalling node: {e}")
            return web.json_response(
                {
                    "success": False,
                    "error": {
                        "code": "REINSTALL_FAILED",
                        "message": e.message,
                    }
                },
                status=500,
            )

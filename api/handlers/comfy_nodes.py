"""
Node management API handler for comfy-cli.

Handles:
- GET /comfy-cli/node/simple-show
- GET /comfy-cli/node/show
- POST /comfy-cli/node/install
- POST /comfy-cli/node/update
- POST /comfy-cli/node/enable
- POST /comfy-cli/node/disable
- POST /comfy-cli/node/uninstall
"""

from aiohttp import web
import logging
from typing import Any, Dict, List
from ...comfy_cli.executor import ComfyCliExecutor, ComfyCLIError, JobStatus

logger = logging.getLogger(__name__)


class NodeHandler:
    """Handler for comfy-cli node management endpoints."""

    def __init__(self, executor: ComfyCliExecutor):
        self.executor = executor

    async def simple_show(self, request: web.Request) -> web.Response:
        """GET /comfy-cli/node/simple-show?mode=installed"""
        mode = request.query.get("mode", "installed")
        valid_modes = ["installed", "enabled", "disabled", "not-installed", "all"]

        if mode not in valid_modes:
            return web.json_response(
                {
                    "success": False,
                    "error": {
                        "code": "INVALID_PARAMETER",
                        "message": f"mode must be one of: {', '.join(valid_modes)}",
                    },
                },
                status=400,
            )

        try:
            result = await self.executor.execute(
                ["node", "simple-show", mode], timeout=60
            )

            if not result["success"]:
                return web.json_response(
                    {
                        "success": False,
                        "error": {
                            "code": "COMMAND_FAILED",
                            "message": result["stderr"] or "Failed to list nodes",
                        },
                    },
                    status=500,
                )

            node_names = self.executor.parse_list_output(result["stdout"])

            return web.json_response(
                {
                    "success": True,
                    "data": {
                        "mode": mode,
                        "nodes": node_names,
                        "total_count": len(node_names),
                    },
                    "raw_output": result["stdout"],
                }
            )

        except ComfyCLIError as e:
            logger.error(f"simple_show failed: {e}")
            return web.json_response(
                {"success": False, "error": {"code": "COMFY_CLI_ERROR", "message": e.message}},
                status=500,
            )
        except Exception as e:
            logger.exception(f"simple_show failed: {e}")
            return web.json_response(
                {"success": False, "error": {"code": "INTERNAL_ERROR", "message": str(e)}},
                status=500,
            )

    async def show(self, request: web.Request) -> web.Response:
        """GET /comfy-cli/node/show?mode=installed"""
        mode = request.query.get("mode", "installed")
        valid_modes = ["installed", "enabled", "disabled", "all"]

        if mode not in valid_modes:
            return web.json_response(
                {
                    "success": False,
                    "error": {
                        "code": "INVALID_PARAMETER",
                        "message": f"mode must be one of: {', '.join(valid_modes)}",
                    },
                },
                status=400,
            )

        try:
            result = await self.executor.execute(["node", "show", mode], timeout=60)

            if not result["success"]:
                return web.json_response(
                    {
                        "success": False,
                        "error": {
                            "code": "COMMAND_FAILED",
                            "message": result["stderr"] or "Failed to show nodes",
                        },
                    },
                    status=500,
                )

            nodes = self._parse_node_show_output(result["stdout"])

            return web.json_response(
                {
                    "success": True,
                    "data": {"mode": mode, "nodes": nodes, "total_count": len(nodes)},
                    "raw_output": result["stdout"],
                }
            )

        except Exception as e:
            logger.exception(f"show failed: {e}")
            return web.json_response(
                {"success": False, "error": {"code": "INTERNAL_ERROR", "message": str(e)}},
                status=500,
            )

    def _parse_node_show_output(self, raw_output: str) -> List[Dict[str, Any]]:
        """Parse detailed node show output."""
        nodes = []
        current_node = {}

        for line in raw_output.strip().split("\n"):
            line = line.strip()
            if not line:
                if current_node:
                    nodes.append(current_node)
                    current_node = {}
                continue

            if line.startswith("Node:"):
                if current_node:
                    nodes.append(current_node)
                current_node = {"name": line.replace("Node:", "").strip()}
            elif ":" in line and current_node:
                key, value = line.split(":", 1)
                key = key.strip().lower().replace(" ", "_")
                value = value.strip()

                if key == "requirements":
                    if value == "-":
                        current_node[key] = []
                    else:
                        current_node[key] = [r.strip() for r in value.split(",")]
                else:
                    current_node[key] = value

        if current_node:
            nodes.append(current_node)

        return nodes

    async def install_node(self, request: web.Request) -> web.Response:
        """POST /comfy-cli/node/install (async)"""
        try:
            data = await request.json()
            nodes = data.get("nodes", [])

            if not nodes:
                return web.json_response(
                    {
                        "success": False,
                        "error": {"code": "MISSING_PARAMETER", "message": "nodes is required"},
                    },
                    status=400,
                )

            args = ["node", "install"] + nodes

            if data.get("fast_deps"):
                args.append("--fast-deps")
            if data.get("no_deps"):
                args.append("--no-deps")
            if data.get("channel"):
                args.extend(["--channel", data["channel"]])

            job = await self.executor.execute_async(args, timeout=300)

            return web.json_response(
                {
                    "success": True,
                    "job_id": job.job_id,
                    "status": job.status.value,
                    "message": f"Installing {len(nodes)} node(s)",
                    "data": {"nodes": nodes},
                },
                status=202,
            )

        except Exception as e:
            logger.exception(f"install_node failed: {e}")
            return web.json_response(
                {"success": False, "error": {"code": "INTERNAL_ERROR", "message": str(e)}},
                status=500,
            )

    async def update_node(self, request: web.Request) -> web.Response:
        """POST /comfy-cli/node/update (async)"""
        try:
            data = await request.json()
            target = data.get("target", "all")

            args = ["node", "update", target]

            if data.get("channel"):
                args.extend(["--channel", data["channel"]])
            if data.get("mode"):
                args.extend(["--mode", data["mode"]])

            job = await self.executor.execute_async(args, timeout=300)

            return web.json_response(
                {
                    "success": True,
                    "job_id": job.job_id,
                    "status": job.status.value,
                    "message": "Updating nodes",
                    "data": {"target": target},
                },
                status=202,
            )

        except Exception as e:
            logger.exception(f"update_node failed: {e}")
            return web.json_response(
                {"success": False, "error": {"code": "INTERNAL_ERROR", "message": str(e)}},
                status=500,
            )

    async def enable_node(self, request: web.Request) -> web.Response:
        """POST /comfy-cli/node/enable"""
        try:
            data = await request.json()
            node = data.get("node")

            if not node:
                return web.json_response(
                    {"success": False, "error": {"code": "MISSING_PARAMETER", "message": "node is required"}},
                    status=400,
                )

            result = await self.executor.execute(["node", "enable", node], timeout=60)

            if not result["success"]:
                return web.json_response(
                    {
                        "success": False,
                        "error": {"code": "COMMAND_FAILED", "message": result["stderr"] or "Failed to enable node"},
                    },
                    status=500,
                )

            return web.json_response(
                {"success": True, "data": {"node": node, "action": "enabled"}, "raw_output": result["stdout"]}
            )

        except Exception as e:
            logger.exception(f"enable_node failed: {e}")
            return web.json_response(
                {"success": False, "error": {"code": "INTERNAL_ERROR", "message": str(e)}},
                status=500,
            )

    async def disable_node(self, request: web.Request) -> web.Response:
        """POST /comfy-cli/node/disable"""
        try:
            data = await request.json()
            node = data.get("node")

            if not node:
                return web.json_response(
                    {"success": False, "error": {"code": "MISSING_PARAMETER", "message": "node is required"}},
                    status=400,
                )

            result = await self.executor.execute(["node", "disable", node], timeout=60)

            if not result["success"]:
                return web.json_response(
                    {
                        "success": False,
                        "error": {"code": "COMMAND_FAILED", "message": result["stderr"] or "Failed to disable node"},
                    },
                    status=500,
                )

            return web.json_response(
                {"success": True, "data": {"node": node, "action": "disabled"}, "raw_output": result["stdout"]}
            )

        except Exception as e:
            logger.exception(f"disable_node failed: {e}")
            return web.json_response(
                {"success": False, "error": {"code": "INTERNAL_ERROR", "message": str(e)}},
                status=500,
            )

    async def uninstall_node(self, request: web.Request) -> web.Response:
        """POST /comfy-cli/node/uninstall"""
        try:
            data = await request.json()
            node = data.get("node")

            if not node:
                return web.json_response(
                    {"success": False, "error": {"code": "MISSING_PARAMETER", "message": "node is required"}},
                    status=400,
                )

            args = ["node", "uninstall", node]
            if data.get("confirm"):
                args.append("--confirm")

            result = await self.executor.execute(args, timeout=60)

            if not result["success"]:
                return web.json_response(
                    {
                        "success": False,
                        "error": {"code": "COMMAND_FAILED", "message": result["stderr"] or "Failed to uninstall node"},
                    },
                    status=500,
                )

            return web.json_response(
                {"success": True, "data": {"node": node, "action": "uninstalled"}, "raw_output": result["stdout"]}
            )

        except Exception as e:
            logger.exception(f"uninstall_node failed: {e}")
            return web.json_response(
                {"success": False, "error": {"code": "INTERNAL_ERROR", "message": str(e)}},
                status=500,
            )

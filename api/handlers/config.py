"""
Configuration API handler for comfy-cli.

Handles:
- GET /comfy-cli/config/env
- GET /comfy-cli/config/which
- POST /comfy-cli/config/set-default
"""

from aiohttp import web
import logging
from pathlib import Path
from ...comfy_cli.executor import ComfyCliExecutor, ComfyCLIError

logger = logging.getLogger(__name__)


class ConfigHandler:
    """Handler for comfy-cli configuration endpoints."""

    def __init__(self, executor: ComfyCliExecutor):
        self.executor = executor

    async def get_env(self, request: web.Request) -> web.Response:
        """GET /comfy-cli/config/env"""
        try:
            result = await self.executor.execute(["env"], timeout=30)

            if not result["success"]:
                return web.json_response(
                    {
                        "success": False,
                        "error": {"code": "COMMAND_FAILED", "message": result["stderr"] or "Failed to get environment"},
                    },
                    status=500,
                )

            env_data = self.executor.parse_env_output(result["stdout"])

            return web.json_response(
                {"success": True, "data": env_data, "raw_output": result["stdout"]}
            )

        except Exception as e:
            logger.exception(f"get_env failed: {e}")
            return web.json_response(
                {"success": False, "error": {"code": "INTERNAL_ERROR", "message": str(e)}},
                status=500,
            )

    async def get_which(self, request: web.Request) -> web.Response:
        """GET /comfy-cli/config/which"""
        try:
            result = await self.executor.execute(["which"], timeout=30)

            if not result["success"]:
                return web.json_response(
                    {
                        "success": False,
                        "error": {"code": "COMMAND_FAILED", "message": result["stderr"] or "Failed to get workspace path"},
                    },
                    status=500,
                )

            workspace_path = result["stdout"].strip()

            return web.json_response(
                {
                    "success": True,
                    "data": {
                        "workspace_path": workspace_path,
                        "comfyui_path": str(Path(workspace_path) / "ComfyUI"),
                        "is_default": True,
                    },
                    "raw_output": workspace_path,
                }
            )

        except Exception as e:
            logger.exception(f"get_which failed: {e}")
            return web.json_response(
                {"success": False, "error": {"code": "INTERNAL_ERROR", "message": str(e)}},
                status=500,
            )

    async def set_default(self, request: web.Request) -> web.Response:
        """POST /comfy-cli/config/set-default"""
        try:
            data = await request.json()
            path = data.get("path")

            if not path:
                return web.json_response(
                    {"success": False, "error": {"code": "MISSING_PARAMETER", "message": "path is required"}},
                    status=400,
                )

            args = ["set-default", path]
            if data.get("launch_extras"):
                args.extend(["--launch-extras", data["launch_extras"]])

            result = await self.executor.execute(args, timeout=30)

            if not result["success"]:
                return web.json_response(
                    {
                        "success": False,
                        "error": {
                            "code": "COMMAND_FAILED",
                            "message": result["stderr"] or "Failed to set default workspace",
                        },
                    },
                    status=400,
                )

            config_file = None
            for line in result["stdout"].split("\n"):
                if "Config file" in line:
                    config_file = line.split(":")[1].strip()

            return web.json_response(
                {
                    "success": True,
                    "data": {"default_workspace": path, "config_file": config_file},
                    "raw_output": result["stdout"],
                }
            )

        except Exception as e:
            logger.exception(f"set_default failed: {e}")
            return web.json_response(
                {"success": False, "error": {"code": "INTERNAL_ERROR", "message": str(e)}},
                status=500,
            )

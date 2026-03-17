"""
Model management API handler for comfy-cli.

Handles:
- GET /comfy-cli/model/list
- POST /comfy-cli/model/download
- POST /comfy-cli/model/remove
"""

from aiohttp import web
import logging
from pathlib import Path
from datetime import datetime
from ...comfy_cli.executor import ComfyCliExecutor, ComfyCLIError, JobStatus

logger = logging.getLogger(__name__)


class ModelHandler:
    """Handler for comfy-cli model management endpoints."""

    def __init__(self, executor: ComfyCliExecutor):
        self.executor = executor
        self.workspace = executor.workspace

    async def list_models(self, request: web.Request) -> web.Response:
        """GET /comfy-cli/model/list?relative_path=models/checkpoints"""
        relative_path = request.query.get("relative_path", "models/checkpoints")
        use_direct_fs = request.query.get("method", "fs") == "fs"

        try:
            if use_direct_fs:
                data = await self._list_models_fs(relative_path)
            else:
                result = await self.executor.execute(
                    ["model", "list", "--relative-path", relative_path],
                    timeout=60,
                )

                if not result["success"]:
                    return web.json_response(
                        {
                            "success": False,
                            "error": {"code": "COMMAND_FAILED", "message": result["stderr"] or "Failed to list models"},
                        },
                        status=500,
                    )

                models = self.executor.parse_list_output(result["stdout"])
                models_detail = await self._enhance_models_info(models, relative_path)

                data = {
                    "path": relative_path,
                    "absolute_path": str(self.workspace / relative_path),
                    "models": models_detail,
                    "count": len(models_detail),
                    "raw_output": result["stdout"],
                }

            return web.json_response({"success": True, "data": data})

        except Exception as e:
            logger.exception(f"list_models failed: {e}")
            return web.json_response(
                {"success": False, "error": {"code": "INTERNAL_ERROR", "message": str(e)}},
                status=500,
            )

    async def _list_models_fs(self, relative_path: str):
        """List models using direct filesystem access."""
        full_path = self.workspace / relative_path

        if not full_path.exists():
            return {"path": relative_path, "models": [], "count": 0, "error": "Path not found"}

        models = []
        model_extensions = {".safetensors", ".ckpt", ".pt", ".bin", ".pth"}

        for f in full_path.iterdir():
            if f.is_file() and f.suffix.lower() in model_extensions:
                stat = f.stat()
                models.append(
                    {
                        "filename": f.name,
                        "size": stat.st_size,
                        "size_human": self._format_size(stat.st_size),
                        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    }
                )

        return {
            "path": relative_path,
            "absolute_path": str(full_path),
            "models": sorted(models, key=lambda x: x["filename"]),
            "count": len(models),
        }

    async def _enhance_models_info(self, model_names, relative_path):
        """Enhance model list with file details."""
        full_path = self.workspace / relative_path
        result = []

        for name in model_names:
            model_file = full_path / name
            if model_file.exists():
                stat = model_file.stat()
                result.append(
                    {
                        "filename": name,
                        "size": stat.st_size,
                        "size_human": self._format_size(stat.st_size),
                        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    }
                )
            else:
                result.append({"filename": name, "size": None, "error": "File not found"})

        return result

    async def download_model(self, request: web.Request) -> web.Response:
        """POST /comfy-cli/model/download (async)"""
        try:
            data = await request.json()
            url = data.get("url")

            if not url:
                return web.json_response(
                    {"success": False, "error": {"code": "MISSING_URL", "message": "url is required"}},
                    status=400,
                )

            args = ["model", "download", "--url", url]

            if data.get("relative_path"):
                args.extend(["--relative-path", data["relative_path"]])
            if data.get("filename"):
                args.extend(["--filename", data["filename"]])
            if data.get("civitai_api_token"):
                args.extend(["--set-civitai-api-token", data["civitai_api_token"]])
            if data.get("hf_api_token"):
                args.extend(["--set-hf-api-token", data["hf_api_token"]])

            job = await self.executor.execute_async(args, timeout=1800)

            return web.json_response(
                {
                    "success": True,
                    "job_id": job.job_id,
                    "status": job.status.value,
                    "message": "Download started",
                    "data": {
                        "url": url,
                        "target_path": str(
                            self.workspace / data.get("relative_path", "models/checkpoints") / (data.get("filename") or "model")
                        ),
                    },
                },
                status=202,
            )

        except Exception as e:
            logger.exception(f"download_model failed: {e}")
            return web.json_response(
                {"success": False, "error": {"code": "INTERNAL_ERROR", "message": str(e)}},
                status=500,
            )

    async def get_download_status(self, request: web.Request) -> web.Response:
        """GET /comfy-cli/model/download/{job_id}/status"""
        job_id = request.match_info.get("job_id")

        job = self.executor.get_job(job_id)
        if not job:
            return web.json_response(
                {"success": False, "error": {"code": "JOB_NOT_FOUND", "message": f"Job {job_id} not found"}},
                status=404,
            )

        response_data = {"job_id": job_id, "status": job.status.value, "created_at": job.created_at.isoformat()}

        if job.status == JobStatus.RUNNING:
            parsed = self.executor.parse_download_progress(job.stdout or "")
            response_data["progress"] = parsed.get("progress", 0)
            response_data["parsed_output"] = parsed
        elif job.status == JobStatus.COMPLETED:
            parsed = self.executor.parse_download_progress(job.stdout or "")
            response_data["parsed_output"] = parsed
        elif job.status == JobStatus.FAILED:
            response_data["error"] = job.error or job.stderr

        return web.json_response({"success": True, "data": response_data})

    async def remove_model(self, request: web.Request) -> web.Response:
        """POST /comfy-cli/model/remove"""
        try:
            data = await request.json()
            model_names = data.get("model_names", [])

            if not model_names:
                return web.json_response(
                    {"success": False, "error": {"code": "MISSING_PARAMETER", "message": "model_names is required"}},
                    status=400,
                )

            args = ["model", "remove"]
            if data.get("relative_path"):
                args.extend(["--relative-path", data["relative_path"]])
            args.extend(["--model-names"] + model_names)
            if data.get("confirm"):
                args.append("--confirm")

            result = await self.executor.execute(args, timeout=60)

            if not result["success"]:
                return web.json_response(
                    {
                        "success": False,
                        "error": {"code": "COMMAND_FAILED", "message": result["stderr"] or "Failed to remove models"},
                    },
                    status=500,
                )

            return web.json_response(
                {"success": True, "data": {"removed": model_names, "count": len(model_names)}, "raw_output": result["stdout"]}
            )

        except Exception as e:
            logger.exception(f"remove_model failed: {e}")
            return web.json_response(
                {"success": False, "error": {"code": "INTERNAL_ERROR", "message": str(e)}},
                status=500,
            )

    @staticmethod
    def _format_size(bytes_size):
        """Format file size."""
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if bytes_size < 1024:
                return f"{bytes_size:.1f} {unit}"
            bytes_size /= 1024
        return f"{bytes_size:.1f} PB"

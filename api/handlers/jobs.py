"""Handler for /cm-cli-rest/jobs/* endpoints."""

from aiohttp import web
import logging

from ...cm_cli import CMCLIExecutor

logger = logging.getLogger(__name__)


class JobsHandler:
    """Handles job status REST API endpoints."""

    def __init__(self, executor: CMCLIExecutor):
        self.executor = executor

    async def get_job(self, request: web.Request) -> web.Response:
        """
        GET /cm-cli-rest/jobs/:id

        Get status of an async job.
        """
        job_id = request.match_info.get("id")

        if not job_id:
            return web.json_response(
                {
                    "success": False,
                    "error": {
                        "code": "INVALID_REQUEST",
                        "message": "Job ID is required",
                    }
                },
                status=400,
            )

        job = self.executor.get_job(job_id)

        if not job:
            return web.json_response(
                {
                    "success": False,
                    "error": {
                        "code": "JOB_NOT_FOUND",
                        "message": f"Job '{job_id}' not found",
                    }
                },
                status=404,
            )

        return web.json_response(
            {
                "success": True,
                "data": job.to_dict(),
            }
        )

    async def list_jobs(self, request: web.Request) -> web.Response:
        """
        GET /cm-cli-rest/jobs

        List all jobs (active and completed).
        """
        jobs = self.executor.list_jobs()

        return web.json_response(
            {
                "success": True,
                "data": {
                    "jobs": [job.to_dict() for job in jobs],
                    "total": len(jobs),
                }
            }
        )

    async def cleanup_job(self, request: web.Request) -> web.Response:
        """
        DELETE /cm-cli-rest/jobs/:id

        Remove a job from tracking (doesn't stop execution).
        """
        job_id = request.match_info.get("id")

        if not job_id:
            return web.json_response(
                {
                    "success": False,
                    "error": {
                        "code": "INVALID_REQUEST",
                        "message": "Job ID is required",
                    }
                },
                status=400,
            )

        if self.executor.cleanup_job(job_id):
            return web.json_response(
                {
                    "success": True,
                    "data": {
                        "message": f"Job '{job_id}' removed from tracking",
                    }
                }
            )
        else:
            return web.json_response(
                {
                    "success": False,
                    "error": {
                        "code": "JOB_NOT_FOUND",
                        "message": f"Job '{job_id}' not found",
                    }
                },
                status=404,
            )

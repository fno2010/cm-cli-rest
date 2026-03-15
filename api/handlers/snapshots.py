"""Handler for /cm-cli-rest/snapshots/* endpoints."""

from aiohttp import web
import logging

from ...cm_cli import CMCLIExecutor, CMCLIError

logger = logging.getLogger(__name__)


class SnapshotsHandler:
    """Handles snapshot management REST API endpoints."""

    def __init__(self, executor: CMCLIExecutor):
        self.executor = executor

    async def save_snapshot(self, request: web.Request) -> web.Response:
        """
        POST /cm-cli-rest/snapshots/save
        
        Save current custom node configuration as a snapshot.
        
        Request body (optional):
        {
            "name": "my-snapshot"  # optional, defaults to timestamp
        }
        """
        try:
            body = await request.json() if request.can_read_body else {}
        except Exception:
            body = {}

        snapshot_name = body.get("name")
        
        try:
            command = ["save-snapshot"]
            if snapshot_name:
                command.append(snapshot_name)

            result = await self.executor.execute(command)
            
            if result["success"]:
                return web.json_response(
                    {
                        "success": True,
                        "data": {
                            "message": "Snapshot saved successfully",
                            "name": snapshot_name or "timestamp-based",
                        }
                    }
                )
            else:
                return web.json_response(
                    {
                        "success": False,
                        "error": {
                            "code": "SNAPSHOT_SAVE_FAILED",
                            "message": "Failed to save snapshot",
                            "details": result["stderr"],
                        }
                    },
                    status=500,
                )

        except CMCLIError as e:
            logger.error(f"Error saving snapshot: {e}")
            return web.json_response(
                {
                    "success": False,
                    "error": {
                        "code": "SNAPSHOT_SAVE_FAILED",
                        "message": e.message,
                    }
                },
                status=500,
            )

    async def restore_snapshot(self, request: web.Request) -> web.Response:
        """
        POST /cm-cli-rest/snapshots/restore
        
        Restore custom node configuration from a snapshot.
        
        Request body:
        {
            "name": "my-snapshot"  # required
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

        snapshot_name = body.get("name")
        if not snapshot_name:
            return web.json_response(
                {
                    "success": False,
                    "error": {
                        "code": "INVALID_REQUEST",
                        "message": "Snapshot 'name' is required",
                    }
                },
                status=400,
            )

        try:
            job = await self.executor.execute_async(
                ["restore-snapshot", snapshot_name],
                timeout=600
            )
            
            return web.json_response(
                {
                    "success": True,
                    "data": {
                        "job_id": job.job_id,
                        "status": job.status.value,
                        "message": f"Restore started for snapshot '{snapshot_name}'",
                    }
                },
                status=202,
            )

        except CMCLIError as e:
            logger.error(f"Error restoring snapshot: {e}")
            return web.json_response(
                {
                    "success": False,
                    "error": {
                        "code": "SNAPSHOT_RESTORE_FAILED",
                        "message": e.message,
                    }
                },
                status=500,
            )

    async def list_snapshots(self, request: web.Request) -> web.Response:
        """
        GET /cm-cli-rest/snapshots
        
        List available snapshots.
        
        Note: cm-cli doesn't have a direct 'list snapshots' command.
        This reads from the snapshots directory if available.
        """
        # TODO: Implement snapshot listing by reading snapshots directory
        # For now, return a placeholder response
        return web.json_response(
            {
                "success": True,
                "data": {
                    "snapshots": [],
                    "message": "Snapshot listing not yet implemented",
                }
            }
        )

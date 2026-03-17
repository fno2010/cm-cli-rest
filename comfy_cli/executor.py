"""
comfy-cli executor - Wraps comfy-cli commands with async subprocess execution.

This module provides a Python interface to comfy-cli commands,
handling subprocess execution, output parsing, and job tracking for long-running operations.
"""

import asyncio
import json
import os
import subprocess
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class ComfyCLIError(Exception):
    """Base exception for comfy-cli execution errors."""

    def __init__(
        self,
        message: str,
        command: Optional[List[str]] = None,
        exit_code: Optional[int] = None,
    ):
        self.message = message
        self.command = command
        self.exit_code = exit_code
        super().__init__(self.message)


class JobStatus(str, Enum):
    """Status of an async comfy-cli job."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


@dataclass
class ComfyCLIJob:
    """Represents an async comfy-cli job with tracking information."""

    job_id: str
    command: List[str]
    status: JobStatus = JobStatus.PENDING
    exit_code: Optional[int] = None
    stdout: str = ""
    stderr: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert job to dictionary for JSON serialization."""
        return {
            "job_id": self.job_id,
            "command": " ".join(self.command),
            "status": self.status.value,
            "exit_code": self.exit_code,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error": self.error,
        }


class ComfyCliExecutor:
    """
    Executor for comfy-cli commands with async support and job tracking.

    Usage:
        executor = ComfyCliExecutor(workspace="/basedir")

        # Synchronous execution
        result = await executor.execute(["model", "list"])

        # Asynchronous job (for long-running operations)
        job = await executor.execute_async(["model", "download", "--url", "..."])
    """

    def __init__(
        self,
        workspace: Optional[str] = None,
        comfy_cmd: str = "comfy",
        python_path: str = "python",
        working_dir: Optional[str] = None,
    ):
        """
        Initialize the comfy-cli executor.

        Args:
            workspace: ComfyUI workspace path. If None, uses current directory.
            comfy_cmd: Command to invoke comfy-cli (default: "comfy").
            python_path: Path to Python interpreter (used only if comfy_cmd is a .py script).
            working_dir: Working directory for subprocess execution.
        """
        self.comfy_cmd = comfy_cmd
        self.python_path = python_path
        self.working_dir = Path(working_dir) if working_dir else Path.cwd()
        self.workspace = Path(workspace) if workspace else self.working_dir
        self._active_jobs: Dict[str, ComfyCLIJob] = {}

        # Auto-detect comfy-cli if needed
        self.comfy_cmd_path = self._auto_detect_comfy_cli()

    def _auto_detect_comfy_cli(self) -> Path:
        """
        Auto-detect comfy-cli executable location.

        Searches in order:
        1. System PATH (comfy installed as console script)
        2. Current working directory

        Returns:
            Path to comfy-cli executable or command name.
        """
        import shutil

        # Try to find 'comfy' in PATH
        comfy_in_path = shutil.which("comfy")
        if comfy_in_path:
            return Path(comfy_in_path)

        # Try 'comfy-cli' variant
        comfy_cli_in_path = shutil.which("comfy-cli")
        if comfy_cli_in_path:
            return Path(comfy_cli_in_path)

        # Return command name and let subprocess handle it
        return Path("comfy")

    def _build_command(self, args: List[str]) -> List[str]:
        """
        Build full command with workspace argument.

        Args:
            args: Command arguments (e.g., ["model", "list"]).

        Returns:
            Full command list including workspace configuration.
        """
        # Check if comfy_cmd is a .py file
        if self.comfy_cmd_path.suffix == ".py":
            command = [self.python_path, str(self.comfy_cmd_path)]
        else:
            command = [str(self.comfy_cmd_path)]

        # Add workspace argument
        command.extend(["--workspace", str(self.workspace)])

        # Add command arguments
        command.extend(args)

        return command

    async def execute(
        self,
        args: List[str],
        timeout: Optional[int] = None,
        capture_output: bool = True,
    ) -> Dict[str, Any]:
        """
        Execute a comfy-cli command synchronously.

        Args:
            args: Command arguments (e.g., ["model", "list"]).
            timeout: Timeout in seconds.
            capture_output: Whether to capture stdout/stderr.

        Returns:
            Dictionary with 'success', 'stdout', 'stderr', 'exit_code'.

        Raises:
            ComfyCLIError: If command execution fails.
        """
        command = self._build_command(args)

        try:
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE if capture_output else None,
                stderr=asyncio.subprocess.PIPE if capture_output else None,
                cwd=self.working_dir,
            )

            if capture_output:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout,
                )
                stdout_str = stdout.decode("utf-8", errors="replace") if stdout else ""
                stderr_str = stderr.decode("utf-8", errors="replace") if stderr else ""
            else:
                await asyncio.wait_for(process.wait(), timeout=timeout)
                stdout_str = ""
                stderr_str = ""

            success = process.returncode == 0

            return {
                "success": success,
                "stdout": stdout_str,
                "stderr": stderr_str,
                "exit_code": process.returncode,
                "command": " ".join(command),
            }

        except asyncio.TimeoutError as e:
            raise ComfyCLIError(
                f"Command timed out after {timeout} seconds",
                command=command,
            ) from e
        except FileNotFoundError as e:
            raise ComfyCLIError(
                f"comfy-cli not found at {self.comfy_cmd_path}. "
                "Ensure comfy-cli is installed (pip install comfy-cli) or in PATH.",
                command=command,
            ) from e
        except Exception as e:
            raise ComfyCLIError(
                f"Failed to execute command: {str(e)}",
                command=command,
            ) from e

    async def execute_async(
        self,
        args: List[str],
        timeout: Optional[int] = None,
    ) -> ComfyCLIJob:
        """
        Execute a comfy-cli command asynchronously with job tracking.

        Use this for long-running operations like model download, node install, etc.

        Args:
            args: Command arguments.
            timeout: Timeout in seconds.

        Returns:
            ComfyCLIJob object for tracking execution.
        """
        job_id = str(uuid.uuid4())[:8]
        command = self._build_command(args)

        job = ComfyCLIJob(
            job_id=job_id,
            command=command,
            status=JobStatus.RUNNING,
            started_at=datetime.now(),
        )

        self._active_jobs[job_id] = job
        process = None

        try:
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.working_dir,
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout,
            )

            job.stdout = stdout.decode("utf-8", errors="replace")
            job.stderr = stderr.decode("utf-8", errors="replace")
            job.exit_code = process.returncode
            job.status = JobStatus.COMPLETED if process.returncode == 0 else JobStatus.FAILED

            if process.returncode != 0:
                job.error = job.stderr.strip() or f"Exit code: {process.returncode}"

        except asyncio.TimeoutError:
            job.status = JobStatus.TIMEOUT
            job.error = f"Command timed out after {timeout} seconds"
            if process:
                try:
                    process.kill()
                except:
                    pass

        except Exception as e:
            job.status = JobStatus.FAILED
            job.error = str(e)

        finally:
            job.completed_at = datetime.now()

        return job

    def get_job(self, job_id: str) -> Optional[ComfyCLIJob]:
        """Get job by ID."""
        return self._active_jobs.get(job_id)

    def list_jobs(self) -> List[ComfyCLIJob]:
        """List all active jobs."""
        return list(self._active_jobs.values())

    def cleanup_job(self, job_id: str) -> bool:
        """Remove job from tracking. Returns True if job existed."""
        if job_id in self._active_jobs:
            del self._active_jobs[job_id]
            return True
        return False

    # Output parsing utilities

    @staticmethod
    def parse_list_output(raw_output: str) -> List[str]:
        """
        Parse list output (one item per line).

        Used for: model list, node simple-show

        Args:
            raw_output: Raw CLI output.

        Returns:
            List of items.
        """
        if not raw_output.strip():
            return []
        return [
            line.strip()
            for line in raw_output.strip().split("\n")
            if line.strip() and not line.startswith("#")
        ]

    @staticmethod
    def parse_env_output(raw_output: str) -> Dict[str, str]:
        """
        Parse environment output (key: value format).

        Args:
            raw_output: Raw CLI output.

        Returns:
            Dictionary of environment variables.
        """
        result = {}
        for line in raw_output.strip().split("\n"):
            if ":" in line:
                key, value = line.split(":", 1)
                key = key.strip().lower().replace(" ", "_")
                value = value.strip()
                result[key] = value
        return result

    @staticmethod
    def parse_download_progress(raw_output: str) -> Dict[str, Any]:
        """
        Parse download progress output.

        Args:
            raw_output: Raw CLI output.

        Returns:
            Dictionary with status, progress, filename, path.
        """
        import re

        result = {
            "status": "unknown",
            "progress": 0,
            "filename": None,
            "path": None,
        }

        # Check for completion
        if "Successfully downloaded" in raw_output or "Download complete" in raw_output:
            result["status"] = "completed"
            result["progress"] = 100

            # Try to extract filename and path
            match = re.search(r"Successfully downloaded (.+?) to (.+)", raw_output)
            if match:
                result["filename"] = match.group(1).strip()
                result["path"] = match.group(2).strip()

        # Check for progress
        progress_match = re.search(r"(\d+)%", raw_output)
        if progress_match:
            result["status"] = "downloading"
            result["progress"] = int(progress_match.group(1))

        # Check for errors
        if "Error" in raw_output or "Failed" in raw_output:
            result["status"] = "failed"

        return result

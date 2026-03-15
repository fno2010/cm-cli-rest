"""
cm-cli executor - Wraps ComfyUI-Manager CLI commands with async subprocess execution.

This module provides a Python interface to cm-cli (ComfyUI-Manager CLI) commands,
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


class CMCLIError(Exception):
    """Base exception for cm-cli execution errors."""

    def __init__(self, message: str, command: Optional[List[str]] = None, exit_code: Optional[int] = None):
        self.message = message
        self.command = command
        self.exit_code = exit_code
        super().__init__(self.message)


class JobStatus(str, Enum):
    """Status of an async cm-cli job."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class CMCLIJob:
    """Represents an async cm-cli job with tracking information."""

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


class CMCLIExecutor:
    """
    Executor for cm-cli commands with async support and job tracking.

    Usage:
        executor = CMCLIExecutor(cm_cli_path="/path/to/cm-cli.py")
        
        # Synchronous execution
        result = await executor.execute(["show", "installed"])
        
        # Asynchronous job (for long-running operations)
        job = await executor.execute_async(["install", "ComfyUI-Impact-Pack"])
    """

    def __init__(
        self,
        cm_cli_path: Optional[str] = None,
        python_path: str = "python",
        working_dir: Optional[str] = None,
    ):
        """
        Initialize the cm-cli executor.

        Args:
            cm_cli_path: Path to cm-cli.py script. If None, auto-detects from ComfyUI-Manager.
            python_path: Path to Python interpreter.
            working_dir: Working directory for subprocess execution (usually ComfyUI root).
        """
        self.python_path = python_path
        self.working_dir = Path(working_dir) if working_dir else Path.cwd()
        self._active_jobs: Dict[str, CMCLIJob] = {}

        # Auto-detect cm-cli path if not provided
        if cm_cli_path:
            self.cm_cli_path = Path(cm_cli_path)
        else:
            self.cm_cli_path = self._auto_detect_cm_cli()

    def _auto_detect_cm_cli(self) -> Path:
        """
        Auto-detect cm-cli.py location from ComfyUI-Manager installation.

        Searches in common locations:
        1. custom_nodes/ComfyUI-Manager/cm-cli.py
        2. custom_nodes/ComfyUI-Manager/cm_cli.py
        3. Current directory cm-cli.py
        """
        possible_paths = [
            self.working_dir / "custom_nodes" / "ComfyUI-Manager" / "cm-cli.py",
            self.working_dir / "custom_nodes" / "ComfyUI-Manager" / "cm_cli.py",
            self.working_dir / "cm-cli.py",
            Path(__file__).parent.parent.parent / "ComfyUI-Manager" / "cm-cli.py",
        ]

        for path in possible_paths:
            if path.exists():
                return path

        # If not found, return default path (will fail if cm-cli not installed)
        return Path("cm-cli.py")

    async def execute(
        self,
        args: List[str],
        timeout: Optional[int] = None,
        capture_output: bool = True,
    ) -> Dict[str, Any]:
        """
        Execute a cm-cli command synchronously.

        Args:
            args: Command arguments (e.g., ["show", "installed"]).
            timeout: Timeout in seconds.
            capture_output: Whether to capture stdout/stderr.

        Returns:
            Dictionary with 'success', 'stdout', 'stderr', 'exit_code'.

        Raises:
            CMCLIError: If command execution fails.
        """
        command = [str(self.cm_cli_path)] + args

        try:
            process = await asyncio.create_subprocess_exec(
                self.python_path,
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
            raise CMCLIError(
                f"Command timed out after {timeout} seconds",
                command=command,
            ) from e
        except FileNotFoundError as e:
            raise CMCLIError(
                f"cm-cli not found at {self.cm_cli_path}. "
                "Ensure ComfyUI-Manager is installed in custom_nodes/.",
                command=command,
            ) from e
        except Exception as e:
            raise CMCLIError(
                f"Failed to execute command: {str(e)}",
                command=command,
            ) from e

    async def execute_async(
        self,
        args: List[str],
        timeout: Optional[int] = None,
    ) -> CMCLIJob:
        """
        Execute a cm-cli command asynchronously with job tracking.

        Use this for long-running operations like install, update, etc.

        Args:
            args: Command arguments.
            timeout: Timeout in seconds.

        Returns:
            CMCLIJob object for tracking execution.
        """
        job_id = str(uuid.uuid4())[:8]
        command = [str(self.cm_cli_path)] + args

        job = CMCLIJob(
            job_id=job_id,
            command=command,
            status=JobStatus.RUNNING,
            started_at=datetime.now(),
        )

        self._active_jobs[job_id] = job

        try:
            process = await asyncio.create_subprocess_exec(
                self.python_path,
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
            job.status = JobStatus.FAILED
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

    def get_job(self, job_id: str) -> Optional[CMCLIJob]:
        """Get job by ID."""
        return self._active_jobs.get(job_id)

    def list_jobs(self) -> List[CMCLIJob]:
        """List all active jobs."""
        return list(self._active_jobs.values())

    def cleanup_job(self, job_id: str) -> bool:
        """Remove job from tracking. Returns True if job existed."""
        if job_id in self._active_jobs:
            del self._active_jobs[job_id]
            return True
        return False

    async def parse_installed_nodes(self, output: str) -> List[Dict[str, str]]:
        """
        Parse output from 'cm-cli.py show installed' command.

        Expected format:
        Node Name [repo_url]
        - version: 1.0.0

        Returns:
            List of dictionaries with 'name', 'repo', 'version' keys.
        """
        nodes = []
        current_node = None

        for line in output.strip().split("\n"):
            line = line.strip()
            if not line:
                continue

            # Node name line (contains [repo])
            if "[" in line and "]" in line:
                if current_node:
                    nodes.append(current_node)

                name_part = line.split("[")[0].strip()
                repo_part = line.split("[")[1].split("]")[0] if "[" in line else ""

                current_node = {
                    "name": name_part,
                    "repo": repo_part,
                    "version": "unknown",
                }

            # Version line
            elif line.startswith("- version:"):
                if current_node:
                    current_node["version"] = line.split(":")[1].strip()

        if current_node:
            nodes.append(current_node)

        return nodes

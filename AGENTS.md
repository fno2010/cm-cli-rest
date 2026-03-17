# AGENTS.md - Development Guide for cm-cli-rest

## Project Overview

**cm-cli-rest** is a ComfyUI custom node that exposes REST API endpoints for managing ComfyUI custom nodes via `cm-cli` (ComfyUI-Manager CLI) and `comfy-cli`.

### Dual CLI Support

The project supports **two CLI tools**:

1. **cm-cli** (ComfyUI-Manager CLI) - Node management focused
   - Endpoints: `/cm-cli-rest/*`
   - Package: `cm_cli/`
   - Provides: Node install/update/uninstall, snapshots

2. **comfy-cli** - Full ComfyUI management
   - Endpoints: `/comfy-cli/*`
   - Package: `comfy_cli/`
   - Provides: Config, models, nodes, ComfyUI lifecycle, workflows

### Environment

- **ComfyUI Version**: 0.15+
- **ComfyUI-Manager Version**: 4.0+ (provides cm-cli)
- **Python Version**: 3.9+ (tested on 3.11)
- **Runtime**: Integrated with ComfyUI's aiohttp server (no separate port)

---

## Build & Development Commands

### Syntax Validation (REQUIRED before commit)

```bash
# Check single file
python -m py_compile cm_cli/executor.py

# Check ALL Python files (CI-style)
find . -name "*.py" -not -path "./__pycache__/*" -not -path "./.git/*" \
  -exec python -m py_compile {} \;

# Quick validation of new comfy-cli modules
python -m py_compile comfy_cli/executor.py comfy_cli_routes.py \
  api/handlers/config.py api/handlers/models.py api/handlers/comfy_nodes.py
```

### Type Checking (Optional but Recommended)

```bash
# Install mypy
pip install mypy

# Run type checking on specific modules
mypy cm_cli/ api/handlers/
mypy comfy_cli/

# Strict mode (for new code)
mypy --strict cm_cli/executor.py
```

### Linting & Formatting

```bash
# Install ruff
pip install ruff

# Lint all files
ruff check .

# Auto-fix issues
ruff check --fix .

# Format code
ruff format .

# Check specific file
ruff check cm_cli/executor.py
```

### Testing

**Current Status**: No test suite exists (as of 2026-03-17). Tests marked as TODO.

**Manual Testing** (after changes):
```bash
# 1. Restart ComfyUI
# 2. Test endpoints with curl

# Health check
curl http://localhost:8188/cm-cli-rest/health

# List nodes (cm-cli)
curl http://localhost:8188/cm-cli-rest/nodes

# List models (comfy-cli)
curl "http://localhost:8188/comfy-cli/model/list?relative_path=models/checkpoints"

# Install node (async)
curl -X POST http://localhost:8188/cm-cli-rest/nodes/install \
  -H "Content-Type: application/json" \
  -d '{"name": "ComfyUI-Impact-Pack"}'
```

**Adding Tests** (future):
```bash
# Create tests/ directory
mkdir tests

# Use pytest
pip install pytest pytest-asyncio

# Run tests
pytest tests/
pytest tests/test_specific.py -v
```

---

## Code Style Guidelines

### Imports (STRICT)

**Order**: Standard library → Third-party → Local imports
**Grouping**: Separate groups with blank lines
**Type imports**: Use `from typing import ...`
**Relative imports**: Use for local modules (`.`, `..`)

```python
# ✅ CORRECT
import asyncio
import logging
from typing import Dict, List, Optional

from aiohttp import web

from ..cm_cli import CMCLIExecutor
from ..comfy_cli import ComfyCliExecutor
```

```python
# ❌ WRONG - Mixed import groups
from aiohttp import web
import asyncio
from ..cm_cli import CMCLIExecutor
from typing import Optional
```

### Formatting

- **Indentation**: 4 spaces (NO tabs)
- **Line length**: 100 characters (soft limit)
- **Quotes**: Double quotes for strings
- **Trailing commas**: Use in multi-line structures
- **Blank lines**: 2 between classes/functions, 1 between methods

### Type Hints (REQUIRED)

**Required for**:
- All function parameters
- All return types
- Class attributes

```python
# ✅ CORRECT
async def execute(
    self,
    args: List[str],
    timeout: Optional[int] = None,
) -> Dict[str, Any]:
    ...

# ❌ AVOID - No type hints
async def execute(self, args, timeout=None):
    ...
```

**Use specific types**:
```python
# ✅ Prefer specific types
def parse_output(raw: str) -> List[Dict[str, str]]:
    ...

# ❌ Avoid overly generic
def parse_output(raw: Any) -> Any:
    ...
```

### Naming Conventions

| Type | Convention | Examples |
|------|-----------|----------|
| Classes | PascalCase | `CMCLIExecutor`, `ComfyCliExecutor`, `NodesHandler` |
| Functions/Methods | snake_case | `list_nodes`, `execute_async`, `_auto_detect` |
| Constants | UPPER_CASE | `JOB_NOT_FOUND`, `MAX_CONCURRENT_JOBS` |
| Private methods | Leading underscore | `_auto_detect_cm_cli`, `_build_command` |
| Exceptions | End with `Error` | `CMCLIError`, `ComfyCLIError` |
| Variables | snake_case | `workspace_path`, `job_id` |

### Error Handling

**Pattern**:
1. Custom exceptions for domain errors
2. Structured JSON responses with `success`, `error.code`, `error.message`
3. Log errors BEFORE returning
4. Never suppress exceptions without logging

```python
# ✅ CORRECT PATTERN
try:
    result = await self.executor.execute(["show", "installed"])
    if not result["success"]:
        logger.error("Failed to list nodes: %s", result["stderr"])
        return web.json_response(
            {"success": False, "error": {"code": "CM_CLI_ERROR", "message": "Failed"}},
            status=500,
        )
except CMCLIError as e:
    logger.error("CMCLIError in list_nodes: %s", e.message)
    return web.json_response(
        {"success": False, "error": {"code": "CM_CLI_ERROR", "message": e.message}},
        status=500,
    )
except Exception as e:
    logger.exception("Unexpected error in list_nodes")
    return web.json_response(
        {"success": False, "error": {"code": "INTERNAL_ERROR", "message": str(e)}},
        status=500,
    )
```

```python
# ❌ WRONG - Silent exception
try:
    result = await self.executor.execute(args)
except Exception:
    pass  # NEVER DO THIS
```

### Async/Await

**Rules**:
- All I/O operations MUST be async (HTTP, subprocess, file I/O)
- Always wrap with `asyncio.wait_for()` for timeouts
- Use `asyncio.create_subprocess_exec()` for subprocesses
- Long-running operations → use `execute_async()` with job tracking

```python
# ✅ CORRECT
async def execute(self, args: List[str], timeout: Optional[int] = None) -> Dict[str, Any]:
    process = await asyncio.create_subprocess_exec(
        *command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await asyncio.wait_for(
        process.communicate(),
        timeout=timeout,
    )
```

### Docstrings (REQUIRED)

**Format**: Google style with Args, Returns, Raises sections

```python
# ✅ CORRECT
async def execute(
    self,
    args: List[str],
    timeout: Optional[int] = None,
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

    Example:
        >>> result = await executor.execute(["show", "installed"])
        >>> print(result["success"])
        True
    """
```

### File Organization

- **One class per file** (or tightly related classes)
- **Handlers**: One handler per endpoint group
- **Exports**: Define `__all__` in `__init__.py`

```
cm-cli-rest/
├── cm_cli/                 # cm-cli integration
│   ├── __init__.py
│   └── executor.py
├── comfy_cli/              # comfy-cli integration
│   ├── __init__.py
│   └── executor.py
├── api/
│   ├── routes.py           # cm-cli routes
│   └── handlers/
│       ├── nodes.py        # Node management (cm-cli)
│       ├── snapshots.py    # Snapshots (cm-cli)
│       ├── jobs.py         # Job tracking (shared)
│       ├── config.py       # Config (comfy-cli)
│       ├── models.py       # Models (comfy-cli)
│       └── comfy_nodes.py  # Nodes (comfy-cli)
├── comfy_cli_routes.py     # comfy-cli route registration
└── __init__.py             # Main entry point
```

---

## Architecture Patterns

### Handler Pattern (STANDARD)

```python
class NodesHandler:
    """Handles node management REST API endpoints."""

    def __init__(self, executor: CMCLIExecutor):
        """Initialize with shared executor."""
        self.executor = executor

    async def list_nodes(self, request: web.Request) -> web.Response:
        """GET /cm-cli-rest/nodes"""
        try:
            result = await self.executor.execute(["show", "installed"])
            # ... process result
        except Exception as e:
            logger.error("list_nodes failed: %s", e)
            return web.json_response(
                {"success": False, "error": {"code": "INTERNAL_ERROR", "message": str(e)}},
                status=500,
            )
```

### Executor Pattern

```python
class ComfyCliExecutor:
    """Executor for comfy-cli commands with async support."""

    def __init__(self, workspace: Optional[str] = None):
        self.workspace = Path(workspace) if workspace else Path.cwd()
        self._active_jobs: Dict[str, ComfyCLIJob] = {}

    def _build_command(self, args: List[str]) -> List[str]:
        """Build full command with workspace argument."""
        command = ["comfy", "--workspace", str(self.workspace)]
        command.extend(args)
        return command

    async def execute(self, args: List[str], timeout: Optional[int] = None) -> Dict[str, Any]:
        """Execute command synchronously."""
        # ...

    async def execute_async(self, args: List[str], timeout: Optional[int] = None) -> ComfyCLIJob:
        """Execute command asynchronously with job tracking."""
        # ...
```

### Response Format (STANDARD)

**Success (2xx)**:
```json
{
  "success": true,
  "data": {
    "nodes": [...],
    "total": 5
  },
  "raw_output": "Optional CLI output"
}
```

**Error (4xx/5xx)**:
```json
{
  "success": false,
  "error": {
    "code": "NODE_NOT_FOUND",
    "message": "Node 'invalid-node' not found",
    "details": "Optional additional context"
  }
}
```

**Async (202 Accepted)**:
```json
{
  "success": true,
  "job_id": "abc12345",
  "status": "running",
  "message": "Installation started"
}
```

---

## Common Tasks

### Adding a New Endpoint (cm-cli)

1. Add handler method in `api/handlers/nodes.py` (or appropriate file)
2. Register route in `api/routes.py`
3. Update README.md documentation
4. Add error codes to error response section
5. Run syntax check: `python -m py_compile api/handlers/nodes.py`

### Adding a New Endpoint (comfy-cli)

1. Add handler method in `api/handlers/comfy_nodes.py` (or `models.py`, `config.py`)
2. Register route in `comfy_cli_routes.py`
3. Update `COMFY_CLI_API.md` documentation
4. Run syntax check: `python -m py_compile api/handlers/comfy_nodes.py`

### Modifying CLI Execution

1. Edit `cm_cli/executor.py` or `comfy_cli/executor.py`
2. Update both `execute()` and `execute_async()` if needed
3. Add/update type hints
4. Run syntax validation

### Testing Changes

```bash
# 1. Syntax check
python -m py_compile <changed_file>.py

# 2. Restart ComfyUI

# 3. Test with curl
curl http://localhost:8188/cm-cli-rest/health
curl http://localhost:8188/comfy-cli/config/env
```

---

## Key Files Reference

| File | Purpose | CLI |
|------|---------|-----|
| `__init__.py` | Entry point, initializes both executors | Both |
| `api/routes.py` | cm-cli route definitions | cm-cli |
| `api/handlers/nodes.py` | Node management (cm-cli) | cm-cli |
| `api/handlers/snapshots.py` | Snapshot endpoints | cm-cli |
| `api/handlers/jobs.py` | Job tracking (shared) | Both |
| `cm_cli/executor.py` | cm-cli subprocess execution | cm-cli |
| `comfy_cli_routes.py` | comfy-cli route definitions | comfy-cli |
| `comfy_cli/executor.py` | comfy-cli subprocess execution | comfy-cli |
| `api/handlers/config.py` | Config endpoints | comfy-cli |
| `api/handlers/models.py` | Model management | comfy-cli |
| `api/handlers/comfy_nodes.py` | Node management | comfy-cli |

---

## Troubleshooting

### CLI Not Found

**Error**: `CM_CLI_NOT_FOUND` or `COMFY_CLI_ERROR: comfy-cli not found`

**Solutions**:
```bash
# For cm-cli (ComfyUI-Manager)
# Ensure ComfyUI-Manager is installed in custom_nodes/ComfyUI-Manager/

# For comfy-cli
pip install comfy-cli
comfy --version  # Verify installation
```

### Import Errors

**Cause**: Circular imports or missing `__init__.py`
**Fix**: Check import order, ensure all packages have `__init__.py`

### Type Errors

**Tool**: Use `lsp_diagnostics` in editor or run `mypy`
**Fix**: NEVER suppress with `as any` or `# type: ignore`

### Import Order Issues

**Wrong**:
```python
from aiohttp import web
import asyncio  # Should be before third-party
```

**Correct**:
```python
import asyncio
from aiohttp import web
```

---

## Documentation

- `README.md` - Main project documentation (cm-cli focused)
- `COMFY_CLI_API.md` - Complete comfy-cli API reference
- `COMFY_CLI_QUICKSTART.md` - comfy-cli quick start guide
- `AGENTS.md` - This file (development guide)

## External References

- [ComfyUI Custom Node Docs](https://docs.comfy.org/custom-nodes/overview)
- [ComfyUI-Manager](https://github.com/ltdrdata/ComfyUI-Manager)
- [cm-cli Documentation](https://github.com/Comfy-Org/ComfyUI-Manager/blob/main/docs/en/cm-cli.md)
- [comfy-cli](https://github.com/Comfy-Org/comfy-cli)

---

## Quick Reference

```bash
# Syntax check single file
python -m py_compile <file>.py

# Check all files
find . -name "*.py" -not -path "./__pycache__/*" -exec python -m py_compile {} \;

# Lint
ruff check .
ruff check --fix .

# Type check
mypy cm_cli/ comfy_cli/

# Test endpoint (cm-cli)
curl http://localhost:8188/cm-cli-rest/health

# Test endpoint (comfy-cli)
curl http://localhost:8188/comfy-cli/config/env
```

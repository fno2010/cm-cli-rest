# AGENTS.md - Development Guide for cm-cli-rest

## Project Overview

**cm-cli-rest** is a ComfyUI custom node that exposes REST API endpoints for managing ComfyUI custom nodes via `cm-cli` (ComfyUI-Manager CLI).

- **ComfyUI Version**: 0.15+
- **ComfyUI-Manager Version**: 4.0+
- **Python Version**: 3.9+ (tested on 3.11)
- **Runtime**: Integrated with ComfyUI's aiohttp server (no separate port)

---

## Build & Development Commands

### Syntax Validation
```bash
# Check Python syntax for a single file
python -m py_compile cm_cli/executor.py

# Check all Python files
find . -name "*.py" -not -path "./__pycache__/*" -exec python -m py_compile {} \;
```

### Type Checking (if type annotations added)
```bash
# Install mypy (optional - not in requirements.txt)
pip install mypy

# Run type checking
mypy cm_cli/ api/
```

### Linting (if linter added)
```bash
# Install ruff (recommended)
pip install ruff

# Lint all files
ruff check .

# Auto-fix issues
ruff check --fix .

# Format code
ruff format .
```

### Testing
**No test suite exists yet** (as of 2026-03-16). Tests are marked as TODO in IMPLEMENTATION_PLAN.md.

To add tests:
1. Create `tests/` directory
2. Use `pytest` as the test framework
3. Run with: `pytest tests/` or `pytest tests/test_specific_file.py -v`

---

## Code Style Guidelines

### Imports
- **Order**: Standard library → Third-party → Local imports
- **Grouping**: Separate import groups with blank lines
- **Type imports**: Use `from typing import ...` for type hints
- **Relative imports**: Use for local modules (`.`, `..`)

```python
# ✅ Correct
import asyncio
import logging
from typing import Dict, List, Optional

from aiohttp import web

from ..cm_cli import CMCLIExecutor
```

### Formatting
- **Indentation**: 4 spaces (no tabs)
- **Line length**: 100 characters (soft limit)
- **Quotes**: Double quotes for strings
- **Trailing commas**: Use in multi-line structures

### Type Hints
- **Required** for function parameters and return types
- **Use `Optional[T]`** for nullable values (Python 3.9+)
- **Use `Dict`, `List`, `Any`** from typing module

```python
# ✅ Correct
async def execute(
    self,
    args: List[str],
    timeout: Optional[int] = None,
) -> Dict[str, Any]:
    ...

# ❌ Avoid (no type hints)
async def execute(self, args, timeout=None):
    ...
```

### Naming Conventions
- **Classes**: PascalCase (`CMCLIExecutor`, `NodesHandler`)
- **Functions/Methods**: snake_case (`list_nodes`, `execute_async`)
- **Constants**: UPPER_CASE (`JOB_NOT_FOUND`, `MAX_CONCURRENT_JOBS`)
- **Private methods**: Leading underscore (`_auto_detect_cm_cli`)
- **Exceptions**: End with `Error` (`CMCLIError`)

### Error Handling
- **Custom exceptions**: Create specific exception classes for domain errors
- **Error responses**: Always return structured JSON with `success`, `error.code`, `error.message`
- **Logging**: Log errors with `logger.error()` before returning
- **Never suppress exceptions** without logging

```python
# ✅ Correct pattern
try:
    result = await self.executor.execute(["show", "installed"])
    if not result["success"]:
        return web.json_response(
            {"success": False, "error": {"code": "CM_CLI_ERROR", "message": "Failed"}},
            status=500,
        )
except CMCLIError as e:
    logger.error(f"Error listing nodes: {e}")
    return web.json_response(
        {"success": False, "error": {"code": "CM_CLI_ERROR", "message": e.message}},
        status=500,
    )
```

### Async/Await
- **All I/O operations**: Use async (HTTP, subprocess, file I/O)
- **Timeout handling**: Always wrap with `asyncio.wait_for()`
- **Subprocess execution**: Use `asyncio.create_subprocess_exec()`

### Docstrings
- **Required** for all public classes, methods, and functions
- **Format**: Google style (Args, Returns, Raises sections)
- **Include examples** for complex methods

```python
# ✅ Correct
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
    """
```

### File Organization
- **One class per file** (or tightly related classes)
- **Handlers**: One handler class per endpoint group (`nodes.py`, `snapshots.py`)
- **Exports**: Define `__all__` in `__init__.py` files

---

## Architecture Patterns

### Handler Pattern
```python
class NodesHandler:
    def __init__(self, executor: CMCLIExecutor):
        self.executor = executor

    async def list_nodes(self, request: web.Request) -> web.Response:
        # Handler logic
```

### Executor Pattern
```python
class CMCLIExecutor:
    def __init__(self, cm_cli_path: Optional[str] = None):
        # Auto-detect cm-cli if not provided
        self.cm_cli_path = self._auto_detect_cm_cli()

    async def execute(self, args: List[str]) -> Dict[str, Any]:
        # Execute command synchronously
```

### Response Format
All responses follow this structure:

**Success (2xx):**
```json
{
  "success": true,
  "data": { ... }
}
```

**Error (4xx/5xx):**
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable message",
    "details": "Optional additional context"
  }
}
```

---

## Key Files

| File | Purpose |
|------|---------|
| `__init__.py` | Entry point, initializes executor, registers routes |
| `api/routes.py` | Route definitions |
| `api/handlers/nodes.py` | Node management endpoints |
| `api/handlers/snapshots.py` | Snapshot endpoints |
| `api/handlers/jobs.py` | Job tracking endpoints |
| `cm_cli/executor.py` | cm-cli subprocess execution |
| `config/config.json` | Server configuration |

---

## Configuration

Edit `config/config.json`:

```json
{
  "enabled": true,
  "api_key": null,
  "cm_cli_path": null,
  "python_path": "python",
  "timeout": 300,
  "max_concurrent_jobs": 3,
  "logging_level": "INFO"
}
```

---

## Common Tasks

### Adding a New Endpoint
1. Add handler method in `api/handlers/nodes.py` (or appropriate handler file)
2. Register route in `api/routes.py`
3. Update README.md documentation
4. Add error codes to error response section

### Modifying cm-cli Execution
1. Edit `cm_cli/executor.py`
2. Ensure both `execute()` and `execute_async()` are updated
3. Run syntax check: `python -m py_compile cm_cli/executor.py`

### Testing Changes
1. Restart ComfyUI
2. Test endpoint with curl:
   ```bash
   curl http://localhost:8188/cm-cli-rest/health
   ```

---

## Troubleshooting

### cm-cli Not Found
- **Error**: `CM_CLI_NOT_FOUND`
- **Cause**: cm-cli executable not in PATH
- **Fix**: Set `cm_cli_path` in config.json to full path

### Import Errors
- **Cause**: Circular imports or missing `__init__.py`
- **Fix**: Check import order, ensure all packages have `__init__.py`

### Type Errors
- **Tool**: Use `lsp_diagnostics` in editor
- **Fix**: Never suppress with `as any` or `# type: ignore`

---

## References

- [ComfyUI Custom Node Docs](https://docs.comfy.org/custom-nodes/overview)
- [ComfyUI-Manager](https://github.com/ltdrdata/ComfyUI-Manager)
- [cm-cli Documentation](https://github.com/Comfy-Org/ComfyUI-Manager/blob/main/docs/en/cm-cli.md)

# cm-cli-rest Implementation Plan

**Project**: ComfyUI Custom Node - REST API for cm-cli  
**Version**: 0.1.0  
**Last Updated**: 2026-03-15  

---

## Project Overview

A ComfyUI custom node that exposes REST API endpoints for managing ComfyUI custom nodes via `cm-cli` (ComfyUI-Manager CLI).

### Goals

- Expose cm-cli commands as REST API endpoints
- Integrate with ComfyUI's built-in aiohttp server (no separate port)
- Support async operations for long-running commands (install, update)
- Provide job tracking for async operations
- Maintain compatibility with ComfyUI 0.15+ and Manager 4.0+

---

## Architecture

### Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **HTTP Server** | ComfyUI PromptServer | No port conflicts, integrated lifecycle |
| **Command Execution** | Async subprocess | Non-blocking, matches cm-cli design |
| **Job Tracking** | In-memory dict | Simple, sufficient for single-instance |
| **Configuration** | JSON config file | Human-readable, easy to modify |
| **Authentication** | Optional API key | Security for exposed instances |

### Project Structure

```
cm-cli-rest/
├── __init__.py              # Entry point, route registration, NODE_CLASS_MAPPINGS
├── nodes.py                 # Optional: ComfyUI workflow nodes
├── api/
│   ├── __init__.py          # exports setup_routes
│   ├── routes.py            # Route definitions
│   └── handlers/
│       ├── __init__.py
│       ├── nodes.py         # /nodes/* endpoint handlers
│       └── snapshots.py     # /snapshots/* endpoint handlers
├── cm_cli/
│   ├── __init__.py
│   └── executor.py          # cm-cli subprocess execution layer
├── config/
│   └── config.json          # Server configuration
├── requirements.txt
├── README.md
└── examples/
    └── api-usage.json       # Example API calls
```

---

## REST API Specification

### Endpoints

#### Health & Status

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/cm-cli-rest/health` | Health check |
| `GET` | `/cm-cli-rest/jobs/:id` | Get async job status |

#### Node Management

| Method | Endpoint | cm-cli Command | Description |
|--------|----------|----------------|-------------|
| `GET` | `/cm-cli-rest/nodes` | `show installed` | List all installed nodes |
| `GET` | `/cm-cli-rest/nodes/:name` | `show installed` (filtered) | Get specific node |
| `POST` | `/cm-cli-rest/nodes/install` | `install <name>` | Install node (async) |
| `POST` | `/cm-cli-rest/nodes/uninstall` | `uninstall <name>` | Uninstall node |
| `POST` | `/cm-cli-rest/nodes/update` | `update <name>` | Update node (async) |
| `POST` | `/cm-cli-rest/nodes/update-all` | `update all` | Update all nodes (async) |
| `POST` | `/cm-cli-rest/nodes/enable` | `enable <name>` | Enable node |
| `POST` | `/cm-cli-rest/nodes/disable` | `disable <name>` | Disable node |
| `POST` | `/cm-cli-rest/nodes/fix` | `fix <name>` | Fix node issues |
| `POST` | `/cm-cli-rest/nodes/reinstall` | `reinstall <name>` | Reinstall node |

#### Snapshots

| Method | Endpoint | cm-cli Command | Description |
|--------|----------|----------------|-------------|
| `POST` | `/cm-cli-rest/snapshots/save` | `save-snapshot` | Save current state |
| `POST` | `/cm-cli-rest/snapshots/restore` | `restore-snapshot` | Restore snapshot |
| `GET` | `/cm-cli-rest/snapshots` | N/A | List available snapshots |

---

## Request/Response Formats

### Health Check

**Request:**
```http
GET /cm-cli-rest/health
```

**Response:**
```json
{
  "status": "healthy",
  "cm_cli_path": "/path/to/cm-cli.py",
  "cm_cli_version": "4.0.5",
  "timestamp": "2026-03-15T10:00:00Z"
}
```

### List Nodes

**Request:**
```http
GET /cm-cli-rest/nodes
```

**Response:**
```json
{
  "success": true,
  "data": {
    "nodes": [
      {
        "name": "ComfyUI-Impact-Pack",
        "repo": "https://github.com/ltdrdata/ComfyUI-Impact-Pack",
        "version": "5.12.0",
        "status": "enabled"
      }
    ],
    "total": 1
  }
}
```

### Install Node (Async)

**Request:**
```http
POST /cm-cli-rest/nodes/install
Content-Type: application/json

{
  "name": "ComfyUI-Impact-Pack",
  "channel": "recent",
  "mode": "remote"
}
```

**Response (202 Accepted):**
```json
{
  "success": true,
  "data": {
    "job_id": "abc12345",
    "status": "running",
    "message": "Installation started"
  }
}
```

### Get Job Status

**Request:**
```http
GET /cm-cli-rest/jobs/abc12345
```

**Response:**
```json
{
  "success": true,
  "data": {
    "job_id": "abc12345",
    "command": "cm-cli.py install ComfyUI-Impact-Pack",
    "status": "completed",
    "exit_code": 0,
    "stdout": "Installation complete...",
    "stderr": "",
    "created_at": "2026-03-15T10:00:00Z",
    "started_at": "2026-03-15T10:00:01Z",
    "completed_at": "2026-03-15T10:00:30Z"
  }
}
```

### Error Response

**Response (4xx/5xx):**
```json
{
  "success": false,
  "error": {
    "code": "NODE_NOT_FOUND",
    "message": "Node 'invalid-node' not found",
    "details": "No custom node with this name exists in the registry"
  }
}
```

---

## Implementation Status

### ✅ Completed

| Component | File | Status | Notes |
|-----------|------|--------|-------|
| **Project Structure** | `cm-cli-rest/` | ✅ Done | Directory structure created |
| **cm-cli Executor** | `cm_cli/executor.py` | ✅ Done | Async subprocess execution, job tracking |
| **cm-cli Module** | `cm_cli/__init__.py` | ✅ Done | Exports executor classes |

### 🚧 In Progress

| Component | File | Status | Notes |
|-----------|------|--------|-------|
| **API Routes** | `api/routes.py` | 🔄 Pending | Route definitions |
| **Nodes Handler** | `api/handlers/nodes.py` | 🔄 Pending | Node management endpoints |
| **Snapshots Handler** | `api/handlers/snapshots.py` | 🔄 Pending | Snapshot endpoints |
| **Main Entry Point** | `__init__.py` | 🔄 Pending | Route registration, NODE_CLASS_MAPPINGS |

### ⏳ Pending

| Component | File | Priority |
|-----------|------|----------|
| **Configuration** | `config/config.json` | Medium |
| **Requirements** | `requirements.txt` | Medium |
| **Documentation** | `README.md` | Medium |
| **Examples** | `examples/api-usage.json` | Low |
| **Tests** | `tests/` | Low |

---

## Implementation Roadmap

### Phase 1: Core Infrastructure (Current)
- [x] Create project structure
- [x] Implement cm-cli executor
- [ ] Create API route definitions
- [ ] Implement health check endpoint
- [ ] Implement list nodes endpoint

### Phase 2: Node Management
- [ ] Implement install endpoint (async)
- [ ] Implement uninstall endpoint
- [ ] Implement update endpoints
- [ ] Implement enable/disable endpoints
- [ ] Add job status tracking

### Phase 3: Advanced Features
- [ ] Implement snapshot endpoints
- [ ] Add configuration system
- [ ] Add error handling middleware
- [ ] Add optional API key authentication
- [ ] Add request logging

### Phase 4: Documentation & Testing
- [ ] Write README.md
- [ ] Create requirements.txt
- [ ] Add API usage examples
- [ ] Write unit tests
- [ ] Add integration tests

---

## Key Classes

### CMCLIExecutor

```python
from cm_cli import CMCLIExecutor

executor = CMCLIExecutor(
    cm_cli_path="/path/to/cm-cli.py",
    working_dir="/path/to/ComfyUI"
)

# Synchronous execution
result = await executor.execute(["show", "installed"])

# Asynchronous job
job = await executor.execute_async(["install", "ComfyUI-Impact-Pack"])

# Get job status
job = executor.get_job("abc12345")
```

### API Handler Pattern

```python
from aiohttp import web
from cm_cli import CMCLIExecutor

class NodesHandler:
    def __init__(self, executor: CMCLIExecutor):
        self.executor = executor
    
    async def list_nodes(self, request: web.Request) -> web.Response:
        result = await self.executor.execute(["show", "installed"])
        nodes = await self.executor.parse_installed_nodes(result["stdout"])
        return web.json_response({"success": True, "data": {"nodes": nodes}})
```

---

## Dependencies

### Required

- Python >= 3.9 (ComfyUI requirement)
- ComfyUI-Manager >= 4.0 (provides cm-cli)

### Optional

- `aiohttp` (already included with ComfyUI)
- No additional external dependencies

---

## Installation

### Prerequisites

1. ComfyUI 0.15+ installed
2. ComfyUI-Manager 4.0+ installed in `custom_nodes/ComfyUI-Manager/`

### Steps

1. Clone this repository to `custom_nodes/cm-cli-rest/`
2. Restart ComfyUI
3. API endpoints available at `http://localhost:8188/cm-cli-rest/*`

---

## Configuration

### config/config.json

```json
{
  "enabled": true,
  "api_key": null,
  "cm_cli_path": null,
  "timeout": 300,
  "max_concurrent_jobs": 3
}
```

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `enabled` | bool | `true` | Enable/disable API |
| `api_key` | string | `null` | Optional API key for auth |
| `cm_cli_path` | string | `null` | Auto-detect if null |
| `timeout` | int | `300` | Command timeout (seconds) |
| `max_concurrent_jobs` | int | `3` | Max parallel operations |

---

## Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `CM_CLI_NOT_FOUND` | 500 | cm-cli.py not found |
| `NODE_NOT_FOUND` | 404 | Node name not in registry |
| `INSTALL_FAILED` | 500 | Node installation failed |
| `JOB_NOT_FOUND` | 404 | Async job ID not found |
| `TIMEOUT` | 504 | Command timed out |
| `UNAUTHORIZED` | 401 | Invalid/missing API key |
| `INVALID_REQUEST` | 400 | Malformed request body |

---

## Security Considerations

1. **API Key Authentication**: Optional but recommended for exposed instances
2. **Command Injection**: All inputs sanitized before passing to subprocess
3. **Path Traversal**: Working directory locked to ComfyUI root
4. **Rate Limiting**: Consider adding for production use

---

## Future Enhancements

- [ ] WebSocket support for real-time job progress
- [ ] Queue system for job prioritization
- [ ] Persistent job storage (SQLite)
- [ ] OpenAPI/Swagger documentation
- [ ] Admin dashboard UI
- [ ] Webhook notifications for job completion
- [ ] Support for custom node search/browse

---

## References

- [ComfyUI Custom Node Docs](https://docs.comfy.org/custom-nodes/overview)
- [ComfyUI Server Routes](https://docs.comfy.org/development/comfyui-server/comms_routes)
- [ComfyUI-Manager](https://github.com/ltdrdata/ComfyUI-Manager)
- [cm-cli Documentation](https://github.com/Comfy-Org/ComfyUI-Manager/blob/main/docs/en/cm-cli.md)

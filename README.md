# cm-cli-rest & comfy-cli REST

A ComfyUI custom node that exposes REST API endpoints for managing ComfyUI custom nodes and models via `cm-cli` (ComfyUI-Manager CLI) and `comfy-cli`.

## Features

- 🚀 **Dual CLI Support**: REST APIs for both cm-cli and comfy-cli
- 🔗 **Integrated with ComfyUI**: Uses ComfyUI's built-in server (no separate port)
- ⚡ **Async Operations**: Long-running commands (install, update, download) run asynchronously
- 📊 **Job Tracking**: Monitor progress of async operations
- 🛡️ **Error Handling**: Comprehensive error responses with status codes
- 🔐 **Optional Authentication**: API key support for exposed instances

## Installation

### Prerequisites

- ComfyUI 0.15+
- ComfyUI-Manager 4.0+ (provides `cm-cli`)
- Python 3.9+
- comfy-cli (optional, for model management): `pip install comfy-cli`

### Steps

1. **Clone this repository** into your ComfyUI custom nodes directory:

   ```bash
   cd ComfyUI/custom_nodes
   git clone https://github.com/YOUR_USERNAME/cm-cli-rest.git
   ```

2. **Install comfy-cli** (optional, for model management):

   ```bash
   pip install comfy-cli
   ```

3. **Restart ComfyUI**

4. **Verify installation**: Check ComfyUI console for:
   ```
   cm-cli-rest & comfy-cli REST initialized - APIs available at /cm-cli-rest/* and /comfy-cli/*
   ```

## Quick Start

### Health Check (cm-cli)

```bash
curl http://localhost:8188/cm-cli-rest/health
```

Response:
```json
{
  "status": "healthy",
  "service": "cm-cli-rest",
  "version": "0.1.0",
  "timestamp": "2026-03-15T10:00:00Z"
}
```

### List Installed Nodes (cm-cli)

```bash
curl http://localhost:8188/cm-cli-rest/nodes
```

### Install a Node (cm-cli)

```bash
curl -X POST http://localhost:8188/cm-cli-rest/nodes/install \
  -H "Content-Type: application/json" \
  -d '{"name": "ComfyUI-Impact-Pack"}'
```

Response (202 Accepted):
```json
{
  "success": true,
  "data": {
    "job_id": "abc12345",
    "status": "running",
    "message": "Installation started for 'ComfyUI-Impact-Pack'"
  }
}
```

### List Models (comfy-cli)

```bash
curl "http://localhost:8188/comfy-cli/model/list?relative_path=models/checkpoints"
```

### Download a Model (comfy-cli)

```bash
curl -X POST "http://localhost:8188/comfy-cli/model/download" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://civitai.com/models/43331",
    "relative_path": "models/checkpoints"
  }'
```

### Check Job Status

```bash
curl http://localhost:8188/cm-cli-rest/jobs/abc12345
```

## API Endpoints

### cm-cli REST API (`/cm-cli-rest/*`)

#### Health & Status

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/cm-cli-rest/health` | Health check |
| `GET` | `/cm-cli-rest/jobs` | List all jobs |
| `GET` | `/cm-cli-rest/jobs/:id` | Get job status |
| `DELETE` | `/cm-cli-rest/jobs/:id` | Remove job from tracking |

#### Node Management

| Method | Endpoint | Description | Async |
|--------|----------|-------------|-------|
| `GET` | `/cm-cli-rest/nodes` | List installed nodes | No |
| `GET` | `/cm-cli-rest/nodes/:name` | Get node details | No |
| `POST` | `/cm-cli-rest/nodes/install` | Install node | ✅ |
| `POST` | `/cm-cli-rest/nodes/uninstall` | Uninstall node | No |
| `POST` | `/cm-cli-rest/nodes/update` | Update node | ✅ |
| `POST` | `/cm-cli-rest/nodes/update-all` | Update all nodes | ✅ |
| `POST` | `/cm-cli-rest/nodes/enable` | Enable node | No |
| `POST` | `/cm-cli-rest/nodes/disable` | Disable node | No |
| `POST` | `/cm-cli-rest/nodes/fix` | Fix node dependencies | ✅ |
| `POST` | `/cm-cli-rest/nodes/reinstall` | Reinstall node | ✅ |

#### Snapshots

| Method | Endpoint | Description | Async |
|--------|----------|-------------|-------|
| `POST` | `/cm-cli-rest/snapshots/save` | Save snapshot | No |
| `POST` | `/cm-cli-rest/snapshots/restore` | Restore snapshot | ✅ |
| `GET` | `/cm-cli-rest/snapshots` | List snapshots | No |

### comfy-cli REST API (`/comfy-cli/*`)

#### Configuration

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/comfy-cli/config/env` | Get environment config |
| `GET` | `/comfy-cli/config/which` | Get workspace path |
| `POST` | `/comfy-cli/config/set-default` | Set default workspace |

#### Model Management

| Method | Endpoint | Description | Async |
|--------|----------|-------------|-------|
| `GET` | `/comfy-cli/model/list` | List models | No |
| `POST` | `/comfy-cli/model/download` | Download model | ✅ |
| `GET` | `/comfy-cli/model/download/:id/status` | Get download status | No |
| `POST` | `/comfy-cli/model/remove` | Remove model | No |

#### Node Management

| Method | Endpoint | Description | Async |
|--------|----------|-------------|-------|
| `GET` | `/comfy-cli/node/simple-show` | List nodes (simple) | No |
| `GET` | `/comfy-cli/node/show` | List nodes (detailed) | No |
| `POST` | `/comfy-cli/node/install` | Install node | ✅ |
| `POST` | `/comfy-cli/node/update` | Update node | ✅ |
| `POST` | `/comfy-cli/node/enable` | Enable node | No |
| `POST` | `/comfy-cli/node/disable` | Disable node | No |
| `POST` | `/comfy-cli/node/uninstall` | Uninstall node | No |

## Request/Response Examples

### cm-cli: Install Node with Options

```bash
curl -X POST http://localhost:8188/cm-cli-rest/nodes/install \
  -H "Content-Type: application/json" \
  -d '{
    "name": "ComfyUI-Impact-Pack",
    "channel": "recent",
    "mode": "remote"
  }'
```

### cm-cli: Update All Nodes

```bash
curl -X POST http://localhost:8188/cm-cli-rest/nodes/update-all
```

### cm-cli: Save Snapshot

```bash
curl -X POST http://localhost:8188/cm-cli-rest/snapshots/save \
  -H "Content-Type: application/json" \
  -d '{"name": "pre-update-backup"}'
```

### comfy-cli: Download Model

```bash
curl -X POST "http://localhost:8188/comfy-cli/model/download" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://civitai.com/models/43331",
    "relative_path": "models/checkpoints",
    "filename": "my_model.safetensors"
  }'
```

### comfy-cli: List Installed Nodes

```bash
curl "http://localhost:8188/comfy-cli/node/simple-show?mode=installed"
```

### comfy-cli: Install Node

```bash
curl -X POST "http://localhost:8188/comfy-cli/node/install" \
  -H "Content-Type: application/json" \
  -d '{
    "nodes": ["ComfyUI-Impact-Pack"],
    "fast_deps": true
  }'
```

## Error Responses

All errors follow this format:

```json
{
  "success": false,
  "error": {
    "code": "NODE_NOT_FOUND",
    "message": "Node 'invalid-node' not found",
    "details": "Additional context..."
  }
}
```

### Common Error Codes (cm-cli)

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `CM_CLI_NOT_FOUND` | 500 | cm-cli.py not found |
| `NODE_NOT_FOUND` | 404 | Node not in registry |
| `INSTALL_FAILED` | 500 | Installation failed |
| `JOB_NOT_FOUND` | 404 | Job ID not found |
| `TIMEOUT` | 504 | Command timed out |
| `INVALID_REQUEST` | 400 | Malformed request |

### Common Error Codes (comfy-cli)

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `COMFY_CLI_ERROR` | 500 | comfy-cli execution failed |
| `COMMAND_FAILED` | 500 | CLI command returned error |
| `MISSING_PARAMETER` | 400 | Required parameter missing |
| `INVALID_PARAMETER` | 400 | Invalid parameter value |
| `JOB_NOT_FOUND` | 404 | Async job ID not found |

## Configuration

Edit `config/config.json`:

```json
{
  "enabled": true,              // Enable/disable API
  "api_key": null,              // Optional API key for auth
  "cm_cli_path": null,          // Auto-detect if null
  "python_path": "python",      // Python interpreter
  "timeout": 300,               // Command timeout (seconds)
  "max_concurrent_jobs": 3,     // Max parallel operations
  "logging_level": "INFO"       // Logging verbosity
}
```

## Architecture

```
cm-cli-rest/
├── __init__.py              # Entry point, initializes both executors
├── api/
│   ├── routes.py            # cm-cli route definitions
│   └── handlers/
│       ├── nodes.py         # Node management (cm-cli)
│       ├── snapshots.py     # Snapshots (cm-cli)
│       ├── jobs.py          # Job tracking (shared)
│       ├── config.py        # Config (comfy-cli)
│       ├── models.py        # Models (comfy-cli)
│       └── comfy_nodes.py   # Nodes (comfy-cli)
├── cm_cli/
│   └── executor.py          # cm-cli subprocess execution
├── comfy_cli/
│   └── executor.py          # comfy-cli subprocess execution
├── comfy_cli_routes.py      # comfy-cli route registration
├── config/
│   └── config.json          # Configuration file
└── README.md
```

### How It Works

1. **Integration**: Routes registered with `PromptServer.instance.app` (ComfyUI's aiohttp server)
2. **Execution**: Commands executed via `asyncio.create_subprocess_exec`
3. **Job Tracking**: Long-running operations tracked in-memory with UUID
4. **Error Handling**: Comprehensive error responses with appropriate HTTP status codes

## Development

### Running Tests

```bash
# TODO: Add test suite
pytest tests/
```

### Syntax Validation

```bash
# Check all Python files
find . -name "*.py" -not -path "./__pycache__/*" -exec python -m py_compile {} \;

# Lint
ruff check .
ruff check --fix .

# Type check
mypy cm_cli/ comfy_cli/
```

### Adding New Endpoints

1. Add handler method in appropriate `api/handlers/*.py` file
2. Register route in `api/routes.py` (cm-cli) or `comfy_cli_routes.py` (comfy-cli)
3. Update this README or `COMFY_CLI_API.md`

## Troubleshooting

### cm-cli Not Found

**Error**: `CM_CLI_NOT_FOUND`

**Solution**: Ensure ComfyUI-Manager is installed in `custom_nodes/ComfyUI-Manager/`

### comfy-cli Not Found

**Error**: `COMFY_CLI_ERROR: comfy-cli not found`

**Solution**:
```bash
pip install comfy-cli
comfy --version  # Verify installation
```

### Port Conflicts

This extension uses ComfyUI's built-in server (default: 8188). No separate port needed.

### Timeout Errors

Increase `timeout` in `config/config.json` for slow operations.

## Security Considerations

- **API Key**: Set `api_key` in config if exposing externally
- **Input Sanitization**: All inputs validated before subprocess execution
- **Path Traversal**: Working directory locked to ComfyUI root

## Documentation

- `README.md` - This file (main documentation)
- `COMFY_CLI_API.md` - Complete comfy-cli API reference
- `COMFY_CLI_QUICKSTART.md` - comfy-cli quick start guide
- `AGENTS.md` - Development guide for agentic coding

## License

MIT License - See LICENSE file for details.

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## References

- [ComfyUI Documentation](https://docs.comfy.org/)
- [ComfyUI-Manager](https://github.com/ltdrdata/ComfyUI-Manager)
- [cm-cli Documentation](https://github.com/Comfy-Org/ComfyUI-Manager/blob/main/docs/en/cm-cli.md)
- [comfy-cli](https://github.com/Comfy-Org/comfy-cli)

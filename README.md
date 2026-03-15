# cm-cli-rest

A ComfyUI custom node that exposes REST API endpoints for managing ComfyUI custom nodes via `cm-cli` (ComfyUI-Manager CLI).

## Features

- 🚀 **REST API for cm-cli**: Control ComfyUI-Manager from external applications
- 🔗 **Integrated with ComfyUI**: Uses ComfyUI's built-in server (no separate port)
- ⚡ **Async Operations**: Long-running commands (install, update) run asynchronously
- 📊 **Job Tracking**: Monitor progress of async operations
- 🛡️ **Error Handling**: Comprehensive error responses with status codes
- 🔐 **Optional Authentication**: API key support for exposed instances

## Installation

### Prerequisites

- ComfyUI 0.15+
- ComfyUI-Manager 4.0+ (provides `cm-cli`)
- Python 3.9+

### Steps

1. **Clone this repository** into your ComfyUI custom nodes directory:

   ```bash
   cd ComfyUI/custom_nodes
   git clone https://github.com/YOUR_USERNAME/cm-cli-rest.git
   ```

2. **Restart ComfyUI**

3. **Verify installation**: Check ComfyUI console for:
   ```
   cm-cli-rest initialized - REST API available at /cm-cli-rest/*
   ```

## Quick Start

### Health Check

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

### List Installed Nodes

```bash
curl http://localhost:8188/cm-cli-rest/nodes
```

### Install a Node

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

### Check Job Status

```bash
curl http://localhost:8188/cm-cli-rest/jobs/abc12345
```

## API Endpoints

### Health & Status

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/cm-cli-rest/health` | Health check |
| `GET` | `/cm-cli-rest/jobs` | List all jobs |
| `GET` | `/cm-cli-rest/jobs/:id` | Get job status |
| `DELETE` | `/cm-cli-rest/jobs/:id` | Remove job from tracking |

### Node Management

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

### Snapshots

| Method | Endpoint | Description | Async |
|--------|----------|-------------|-------|
| `POST` | `/cm-cli-rest/snapshots/save` | Save snapshot | No |
| `POST` | `/cm-cli-rest/snapshots/restore` | Restore snapshot | ✅ |
| `GET` | `/cm-cli-rest/snapshots` | List snapshots | No |

## Request/Response Examples

### Install Node with Options

```bash
curl -X POST http://localhost:8188/cm-cli-rest/nodes/install \
  -H "Content-Type: application/json" \
  -d '{
    "name": "ComfyUI-Impact-Pack",
    "channel": "recent",
    "mode": "remote"
  }'
```

### Update All Nodes

```bash
curl -X POST http://localhost:8188/cm-cli-rest/nodes/update-all
```

### Save Snapshot

```bash
curl -X POST http://localhost:8188/cm-cli-rest/snapshots/save \
  -H "Content-Type: application/json" \
  -d '{"name": "pre-update-backup"}'
```

### Restore Snapshot

```bash
curl -X POST http://localhost:8188/cm-cli-rest/snapshots/restore \
  -H "Content-Type: application/json" \
  -d '{"name": "pre-update-backup"}'
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

### Common Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `CM_CLI_NOT_FOUND` | 500 | cm-cli.py not found |
| `NODE_NOT_FOUND` | 404 | Node not in registry |
| `INSTALL_FAILED` | 500 | Installation failed |
| `JOB_NOT_FOUND` | 404 | Job ID not found |
| `TIMEOUT` | 504 | Command timed out |
| `INVALID_REQUEST` | 400 | Malformed request |

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
├── __init__.py           # Entry point, route registration
├── api/
│   ├── routes.py         # Route definitions
│   └── handlers/
│       ├── nodes.py      # Node management endpoints
│       ├── snapshots.py  # Snapshot endpoints
│       └── jobs.py       # Job tracking endpoints
├── cm_cli/
│   └── executor.py       # cm-cli subprocess execution
├── config/
│   └── config.json       # Configuration file
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

### Adding New Endpoints

1. Add handler method in `api/handlers/*.py`
2. Register route in `api/routes.py`
3. Update this README

## Troubleshooting

### cm-cli Not Found

**Error**: `CM_CLI_NOT_FOUND`

**Solution**: Ensure ComfyUI-Manager is installed in `custom_nodes/ComfyUI-Manager/`

### Port Conflicts

This extension uses ComfyUI's built-in server (default: 8188). No separate port needed.

### Timeout Errors

Increase `timeout` in `config/config.json` for slow operations.

## Security Considerations

- **API Key**: Set `api_key` in config if exposing externally
- **Input Sanitization**: All inputs validated before subprocess execution
- **Path Traversal**: Working directory locked to ComfyUI root

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

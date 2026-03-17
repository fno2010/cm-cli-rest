# comfy-cli REST API Documentation

This document describes the comfy-cli REST API endpoints added to cm-cli-rest.

## Overview

The comfy-cli REST API provides endpoints for managing ComfyUI through the `comfy-cli` command-line tool. All endpoints are prefixed with `/comfy-cli/`.

## API Endpoints

### Configuration

#### GET `/comfy-cli/config/env`

Get environment configuration.

**Response:**
```json
{
  "success": true,
  "data": {
    "default_workspace": "/basedir",
    "recent_workspace": "/basedir",
    "launch_extras": "--listen 0.0.0.0 --port 8188",
    "enable_tracking": false
  },
  "raw_output": "Default Workspace: /basedir\n..."
}
```

#### GET `/comfy-cli/config/which`

Get current workspace path.

**Response:**
```json
{
  "success": true,
  "data": {
    "workspace_path": "/basedir",
    "comfyui_path": "/basedir/ComfyUI",
    "is_default": true
  }
}
```

#### POST `/comfy-cli/config/set-default`

Set default workspace path.

**Request:**
```json
{
  "path": "/basedir",
  "launch_extras": "--listen 0.0.0.0 --port 8188"
}
```

### Model Management

#### GET `/comfy-cli/model/list`

List models in directory.

**Query Parameters:**
- `relative_path` (optional): Relative path to models directory (default: `models/checkpoints`)
- `method` (optional): `cli` or `fs` (default: `fs` for filesystem access)

**Response:**
```json
{
  "success": true,
  "data": {
    "path": "models/checkpoints",
    "absolute_path": "/basedir/models/checkpoints",
    "models": [
      {
        "filename": "sd_xl_base_1.0.safetensors",
        "size": 6200000000,
        "size_human": "5.8 GB",
        "modified": "2026-03-15T10:30:00Z"
      }
    ],
    "count": 1
  }
}
```

#### POST `/comfy-cli/model/download`

Download model file (async operation).

**Request:**
```json
{
  "url": "https://civitai.com/models/43331",
  "relative_path": "models/checkpoints",
  "filename": "my_model.safetensors",
  "civitai_api_token": "optional_token"
}
```

**Response (202 Accepted):**
```json
{
  "success": true,
  "job_id": "abc12345",
  "status": "running",
  "message": "Download started",
  "data": {
    "url": "https://civitai.com/models/43331",
    "target_path": "/basedir/models/checkpoints/my_model.safetensors"
  }
}
```

#### GET `/comfy-cli/model/download/{job_id}/status`

Get download job status.

**Response:**
```json
{
  "success": true,
  "data": {
    "job_id": "abc12345",
    "status": "running",
    "progress": 45,
    "parsed_output": {
      "status": "downloading",
      "progress": 45
    }
  }
}
```

#### POST `/comfy-cli/model/remove`

Remove model file(s).

**Request:**
```json
{
  "relative_path": "models/checkpoints",
  "model_names": ["old_model.safetensors"],
  "confirm": true
}
```

### Node Management

#### GET `/comfy-cli/node/simple-show`

Show node list (simplified format).

**Query Parameters:**
- `mode`: `installed`, `enabled`, `disabled`, `not-installed`, `all`

**Response:**
```json
{
  "success": true,
  "data": {
    "mode": "installed",
    "nodes": ["ComfyUI-Impact-Pack", "ComfyUI-Manager"],
    "total_count": 2
  }
}
```

#### GET `/comfy-cli/node/show`

Show node details.

**Query Parameters:**
- `mode`: `installed`, `enabled`, `disabled`, `all`

**Response:**
```json
{
  "success": true,
  "data": {
    "mode": "installed",
    "nodes": [
      {
        "name": "ComfyUI-Impact-Pack",
        "author": "ltdrdata",
        "version": "v5.12.1",
        "status": "enabled",
        "requirements": ["opencv-python", "pillow"]
      }
    ]
  }
}
```

#### POST `/comfy-cli/node/install`

Install node(s) (async operation).

**Request:**
```json
{
  "nodes": ["ComfyUI-Impact-Pack"],
  "fast_deps": true,
  "channel": "recent"
}
```

**Response (202 Accepted):**
```json
{
  "success": true,
  "job_id": "node-install-456",
  "status": "running",
  "message": "Installing 1 node(s)",
  "data": {
    "nodes": ["ComfyUI-Impact-Pack"]
  }
}
```

#### POST `/comfy-cli/node/update`

Update node(s) (async operation).

**Request:**
```json
{
  "target": "all",
  "channel": "recent",
  "mode": "remote"
}
```

#### POST `/comfy-cli/node/enable`

Enable node.

**Request:**
```json
{
  "node": "ComfyUI-Impact-Pack"
}
```

#### POST `/comfy-cli/node/disable`

Disable node.

**Request:**
```json
{
  "node": "ComfyUI-Impact-Pack"
}
```

#### POST `/comfy-cli/node/uninstall`

Uninstall node.

**Request:**
```json
{
  "node": "ComfyUI-Impact-Pack",
  "confirm": true
}
```

## Error Responses

All errors follow this format:

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

### Common Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `COMFY_CLI_ERROR` | 500 | comfy-cli execution failed |
| `COMMAND_FAILED` | 500 | CLI command returned non-zero exit code |
| `MISSING_PARAMETER` | 400 | Required parameter missing |
| `INVALID_PARAMETER` | 400 | Invalid parameter value |
| `JOB_NOT_FOUND` | 404 | Async job ID not found |
| `INTERNAL_ERROR` | 500 | Unexpected server error |

## Usage Examples

### List Models

```bash
curl "http://localhost:8188/comfy-cli/model/list?relative_path=models/checkpoints"
```

### Download Model

```bash
curl -X POST "http://localhost:8188/comfy-cli/model/download" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://civitai.com/models/43331",
    "relative_path": "models/checkpoints"
  }'
```

### Check Download Status

```bash
curl "http://localhost:8188/comfy-cli/model/download/abc12345/status"
```

### List Installed Nodes

```bash
curl "http://localhost:8188/comfy-cli/node/simple-show?mode=installed"
```

### Install Node

```bash
curl -X POST "http://localhost:8188/comfy-cli/node/install" \
  -H "Content-Type: application/json" \
  -d '{
    "nodes": ["ComfyUI-Impact-Pack"],
    "fast_deps": true
  }'
```

## Architecture

```
ComfyUI Server (aiohttp)
    ├── /cm-cli-rest/* (cm-cli API)
    └── /comfy-cli/* (comfy-cli API)
            ├── ConfigHandler
            ├── ModelHandler
            └── NodeHandler
                    └── ComfyCliExecutor
                            └── comfy-cli (subprocess)
```

## Notes

1. **Async Operations**: Long-running operations (download, install, update) return immediately with a `job_id`. Use the status endpoint to poll for completion.

2. **Filesystem Access**: Model list uses direct filesystem access by default (`method=fs`) for more reliable results. Use `method=cli` to invoke comfy-cli directly.

3. **Workspace Configuration**: All commands use the workspace path configured during initialization. Default is the ComfyUI root directory.

4. **Error Handling**: All errors return structured JSON responses with appropriate HTTP status codes.

## Requirements

- comfy-cli installed and in PATH (`pip install comfy-cli`)
- ComfyUI workspace configured

# comfy-cli API Reference

> 文档版本：1.0
> 最后更新：2026-03-16
> 基于 comfy-cli v1.6.0
> 适用环境：ComfyUI-Nvidia-Docker

本文档详细描述 comfy-cli 所有命令的输入输出格式，用于 REST API 集成开发。

---

## 目录

1. [概述](#1-概述)
2. [通用约定](#2-通用约定)
3. [配置命令](#3-配置命令)
4. [模型管理命令](#4-模型管理命令)
5. [节点管理命令](#5-节点管理命令)
6. [ComfyUI 管理命令](#6-comfyui-管理命令)
7. [Workflow 执行命令](#7-workflow-执行命令)
8. [输出解析指南](#8-输出解析指南)
9. [REST API 集成示例](#9-rest-api-集成示例)

---

## 1. 概述

### 1.1 命令分类

| 类别 | 命令前缀 | 典型用途 |
|------|----------|----------|
| 配置 | `comfy` | 工作区设置、环境查询 |
| 模型 | `comfy model` | 下载、列表、删除模型 |
| 节点 | `comfy node` | 安装、更新、管理自定义节点 |
| ComfyUI | `comfy install/update/launch` | ComfyUI 生命周期管理 |
| Workflow | `comfy run` | 执行 workflow |

### 1.2 执行模式

| 模式 | 说明 | 适用命令 |
|------|------|----------|
| 同步 | 等待命令完成，返回完整输出 | `model list`, `node simple-show` |
| 异步 | 启动任务后立即返回，需轮询状态 | `model download`, `node install` |

---

## 2. 通用约定

### 2.1 基础命令格式

```bash
comfy [GLOBAL_OPTIONS] COMMAND [SUBCOMMAND] [OPTIONS]
```

### 2.2 全局选项

| 选项 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `--workspace PATH` | string | - | 指定工作区路径 |
| `--recent` | flag | false | 使用最近的工作区 |
| `--here` | flag | false | 使用当前目录 |
| `--version` | flag | false | 显示版本号 |
| `--help` | flag | false | 显示帮助 |

### 2.3 通用响应结构（REST API）

```json
{
  "success": true,
  "data": { ... },
  "error": null,
  "job_id": "uuid-optional",
  "raw_output": "原始 CLI 输出",
  "parsed_output": { ... }
}
```

### 2.4 错误响应结构

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "人类可读的错误描述",
    "details": { ... }
  },
  "job_id": null
}
```

### 2.5 常见错误码

| 错误码 | HTTP 状态 | 说明 |
|--------|-----------|------|
| `INVALID_WORKSPACE` | 400 | 工作区路径无效 |
| `MISSING_PARAMETER` | 400 | 缺少必需参数 |
| `COMMAND_FAILED` | 500 | CLI 命令执行失败 |
| `JOB_NOT_FOUND` | 404 | 异步任务 ID 不存在 |
| `ALREADY_RUNNING` | 409 | 任务已在运行中 |

---

## 3. 配置命令

### 3.1 `comfy set-default`

设置默认工作区路径。

**CLI 格式：**
```bash
comfy set-default PATH [--launch-extras "ARGS"]
```

**参数：**
| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `PATH` | string | 是 | 工作区路径 |
| `--launch-extras` | string | 否 | 默认启动参数 |

**REST API 请求：**
```json
POST /comfy-cli/config/set-default
{
  "path": "/basedir",
  "launch_extras": "--listen 0.0.0.0 --port 8188"
}
```

**成功响应：**
```json
{
  "success": true,
  "data": {
    "default_workspace": "/basedir",
    "config_file": "/root/.config/comfy-cli/config.ini"
  },
  "raw_output": "Default workspace set to /basedir"
}
```

**失败响应（Docker 环境）：**
```json
{
  "success": false,
  "error": {
    "code": "INVALID_WORKSPACE",
    "message": "Specified path is not a ComfyUI path: /basedir",
    "details": {
      "reason": "git_repo_not_found",
      "suggestion": "Use direct config.ini modification instead"
    }
  }
}
```

---

### 3.2 `comfy which`

显示当前选中的 ComfyUI 路径。

**CLI 格式：**
```bash
comfy which
```

**REST API 请求：**
```json
GET /comfy-cli/config/which
```

**成功响应：**
```json
{
  "success": true,
  "data": {
    "workspace_path": "/basedir",
    "comfyui_path": "/basedir/ComfyUI",
    "is_default": true
  },
  "raw_output": "/basedir"
}
```

---

### 3.3 `comfy env`

打印环境信息。

**CLI 格式：**
```bash
comfy env
```

**REST API 请求：**
```json
GET /comfy-cli/config/env
```

**成功响应：**
```json
{
  "success": true,
  "data": {
    "default_workspace": "/basedir",
    "recent_workspace": "/basedir",
    "launch_extras": "--listen 0.0.0.0 --port 8188",
    "enable_tracking": false,
    "civitai_api_token": "set",
    "hf_api_token": "not_set",
    "background_process": null
  },
  "raw_output": "Default Workspace: /basedir\n..."
}
```

---

## 4. 模型管理命令

### 4.1 `comfy model download`

下载模型文件。

**CLI 格式：**
```bash
comfy model download \
  --url URL \
  [--relative-path PATH] \
  [--filename NAME] \
  [--set-civitai-api-token TOKEN] \
  [--set-hf-api-token TOKEN]
```

**参数：**
| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| `--url` | string | 是 | - | 模型下载 URL |
| `--relative-path` | string | 否 | `models/checkpoints` | 保存相对路径 |
| `--filename` | string | 否 | 自动 | 保存文件名 |
| `--set-civitai-api-token` | string | 否 | - | CivitAI API Token |
| `--set-hf-api-token` | string | 否 | - | HuggingFace API Token |

**REST API 请求：**
```json
POST /comfy-cli/model/download
{
  "url": "https://civitai.com/models/43331",
  "relative_path": "models/checkpoints",
  "filename": "my_model.safetensors",
  "civitai_api_token": "optional_token"
}
```

**异步响应（202 Accepted）：**
```json
{
  "success": true,
  "job_id": "abc-123-def",
  "status": "running",
  "message": "Download started",
  "data": {
    "url": "https://civitai.com/models/43331",
    "target_path": "/basedir/models/checkpoints/my_model.safetensors"
  }
}
```

**完成响应（轮询 job_id）：**
```json
{
  "success": true,
  "job_id": "abc-123-def",
  "status": "completed",
  "data": {
    "downloaded_file": "/basedir/models/checkpoints/my_model.safetensors",
    "file_size": "2.1 GB",
    "download_time": "45s"
  },
  "parsed_output": {
    "status": "success",
    "path": "models/checkpoints/my_model.safetensors",
    "size_bytes": 2254857830
  }
}
```

**失败响应：**
```json
{
  "success": false,
  "job_id": "abc-123-def",
  "status": "failed",
  "error": {
    "code": "DOWNLOAD_FAILED",
    "message": "HTTP 401: Unauthorized",
    "details": {
      "reason": "missing_api_token",
      "url": "https://civitai.com/models/43331"
    }
  }
}
```

---

### 4.2 `comfy model list`

列出模型文件。

**CLI 格式：**
```bash
comfy model list \
  [--relative-path PATH]
```

**参数：**
| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| `--relative-path` | string | 否 | `models` | 列出目录 |

**REST API 请求：**
```json
GET /comfy-cli/model/list?relative_path=models/checkpoints
```

**成功响应：**
```json
{
  "success": true,
  "data": {
    "path": "models/checkpoints",
    "absolute_path": "/basedir/models/checkpoints",
    "models": [
      {
        "filename": "sd_xl_base_1.0.safetensors",
        "size": "6.2 GB",
        "modified": "2026-03-15T10:30:00Z"
      },
      {
        "filename": "realistic_vision_v5.safetensors",
        "size": "2.1 GB",
        "modified": "2026-03-14T08:15:00Z"
      }
    ],
    "total_count": 2,
    "total_size": "8.3 GB"
  },
  "raw_output": "sd_xl_base_1.0.safetensors\nrealistic_vision_v5.safetensors",
  "parsed_output": {
    "models": ["sd_xl_base_1.0.safetensors", "realistic_vision_v5.safetensors"]
  }
}
```

**空目录响应：**
```json
{
  "success": true,
  "data": {
    "path": "models/checkpoints",
    "models": [],
    "total_count": 0
  },
  "raw_output": "",
  "parsed_output": {
    "models": []
  }
}
```

---

### 4.3 `comfy model remove`

删除模型文件。

**CLI 格式：**
```bash
comfy model remove \
  --relative-path PATH \
  --model-names NAME1 [NAME2 ...] \
  [--confirm]
```

**参数：**
| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| `--relative-path` | string | 否 | `models/checkpoints` | 模型目录 |
| `--model-names` | string[] | 是 | - | 模型文件名列表 |
| `--confirm` | flag | 否 | false | 跳过确认提示 |

**REST API 请求：**
```json
POST /comfy-cli/model/remove
{
  "relative_path": "models/checkpoints",
  "model_names": ["old_model.safetensors"],
  "confirm": true
}
```

**成功响应：**
```json
{
  "success": true,
  "data": {
    "removed": ["old_model.safetensors"],
    "count": 1,
    "freed_space": "2.1 GB"
  },
  "raw_output": "Successfully removed 1 model(s)"
}
```

**失败响应（文件不存在）：**
```json
{
  "success": false,
  "error": {
    "code": "FILE_NOT_FOUND",
    "message": "Model not found: old_model.safetensors",
    "details": {
      "path": "/basedir/models/checkpoints/old_model.safetensors"
    }
  }
}
```

---

## 5. 节点管理命令

### 5.1 `comfy node simple-show`

显示节点列表（简化格式）。

**CLI 格式：**
```bash
comfy node simple-show {installed|enabled|disabled|not-installed|all}
```

**参数：**
| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `mode` | string | 是 | `installed`, `enabled`, `disabled`, `not-installed`, `all` |

**REST API 请求：**
```json
GET /comfy-cli/node/simple-show?mode=installed
```

**成功响应：**
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
        "path": "/basedir/custom_nodes/ComfyUI-Impact-Pack"
      },
      {
        "name": "ComfyUI-Manager",
        "author": "ltdrdata",
        "version": "v2.45.0",
        "status": "enabled",
        "path": "/basedir/custom_nodes/ComfyUI-Manager"
      }
    ],
    "total_count": 2
  },
  "raw_output": "ComfyUI-Impact-Pack\nComfyUI-Manager",
  "parsed_output": {
    "node_names": ["ComfyUI-Impact-Pack", "ComfyUI-Manager"]
  }
}
```

---

### 5.2 `comfy node show`

显示节点详细信息。

**CLI 格式：**
```bash
comfy node show {installed|enabled|disabled|all}
```

**REST API 请求：**
```json
GET /comfy-cli/node/show?mode=installed
```

**成功响应：**
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
        "path": "/basedir/custom_nodes/ComfyUI-Impact-Pack",
        "requirements": ["opencv-python", "pillow"],
        "git_url": "https://github.com/ltdrdata/ComfyUI-Impact-Pack"
      }
    ]
  }
}
```

---

### 5.3 `comfy node install`

安装自定义节点。

**CLI 格式：**
```bash
comfy node install NODE_NAME [NODE_NAME2 ...] \
  [--fast-deps] \
  [--no-deps] \
  [--channel CHANNEL]
```

**参数：**
| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| `NODE_NAME` | string[] | 是 | - | 节点名称（可多个） |
| `--fast-deps` | flag | 否 | false | 快速依赖安装 |
| `--no-deps` | flag | 否 | false | 跳过依赖安装 |
| `--channel` | string | 否 | `recent` | 节点频道 |

**REST API 请求：**
```json
POST /comfy-cli/node/install
{
  "nodes": ["ComfyUI-Impact-Pack"],
  "fast_deps": true,
  "no_deps": false,
  "channel": "recent"
}
```

**异步响应（202 Accepted）：**
```json
{
  "success": true,
  "job_id": "node-install-456",
  "status": "running",
  "message": "Installing 1 node(s)",
  "data": {
    "nodes": ["ComfyUI-Impact-Pack"],
    "estimated_time": "60s"
  }
}
```

**完成响应：**
```json
{
  "success": true,
  "job_id": "node-install-456",
  "status": "completed",
  "data": {
    "installed": ["ComfyUI-Impact-Pack"],
    "failed": [],
    "dependencies_installed": ["opencv-python", "pillow"]
  }
}
```

---

### 5.4 `comfy node update`

更新节点。

**CLI 格式：**
```bash
comfy node update {all|NODE_NAME} \
  [--channel CHANNEL] \
  [--mode MODE]
```

**参数：**
| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| `target` | string | 是 | - | `all` 或节点名 |
| `--channel` | string | 否 | `recent` | 节点频道 |
| `--mode` | string | 否 | `remote` | 更新模式 |

**REST API 请求：**
```json
POST /comfy-cli/node/update
{
  "target": "all",
  "channel": "recent",
  "mode": "remote"
}
```

**成功响应：**
```json
{
  "success": true,
  "data": {
    "updated": ["ComfyUI-Impact-Pack"],
    "unchanged": ["ComfyUI-Manager"],
    "failed": []
  }
}
```

---

### 5.5 `comfy node enable/disable`

启用/禁用节点。

**CLI 格式：**
```bash
comfy node enable NODE_NAME
comfy node disable NODE_NAME
```

**REST API 请求：**
```json
POST /comfy-cli/node/enable
{"node": "ComfyUI-Impact-Pack"}

POST /comfy-cli/node/disable
{"node": "ComfyUI-Impact-Pack"}
```

**成功响应：**
```json
{
  "success": true,
  "data": {
    "node": "ComfyUI-Impact-Pack",
    "action": "enabled",
    "path": "/basedir/custom_nodes/ComfyUI-Impact-Pack"
  }
}
```

---

### 5.6 `comfy node uninstall`

卸载节点。

**CLI 格式：**
```bash
comfy node uninstall NODE_NAME
```

**REST API 请求：**
```json
POST /comfy-cli/node/uninstall
{"node": "ComfyUI-Impact-Pack"}
```

---

### 5.7 `comfy node save-snapshot`

保存当前节点快照。

**CLI 格式：**
```bash
comfy node save-snapshot [--output FILENAME]
```

**REST API 请求：**
```json
POST /comfy-cli/node/save-snapshot
{"output": "backup-2026-03-16.json"}
```

**成功响应：**
```json
{
  "success": true,
  "data": {
    "snapshot_file": "/basedir/custom_nodes/snapshot/backup-2026-03-16.json",
    "nodes_count": 5,
    "created_at": "2026-03-16T14:30:00Z"
  }
}
```

---

### 5.8 `comfy node restore-snapshot`

恢复节点快照。

**CLI 格式：**
```bash
comfy node restore-snapshot SNAPSHOT_FILE [--retry]
```

**REST API 请求：**
```json
POST /comfy-cli/node/restore-snapshot
{
  "snapshot_file": "backup-2026-03-16.json",
  "retry": true
}
```

---

## 6. ComfyUI 管理命令

### 6.1 `comfy install`

安装 ComfyUI。

**CLI 格式：**
```bash
comfy install \
  [--version VERSION] \
  [--nvidia|amd|cpu] \
  [--skip-manager] \
  [--pr PR_NUMBER]
```

**REST API 请求：**
```json
POST /comfy-cli/comfyui/install
{
  "version": "latest",
  "gpu_type": "nvidia",
  "skip_manager": false
}
```

---

### 6.2 `comfy launch`

启动 ComfyUI。

**CLI 格式：**
```bash
comfy launch \
  [--background] \
  [-- ARGS...]
```

**REST API 请求：**
```json
POST /comfy-cli/comfyui/launch
{
  "background": true,
  "extra_args": ["--listen", "0.0.0.0", "--port", "8188"]
}
```

---

### 6.3 `comfy update`

更新 ComfyUI。

**CLI 格式：**
```bash
comfy update {comfy|all}
```

**REST API 请求：**
```json
POST /comfy-cli/comfyui/update
{"target": "comfy"}
```

---

## 7. Workflow 执行命令

### 7.1 `comfy run`

执行 workflow 文件。

**CLI 格式：**
```bash
comfy run \
  --workflow WORKFLOW_FILE \
  [--wait] \
  [--verbose] \
  [--host HOST] \
  [--port PORT] \
  [--timeout SECONDS]
```

**参数：**
| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| `--workflow` | string | 是 | - | Workflow JSON 文件路径 |
| `--wait` | flag | 否 | false | 等待完成 |
| `--verbose` | flag | 否 | false | 详细输出 |
| `--host` | string | 否 | `127.0.0.1` | ComfyUI 主机 |
| `--port` | int | 否 | `8188` | ComfyUI 端口 |
| `--timeout` | int | 否 | `60` | 超时秒数 |

**REST API 请求：**
```json
POST /comfy-cli/workflow/run
{
  "workflow_path": "/basedir/workflows/my_workflow.json",
  "wait": true,
  "timeout": 300,
  "parameters": {
    "prompt": "a cat",
    "steps": 30
  }
}
```

**异步响应：**
```json
{
  "success": true,
  "job_id": "workflow-789",
  "prompt_id": "comfyui-prompt-uuid",
  "status": "queued"
}
```

**完成响应：**
```json
{
  "success": true,
  "job_id": "workflow-789",
  "prompt_id": "comfyui-prompt-uuid",
  "status": "completed",
  "data": {
    "outputs": [
      {
        "type": "image",
        "filename": "ComfyUI_00001.png",
        "path": "/basedir/output/ComfyUI_00001.png",
        "url": "/view?filename=ComfyUI_00001.png&type=output"
      }
    ],
    "execution_time": "12.5s"
  }
}
```

---

## 8. 输出解析指南

### 8.1 CLI 原始输出类型

| 命令 | 原始输出格式 | 解析难度 |
|------|-------------|----------|
| `model list` | 每行一个文件名 | 简单 |
| `node simple-show` | 每行一个节点名 | 简单 |
| `node show` | 多行详细信息 | 中等 |
| `model download` | 进度 + 完成消息 | 复杂 |
| `env` | 键值对列表 | 中等 |

### 8.2 解析建议

#### 简单列表输出（`model list`, `node simple-show`）

```python
def parse_list_output(raw: str) -> List[str]:
    """解析每行一个项目的输出"""
    if not raw.strip():
        return []
    return [line.strip() for line in raw.strip().split('\n') if line.strip()]
```

#### 键值对输出（`env`）

```python
def parse_env_output(raw: str) -> Dict[str, Any]:
    """解析键值对输出"""
    result = {}
    for line in raw.strip().split('\n'):
        if ':' in line:
            key, value = line.split(':', 1)
            result[key.strip().lower().replace(' ', '_')] = value.strip()
    return result
```

#### 进度输出（`model download`）

```python
import re

def parse_download_progress(raw: str) -> Dict[str, Any]:
    """解析下载进度"""
    result = {"status": "unknown", "progress": 0}

    # 匹配进度行
    progress_match = re.search(r'(\d+)%', raw)
    if progress_match:
        result["progress"] = int(progress_match.group(1))
        result["status"] = "downloading"

    # 匹配完成
    if "Successfully downloaded" in raw or "Download complete" in raw:
        result["status"] = "completed"
        result["progress"] = 100

    # 匹配错误
    if "Error" in raw or "Failed" in raw:
        result["status"] = "failed"

    return result
```

### 8.3 推荐：直接文件系统操作

对于某些命令，直接操作文件系统比解析 CLI 输出更可靠：

```python
# 替代 comfy model list
def list_models_direct(workspace: str, relative_path: str) -> List[Dict]:
    """直接读取文件系统获取模型列表"""
    import os
    from pathlib import Path

    full_path = Path(workspace) / relative_path
    if not full_path.exists():
        return []

    models = []
    for f in full_path.iterdir():
        if f.is_file() and f.suffix in ['.safetensors', '.ckpt', '.pt']:
            models.append({
                "filename": f.name,
                "size": f.stat().st_size,
                "modified": f.stat().st_mtime
            })
    return models
```

---

## 9. REST API 集成示例

### 9.1 完整 Handler 示例

```python
# handlers/models.py
from aiohttp import web
import subprocess
import json
from pathlib import Path

class ModelHandler:
    def __init__(self, workspace: str = "/basedir"):
        self.workspace = Path(workspace)

    async def list_models(self, request: web.Request) -> web.Response:
        """列出模型（带解析）"""
        relative_path = request.query.get("relative_path", "models/checkpoints")

        try:
            # 方法 1：调用 CLI 并解析
            cmd = ["comfy", "--workspace", str(self.workspace),
                   "model", "list", "--relative-path", relative_path]

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                return web.json_response({
                    "success": False,
                    "error": {"code": "CLI_ERROR", "message": stderr.decode()}
                }, status=500)

            # 解析输出
            raw_output = stdout.decode().strip()
            models = [line.strip() for line in raw_output.split('\n') if line.strip()]

            # 增强：获取文件详细信息
            models_detail = []
            full_path = self.workspace / relative_path
            for model in models:
                model_path = full_path / model
                if model_path.exists():
                    stat = model_path.stat()
                    models_detail.append({
                        "filename": model,
                        "size": stat.st_size,
                        "size_human": self._format_size(stat.st_size),
                        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
                    })

            return web.json_response({
                "success": True,
                "data": {
                    "path": relative_path,
                    "models": models_detail,
                    "total_count": len(models_detail)
                },
                "raw_output": raw_output,
                "parsed_output": {"models": models}
            })

        except Exception as e:
            return web.json_response({
                "success": False,
                "error": {"code": "INTERNAL_ERROR", "message": str(e)}
            }, status=500)

    async def download_model(self, request: web.Request) -> web.Response:
        """下载模型（异步）"""
        try:
            data = await request.json()
            url = data.get("url")

            if not url:
                return web.json_response({
                    "success": False,
                    "error": {"code": "MISSING_URL", "message": "URL is required"}
                }, status=400)

            # 构建命令
            cmd = ["comfy", "--workspace", str(self.workspace),
                   "model", "download", "--url", url]

            if data.get("relative_path"):
                cmd.extend(["--relative-path", data["relative_path"]])
            if data.get("filename"):
                cmd.extend(["--filename", data["filename"]])
            if data.get("civitai_api_token"):
                cmd.extend(["--set-civitai-api-token", data["civitai_api_token"]])

            # 异步执行
            job_id = str(uuid.uuid4())
            task = asyncio.create_task(self._run_download(job_id, cmd))

            # 存储任务
            self.jobs[job_id] = {
                "status": "running",
                "task": task,
                "created_at": datetime.utcnow().isoformat()
            }

            return web.json_response({
                "success": True,
                "job_id": job_id,
                "status": "running",
                "message": "Download started"
            }, status=202)

        except Exception as e:
            return web.json_response({
                "success": False,
                "error": {"code": "INTERNAL_ERROR", "message": str(e)}
            }, status=500)

    async def _run_download(self, job_id: str, cmd: List[str]):
        """后台运行下载任务"""
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()

            if process.returncode == 0:
                self.jobs[job_id] = {
                    "status": "completed",
                    "output": stdout.decode(),
                    "error": None
                }
            else:
                self.jobs[job_id] = {
                    "status": "failed",
                    "output": stdout.decode(),
                    "error": stderr.decode()
                }
        except Exception as e:
            self.jobs[job_id] = {
                "status": "failed",
                "error": str(e)
            }

    def _format_size(self, bytes: int) -> str:
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes < 1024:
                return f"{bytes:.1f} {unit}"
            bytes /= 1024
        return f"{bytes:.1f} TB"
```

### 9.2 路由注册

```python
# routes.py
from aiohttp import web
from handlers.models import ModelHandler
from handlers.nodes import NodeHandler

model_handler = ModelHandler(workspace="/basedir")
node_handler = NodeHandler(workspace="/basedir")

def setup_routes(app):
    # 模型管理
    app.router.add_get("/comfy-cli/model/list", model_handler.list_models)
    app.router.add_post("/comfy-cli/model/download", model_handler.download_model)
    app.router.add_post("/comfy-cli/model/remove", model_handler.remove_model)

    # 节点管理
    app.router.add_get("/comfy-cli/node/simple-show", node_handler.simple_show)
    app.router.add_post("/comfy-cli/node/install", node_handler.install)
    app.router.add_post("/comfy-cli/node/update", node_handler.update)

    # 任务状态
    app.router.add_get("/comfy-cli/jobs/{job_id}", get_job_status)
```

---

## 附录 A：完整命令列表

```
comfy
├── install              # 安装 ComfyUI
├── update               # 更新 ComfyUI/节点
│   ├── comfy
│   └── all
├── launch               # 启动 ComfyUI
├── stop                 # 停止后台 ComfyUI
├── set-default          # 设置默认工作区
├── which                # 显示当前工作区
├── env                  # 显示环境信息
├── model                # 模型管理
│   ├── download
│   ├── list
│   └── remove
├── node                 # 节点管理
│   ├── install
│   ├── uninstall
│   ├── update
│   ├── enable
│   ├── disable
│   ├── show
│   ├── simple-show
│   ├── save-snapshot
│   ├── restore-snapshot
│   └── deps-in-workflow
└── run                  # 执行 workflow
```

---

## 附录 B：模型类型映射

| comfy-cli 路径 | ComfyUI 模型类型 |
|---------------|-----------------|
| `models/checkpoints` | 主模型检查点 |
| `models/loras` | LoRA 模型 |
| `models/vae` | VAE 模型 |
| `models/embeddings` | Textual Inversion |
| `models/controlnet` | ControlNet 模型 |
| `models/upscale_models` | 放大模型 |
| `models/clip_vision` | CLIP Vision 模型 |
| `models/diffusers` | Diffusers 模型 |

---

*由 Zero (零号) 生成 | 2026-03-16*

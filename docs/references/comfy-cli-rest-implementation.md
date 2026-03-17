# comfy-cli REST API 实现指南

> 文档版本：1.0
> 最后更新：2026-03-16
> 目标：将 comfy-cli 命令转换为结构化 REST API

---

## 1. 架构设计

### 1.1 为什么需要 REST API？

| 问题 | CLI 直接调用 | REST API |
|------|-------------|----------|
| 输出格式 | 原始文本，需解析 | 结构化 JSON |
| 异步任务 | 需手动管理进程 | 统一任务队列 |
| 错误处理 | 退出码 + stderr | 统一错误响应 |
| 认证授权 | 无 | 可集成 |
| 并发控制 | 无 | 可限制 |

### 1.2 设计原则

1. **CLI 作为实现细节**：外部调用者不应直接依赖 CLI 输出格式
2. **结构化响应**：所有响应都是 JSON，包含 `success`, `data`, `error`
3. **异步任务统一处理**：长时间运行的命令返回 `job_id`
4. **解析层隔离**：CLI 输出解析在内部完成，不暴露给调用者

### 1.3 系统架构

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐     ┌──────────┐
│   Client    │────▶│  REST API    │────▶│  Executor   │────▶│ comfy-cli│
│  (Browser/  │◀────│   Server     │◀────│   (Python)  │◀────│  (CLI)  │
│   App)      │     │  (aiohttp)   │     │             │     │          │
└─────────────┘     └──────────────┘     └─────────────┘     └──────────┘
                           │                    │
                           ▼                    ▼
                    ┌──────────────┐     ┌─────────────┐
                    │  Task Queue  │     │  Parsers    │
                    │  (in-memory) │     │  (CLI→JSON) │
                    └──────────────┘     └─────────────┘
```

---

## 2. 项目结构

```
comfy-cli-rest/
├── __init__.py              # 包初始化
├── server.py                # aiohttp 服务器入口
├── config.py                # 配置管理
├── executor.py              # CLI 执行器
├── parsers/                 # 输出解析器
│   ├── __init__.py
│   ├── base.py              # 解析器基类
│   ├── model_parser.py      # 模型命令解析
│   ├── node_parser.py       # 节点命令解析
│   └── env_parser.py        # 环境命令解析
├── handlers/                # API handlers
│   ├── __init__.py
│   ├── models.py            # 模型管理 API
│   ├── nodes.py             # 节点管理 API
│   ├── config.py            # 配置 API
│   └── jobs.py              # 任务管理 API
├── routes.py                # 路由注册
├── middleware.py            # 中间件（认证、日志、错误处理）
├── requirements.txt         # 依赖
└── README.md                # 使用说明
```

---

## 3. 核心组件实现

### 3.1 配置管理 (`config.py`)

```python
from dataclasses import dataclass
from pathlib import Path
import json

@dataclass
class Config:
    workspace: str = "/basedir"
    comfy_cmd: str = "comfy"
    host: str = "0.0.0.0"
    port: int = 8189  # 注意：不是 8188（ComfyUI 端口）
    api_prefix: str = "/comfy-cli"
    max_concurrent_jobs: int = 5
    job_ttl_seconds: int = 3600

    @classmethod
    def from_file(cls, path: str) -> "Config":
        with open(path) as f:
            data = json.load(f)
        return cls(**data)

    @property
    def comfy_args(self) -> list:
        return [self.comfy_cmd, "--workspace", self.workspace]

# 默认配置
DEFAULT_CONFIG = Config()
```

### 3.2 CLI 执行器 (`executor.py`)

```python
import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Dict, Optional, Any, List
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class JobStatus:
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"

@dataclass
class Job:
    id: str
    command: List[str]
    status: str
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    return_code: Optional[int] = None
    error: Optional[str] = None

class ComfyCliExecutor:
    """CLI 命令执行器，管理异步任务"""

    def __init__(self, config: Config):
        self.config = config
        self.jobs: Dict[str, Job] = {}
        self._cleanup_task: Optional[asyncio.Task] = None

    async def start(self):
        """启动执行器（启动清理任务）"""
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())

    async def stop(self):
        """停止执行器"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

    async def execute(
        self,
        command: List[str],
        async_mode: bool = True,
        timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        """执行 CLI 命令"""
        job_id = str(uuid.uuid4())
        full_cmd = self.config.comfy_args + command

        job = Job(
            id=job_id,
            command=full_cmd,
            status=JobStatus.PENDING,
            created_at=datetime.utcnow()
        )
        self.jobs[job_id] = job

        if async_mode:
            # 异步执行，立即返回 job_id
            asyncio.create_task(self._run_job(job, timeout))
            return {
                "job_id": job_id,
                "status": JobStatus.PENDING,
                "message": f"Command queued: {' '.join(command)}"
            }
        else:
            # 同步执行，等待完成
            await self._run_job(job, timeout)
            return self._job_to_response(job)

    async def _run_job(self, job: Job, timeout: Optional[int] = None):
        """后台运行任务"""
        job.status = JobStatus.RUNNING
        job.started_at = datetime.utcnow()

        try:
            process = await asyncio.create_subprocess_exec(
                *job.command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.config.workspace
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout
                )
                job.stdout = stdout.decode('utf-8', errors='replace')
                job.stderr = stderr.decode('utf-8', errors='replace')
                job.return_code = process.returncode
                job.status = (
                    JobStatus.COMPLETED if process.returncode == 0
                    else JobStatus.FAILED
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.communicate()
                job.status = JobStatus.TIMEOUT
                job.error = f"Command timed out after {timeout}s"

        except Exception as e:
            job.status = JobStatus.FAILED
            job.error = str(e)
            logger.exception(f"Job {job.id} failed")

        job.completed_at = datetime.utcnow()

    def _job_to_response(self, job: Job) -> Dict[str, Any]:
        """将任务转换为 API 响应"""
        if job.status == JobStatus.COMPLETED:
            return {
                "job_id": job.id,
                "status": job.status,
                "stdout": job.stdout,
                "stderr": job.stderr,
                "return_code": job.return_code
            }
        elif job.status == JobStatus.FAILED:
            return {
                "job_id": job.id,
                "status": job.status,
                "error": job.error or job.stderr,
                "stdout": job.stdout
            }
        else:
            return {
                "job_id": job.id,
                "status": job.status,
                "message": job.error
            }

    def get_job(self, job_id: str) -> Optional[Job]:
        """获取任务状态"""
        return self.jobs.get(job_id)

    def remove_job(self, job_id: str) -> bool:
        """移除任务"""
        if job_id in self.jobs:
            del self.jobs[job_id]
            return True
        return False

    async def _cleanup_loop(self):
        """定期清理过期任务"""
        while True:
            await asyncio.sleep(60)  # 每分钟清理一次
            now = datetime.utcnow()
            expired = [
                job_id for job_id, job in self.jobs.items()
                if job.completed_at and
                   (now - job.completed_at).total_seconds() > self.config.job_ttl_seconds
            ]
            for job_id in expired:
                del self.jobs[job_id]
            if expired:
                logger.info(f"Cleaned up {len(expired)} expired jobs")
```

### 3.3 解析器基类 (`parsers/base.py`)

```python
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

class ParseError(Exception):
    """解析错误"""
    pass

class BaseParser(ABC):
    """CLI 输出解析器基类"""

    @abstractmethod
    def parse(self, raw_output: str, raw_error: str = "") -> Dict[str, Any]:
        """解析 CLI 输出为结构化数据"""
        pass

    def safe_parse(self, raw_output: str, raw_error: str = "") -> Dict[str, Any]:
        """安全解析，失败时返回原始数据"""
        try:
            return {
                "parsed": self.parse(raw_output, raw_error),
                "parse_success": True
            }
        except ParseError as e:
            return {
                "parsed": {"raw": raw_output},
                "parse_success": False,
                "parse_error": str(e)
            }
```

### 3.4 模型解析器 (`parsers/model_parser.py`)

```python
from .base import BaseParser, ParseError
from typing import List, Dict, Any
from pathlib import Path
import re

class ModelListParser(BaseParser):
    """解析 `comfy model list` 输出"""

    def parse(self, raw_output: str, raw_error: str = "") -> Dict[str, Any]:
        if not raw_output.strip():
            return {"models": [], "count": 0}

        # 每行一个文件名
        models = [
            line.strip()
            for line in raw_output.strip().split('\n')
            if line.strip() and not line.startswith('#')
        ]

        return {
            "models": models,
            "count": len(models)
        }

class ModelDownloadParser(BaseParser):
    """解析 `comfy model download` 输出"""

    def parse(self, raw_output: str, raw_error: str = "") -> Dict[str, Any]:
        result = {
            "status": "unknown",
            "progress": 0,
            "filename": None,
            "path": None
        }

        # 检查错误
        if raw_error:
            result["status"] = "error"
            result["error"] = raw_error.strip()
            return result

        # 检查完成消息
        if "Successfully downloaded" in raw_output:
            result["status"] = "completed"
            result["progress"] = 100

            # 尝试提取文件名
            match = re.search(r'Successfully downloaded (.+) to (.+)', raw_output)
            if match:
                result["filename"] = match.group(1)
                result["path"] = match.group(2)

        # 检查进度
        progress_match = re.search(r'(\d+)%', raw_output)
        if progress_match:
            result["status"] = "downloading"
            result["progress"] = int(progress_match.group(1))

        return result
```

### 3.5 模型 Handler (`handlers/models.py`)

```python
from aiohttp import web
from typing import Dict, Any
import logging
from pathlib import Path

from ..executor import ComfyCliExecutor, JobStatus
from ..parsers.model_parser import ModelListParser, ModelDownloadParser

logger = logging.getLogger(__name__)

class ModelHandler:
    def __init__(self, executor: ComfyCliExecutor, workspace: str = "/basedir"):
        self.executor = executor
        self.workspace = Path(workspace)
        self.list_parser = ModelListParser()
        self.download_parser = ModelDownloadParser()

    async def list_models(self, request: web.Request) -> web.Response:
        """
        GET /comfy-cli/model/list?relative_path=models/checkpoints

        响应：
        {
            "success": true,
            "data": {
                "path": "models/checkpoints",
                "models": [
                    {"filename": "model1.safetensors", "size": 6200000000},
                    ...
                ],
                "count": 5
            }
        }
        """
        relative_path = request.query.get("relative_path", "models/checkpoints")
        use_direct_fs = request.query.get("method", "cli") == "fs"

        try:
            if use_direct_fs:
                # 方法 1：直接文件系统访问（更可靠）
                data = await self._list_models_fs(relative_path)
            else:
                # 方法 2：CLI 调用
                result = await self.executor.execute(
                    ["model", "list", "--relative-path", relative_path],
                    async_mode=False
                )

                if result["status"] != JobStatus.COMPLETED:
                    return web.json_response({
                        "success": False,
                        "error": {"code": "EXECUTION_FAILED", "message": result.get("error")}
                    }, status=500)

                # 解析 CLI 输出
                parsed = self.list_parser.safe_parse(result["stdout"], result.get("stderr", ""))

                # 增强：获取文件详细信息
                models_detail = await self._enhance_models_info(
                    parsed["parsed"].get("models", []),
                    relative_path
                )

                data = {
                    "path": relative_path,
                    "models": models_detail,
                    "count": len(models_detail),
                    "cli_output": parsed
                }

            return web.json_response({
                "success": True,
                "data": data
            })

        except Exception as e:
            logger.exception("list_models failed")
            return web.json_response({
                "success": False,
                "error": {"code": "INTERNAL_ERROR", "message": str(e)}
            }, status=500)

    async def _list_models_fs(self, relative_path: str) -> Dict[str, Any]:
        """直接文件系统方式列出模型"""
        full_path = self.workspace / relative_path

        if not full_path.exists():
            return {"path": relative_path, "models": [], "count": 0, "error": "Path not found"}

        models = []
        for f in full_path.iterdir():
            if f.is_file() and f.suffix in ['.safetensors', '.ckpt', '.pt', '.bin']:
                stat = f.stat()
                models.append({
                    "filename": f.name,
                    "size": stat.st_size,
                    "size_human": self._format_size(stat.st_size),
                    "modified": stat.st_mtime
                })

        return {
            "path": relative_path,
            "absolute_path": str(full_path),
            "models": sorted(models, key=lambda x: x["filename"]),
            "count": len(models)
        }

    async def download_model(self, request: web.Request) -> web.Response:
        """
        POST /comfy-cli/model/download

        请求体：
        {
            "url": "https://...",
            "relative_path": "models/checkpoints",
            "filename": "optional.safetensors",
            "civitai_api_token": "optional"
        }

        响应（202 Accepted）：
        {
            "success": true,
            "job_id": "uuid",
            "status": "pending"
        }
        """
        try:
            data = await request.json()
            url = data.get("url")

            if not url:
                return web.json_response({
                    "success": False,
                    "error": {"code": "MISSING_URL", "message": "url is required"}
                }, status=400)

            # 构建 CLI 命令
            cmd = ["model", "download", "--url", url]

            if data.get("relative_path"):
                cmd.extend(["--relative-path", data["relative_path"]])
            if data.get("filename"):
                cmd.extend(["--filename", data["filename"]])
            if data.get("civitai_api_token"):
                cmd.extend(["--set-civitai-api-token", data["civitai_api_token"]])
            if data.get("hf_api_token"):
                cmd.extend(["--set-hf-api-token", data["hf_api_token"]])

            # 异步执行
            result = await self.executor.execute(cmd, async_mode=True, timeout=1800)

            return web.json_response({
                "success": True,
                "job_id": result["job_id"],
                "status": result["status"],
                "message": result["message"]
            }, status=202)

        except Exception as e:
            logger.exception("download_model failed")
            return web.json_response({
                "success": False,
                "error": {"code": "INTERNAL_ERROR", "message": str(e)}
            }, status=500)

    async def get_download_status(self, request: web.Request) -> web.Response:
        """
        GET /comfy-cli/model/download/{job_id}/status

        响应：
        {
            "success": true,
            "data": {
                "job_id": "uuid",
                "status": "running|completed|failed",
                "progress": 45,
                "parsed_output": {...}
            }
        }
        """
        job_id = request.match_info["job_id"]

        job = self.executor.get_job(job_id)
        if not job:
            return web.json_response({
                "success": False,
                "error": {"code": "JOB_NOT_FOUND", "message": f"Job {job_id} not found"}
            }, status=404)

        response_data = {
            "job_id": job_id,
            "status": job.status,
            "created_at": job.created_at.isoformat(),
        }

        if job.status == JobStatus.RUNNING:
            # 解析进度
            parsed = self.download_parser.safe_parse(job.stdout or "", job.stderr or "")
            response_data["progress"] = parsed["parsed"].get("progress", 0)
            response_data["parsed_output"] = parsed["parsed"]

        elif job.status == JobStatus.COMPLETED:
            parsed = self.download_parser.safe_parse(job.stdout or "", job.stderr or "")
            response_data["parsed_output"] = parsed["parsed"]
            response_data["parse_success"] = parsed["parse_success"]

        elif job.status == JobStatus.FAILED:
            response_data["error"] = job.error or job.stderr

        return web.json_response({
            "success": True,
            "data": response_data
        })

    async def _enhance_models_info(self, model_names: List[str], relative_path: str) -> List[Dict]:
        """增强模型信息（添加文件大小等）"""
        full_path = self.workspace / relative_path
        result = []

        for name in model_names:
            model_file = full_path / name
            if model_file.exists():
                stat = model_file.stat()
                result.append({
                    "filename": name,
                    "size": stat.st_size,
                    "size_human": self._format_size(stat.st_size),
                    "modified": stat.st_mtime
                })
            else:
                result.append({"filename": name, "size": None, "error": "File not found"})

        return result

    def _format_size(self, bytes: int) -> str:
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes < 1024:
                return f"{bytes:.1f} {unit}"
            bytes /= 1024
        return f"{bytes:.1f} TB"
```

---

## 4. 服务器入口 (`server.py`)

```python
from aiohttp import web
import logging
from config import Config, DEFAULT_CONFIG
from executor import ComfyCliExecutor
from handlers.models import ModelHandler
from handlers.nodes import NodeHandler
from handlers.jobs import JobHandler
from routes import setup_routes
from middleware import setup_middleware

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def create_app(config: Config = DEFAULT_CONFIG) -> web.Application:
    """创建应用"""
    app = web.Application()

    # 创建共享组件
    executor = ComfyCliExecutor(config)
    await executor.start()

    # 创建 handlers
    model_handler = ModelHandler(executor, config.workspace)
    node_handler = NodeHandler(executor, config.workspace)
    job_handler = JobHandler(executor)

    # 存储到 app，便于清理
    app['executor'] = executor
    app['handlers'] = {
        'model': model_handler,
        'node': node_handler,
        'job': job_handler
    }

    # 设置中间件
    setup_middleware(app)

    # 设置路由
    setup_routes(app, model_handler, node_handler, job_handler)

    # 生命周期钩子
    app.on_shutdown.append(on_shutdown)

    return app

async def on_shutdown(app: web.Application):
    """清理资源"""
    await app['executor'].stop()

def main():
    app = web.run_app(create_app(), host=DEFAULT_CONFIG.host, port=DEFAULT_CONFIG.port)

if __name__ == '__main__':
    main()
```

---

## 5. 中间件 (`middleware.py`)

```python
from aiohttp import web
import logging
import time
import json

logger = logging.getLogger(__name__)

@web.middleware
async def logging_middleware(request: web.Request, handler):
    """请求日志"""
    start = time.time()
    try:
        response = await handler(request)
        duration = time.time() - start
        logger.info(f"{request.method} {request.path} - {response.status} - {duration:.3f}s")
        return response
    except Exception as e:
        logger.exception(f"{request.method} {request.path} - Error: {e}")
        raise

@web.middleware
async def error_handler_middleware(request: web.Request, handler):
    """统一错误处理"""
    try:
        return await handler(request)
    except web.HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Unhandled error in {request.path}")
        return web.json_response({
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred",
                "details": str(e) if request.app['debug'] else None
            }
        }, status=500)

@web.middleware
async def json_body_middleware(request: web.Request, handler):
    """自动解析 JSON 请求体"""
    if request.content_type == 'application/json':
        try:
            request['json'] = await request.json()
        except json.JSONDecodeError:
            return web.json_response({
                "success": False,
                "error": {"code": "INVALID_JSON", "message": "Invalid JSON in request body"}
            }, status=400)
    return await handler(request)

def setup_middleware(app: web.Application):
    app.middlewares.append(logging_middleware)
    app.middlewares.append(error_handler_middleware)
    app.middlewares.append(json_body_middleware)
```

---

## 6. 使用示例

### 6.1 启动服务器

```bash
# 安装依赖
pip install aiohttp

# 启动
python -m comfy_cli_rest.server

# 或使用配置
python -c "
from comfy_cli_rest.server import create_app
from comfy_cli_rest.config import Config
from aiohttp import web

config = Config.from_file('config.json')
app = create_app(config)
web.run_app(app, host=config.host, port=config.port)
"
```

### 6.2 API 调用示例

```bash
# 列出模型
curl "http://localhost:8189/comfy-cli/model/list?relative_path=models/checkpoints"

# 下载模型
curl -X POST "http://localhost:8189/comfy-cli/model/download" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://civitai.com/models/43331",
    "relative_path": "models/checkpoints"
  }'

# 查询任务状态
curl "http://localhost:8189/comfy-cli/jobs/{job_id}"

# 安装节点
curl -X POST "http://localhost:8189/comfy-cli/node/install" \
  -H "Content-Type: application/json" \
  -d '{"nodes": ["ComfyUI-Impact-Pack"]}'
```

### 6.3 Python 客户端

```python
import aiohttp
import asyncio

class ComfyCliClient:
    def __init__(self, base_url: str = "http://localhost:8189"):
        self.base_url = base_url

    async def list_models(self, relative_path: str = "models/checkpoints"):
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/comfy-cli/model/list",
                params={"relative_path": relative_path}
            ) as resp:
                data = await resp.json()
                return data["data"]["models"]

    async def download_model(self, url: str, **kwargs):
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/comfy-cli/model/download",
                json={"url": url, **kwargs}
            ) as resp:
                return await resp.json()

    async def wait_for_job(self, job_id: str, poll_interval: float = 2.0):
        async with aiohttp.ClientSession() as session:
            while True:
                async with session.get(
                    f"{self.base_url}/comfy-cli/jobs/{job_id}"
                ) as resp:
                    data = await resp.json()
                    status = data["data"]["status"]

                    if status in ["completed", "failed", "timeout"]:
                        return data

                    await asyncio.sleep(poll_interval)

# 使用示例
async def main():
    client = ComfyCliClient()

    # 列出模型
    models = await client.list_models()
    print(f"Found {len(models)} models")

    # 下载模型并等待完成
    result = await client.download_model("https://...")
    job_id = result["job_id"]

    final = await client.wait_for_job(job_id)
    print(f"Download {final['data']['status']}")

asyncio.run(main())
```

---

## 7. 部署建议

### 7.1 Docker Compose

```yaml
version: '3.8'

services:
  comfyui:
    image: mmartial/comfyui-nvidia-docker:latest
    container_name: comfyui
    # ... 其他配置

  comfy-cli-rest:
    build: ./comfy-cli-rest
    container_name: comfy-cli-rest
    volumes:
      - ./basedir:/basedir
    environment:
      - COMFY_WORKSPACE=/basedir
      - CIVITAI_API_TOKEN=${CIVITAI_API_TOKEN}
    ports:
      - "8189:8189"
    depends_on:
      - comfyui
```

### 7.2 安全建议

1. **不要暴露到公网**：默认监听 `127.0.0.1`
2. **添加 API 认证**：使用 API key 或 JWT
3. **限制命令白名单**：只允许安全的 CLI 命令
4. **速率限制**：防止滥用

---

*由 Zero (零号) 生成 | 2026-03-16*

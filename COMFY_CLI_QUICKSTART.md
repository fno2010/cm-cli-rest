# comfy-cli REST API - Quick Reference

## 安装要求

```bash
# 安装 comfy-cli
pip install comfy-cli

# 验证安装
comfy --version
```

## API 端点总览

### 配置 (Config)
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/comfy-cli/config/env` | 获取环境配置 |
| `GET` | `/comfy-cli/config/which` | 获取当前工作区路径 |
| `POST` | `/comfy-cli/config/set-default` | 设置默认工作区 |

### 模型管理 (Models)
| Method | Endpoint | Description | Async |
|--------|----------|-------------|-------|
| `GET` | `/comfy-cli/model/list` | 列出模型 | ❌ |
| `POST` | `/comfy-cli/model/download` | 下载模型 | ✅ |
| `GET` | `/comfy-cli/model/download/{job_id}/status` | 获取下载状态 | ❌ |
| `POST` | `/comfy-cli/model/remove` | 删除模型 | ❌ |

### 节点管理 (Nodes)
| Method | Endpoint | Description | Async |
|--------|----------|-------------|-------|
| `GET` | `/comfy-cli/node/simple-show` | 列出节点（简化） | ❌ |
| `GET` | `/comfy-cli/node/show` | 列出节点（详细） | ❌ |
| `POST` | `/comfy-cli/node/install` | 安装节点 | ✅ |
| `POST` | `/comfy-cli/node/update` | 更新节点 | ✅ |
| `POST` | `/comfy-cli/node/enable` | 启用节点 | ❌ |
| `POST` | `/comfy-cli/node/disable` | 禁用节点 | ❌ |
| `POST` | `/comfy-cli/node/uninstall` | 卸载节点 | ❌ |

## 快速示例

### 列出已安装的模型
```bash
curl "http://localhost:8188/comfy-cli/model/list?relative_path=models/checkpoints"
```

### 下载模型
```bash
curl -X POST "http://localhost:8188/comfy-cli/model/download" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://civitai.com/models/43331",
    "relative_path": "models/checkpoints",
    "filename": "my_model.safetensors"
  }'
```

### 检查下载进度
```bash
curl "http://localhost:8188/comfy-cli/model/download/abc12345/status"
```

### 列出已安装的节点
```bash
curl "http://localhost:8188/comfy-cli/node/simple-show?mode=installed"
```

### 安装节点
```bash
curl -X POST "http://localhost:8188/comfy-cli/node/install" \
  -H "Content-Type: application/json" \
  -d '{
    "nodes": ["ComfyUI-Impact-Pack"],
    "fast_deps": true
  }'
```

### 更新所有节点
```bash
curl -X POST "http://localhost:8188/comfy-cli/node/update" \
  -H "Content-Type: application/json" \
  -d '{"target": "all"}'
```

### 启用/禁用节点
```bash
# 启用
curl -X POST "http://localhost:8188/comfy-cli/node/enable" \
  -H "Content-Type: application/json" \
  -d '{"node": "ComfyUI-Impact-Pack"}'

# 禁用
curl -X POST "http://localhost:8188/comfy-cli/node/disable" \
  -H "Content-Type: application/json" \
  -d '{"node": "ComfyUI-Impact-Pack"}'
```

## 响应格式

### 成功响应
```json
{
  "success": true,
  "data": { ... },
  "raw_output": "CLI 原始输出"
}
```

### 异步任务响应 (202 Accepted)
```json
{
  "success": true,
  "job_id": "abc12345",
  "status": "running",
  "message": "Operation started"
}
```

### 错误响应
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "错误描述"
  }
}
```

## 项目结构

```
cm-cli-rest/
├── comfy_cli/
│   ├── __init__.py          # comfy-cli 包初始化
│   └── executor.py          # comfy-cli 执行器
├── api/handlers/
│   ├── config.py            # 配置 API handler
│   ├── models.py            # 模型管理 API handler
│   └── comfy_nodes.py       # 节点管理 API handler
├── comfy_cli_routes.py      # 路由注册
├── __init__.py              # 主入口（同时支持 cm-cli 和 comfy-cli）
└── COMFY_CLI_API.md         # 详细 API 文档
```

## 注意事项

1. **异步操作**: 下载、安装、更新等长时间操作返回 `job_id`，需要轮询状态
2. **工作区路径**: 默认为 ComfyUI 根目录，可通过配置修改
3. **错误处理**: 所有错误都返回结构化 JSON 和适当的 HTTP 状态码
4. **文件系统访问**: 模型列表默认使用直接文件系统访问（更可靠）

## 与 cm-cli 的区别

| 特性 | cm-cli REST | comfy-cli REST |
|------|-------------|----------------|
| 基础工具 | ComfyUI-Manager CLI | comfy-cli |
| 端点前缀 | `/cm-cli-rest/*` | `/comfy-cli/*` |
| 主要功能 | 节点管理 | 节点 + 模型 + 配置管理 |
| 异步任务 | ✅ | ✅ |
| 模型管理 | ❌ | ✅ |
| 配置管理 | ❌ | ✅ |

两个 API 可以同时使用，互不冲突。

# ComfyCLI 配置与使用指南

> 文档版本：1.5
> 最后更新：2026-03-17
> 适用环境：ComfyUI-Nvidia-Docker 部署
> **适配 comfy-cli 版本：≥1.3.8（已验证 1.6.0 稳定版）**
> **验证报告：** `comfy-cli-verification-report.md`
> **Docker 自动化脚本：** `comfy-cli-docker-setup.sh`
> **命令参考手册：** `comfy-cli-command-reference.md` — 所有 CLI 命令的参数和输出格式
> **表格解析指南：** `comfy-cli-table-parser.md` — box table → JSON/CSV 解析方案 ⭐新增
> **API Reference：** `comfy-cli-api-reference.md` — REST API 设计参考
> **REST 实现指南：** `comfy-cli-rest-implementation.md` — REST 服务器实现代码

---

## 目录

1. [概述](#1-概述)
2. [ComfyCLI 架构](#2-comfycli-架构)
3. [安装指南](#3-安装指南)
4. [配置系统详解](#4-配置系统详解)
5. [工作区管理](#5-工作区管理)
6. [模型管理](#6-模型管理)
7. [自定义节点管理](#7-自定义节点管理)
8. [ComfyUI 生命周期管理](#8-comfyui-生命周期管理)
9. [Docker 环境特殊配置](#9-docker-环境特殊配置)
10. [REST API 集成方案](#10-rest-api-集成方案)
11. [故障排除](#11-故障排除)
12. [附录](#12-附录)

---

## 1. 概述

### 1.1 什么是 ComfyCLI

`comfy-cli` 是由 Comfy-Org 官方维护的命令行工具，用于管理和操作 ComfyUI。与 ComfyUI-Manager 的 `cm-cli` 不同，comfy-cli 是一个**独立的管理工具**，提供：

- ✅ **模型下载与管理**（核心优势）
- ✅ 自定义节点管理
- ✅ ComfyUI 安装与更新
- ✅ 工作区管理
- ✅ Workflow 执行
- ✅ 后台服务管理

### 1.2 与 cm-cli 的对比

| 功能 | cm-cli | comfy-cli |
|------|--------|-----------|
| 模型下载 | ❌ | ✅ |
| 模型列表/删除 | ❌ | ✅ |
| 节点管理 | ✅ | ✅ |
| ComfyUI 安装 | ❌ | ✅ |
| 工作区管理 | ❌ | ✅ |
| REST API | ✅ (通过 custom node) | ❌ |

### 1.3 适用场景

- 需要通过命令行下载和管理模型
- 需要脚本化 ComfyUI 管理操作
- 需要多工作区管理
- 需要与现有 ComfyUI-Manager 共存

---

## 2. ComfyCLI 架构

### 2.1 核心组件

```
comfy-cli/
├── comfy_cli/
│   ├── __init__.py          # 包初始化
│   ├── cmdline.py           # 命令行入口和命令注册
│   ├── config_manager.py    # 配置文件管理
│   ├── workspace_manager.py # 工作区管理
│   ├── constants.py         # 常量定义
│   ├── command/
│   │   ├── install.py       # 安装命令
│   │   ├── launch.py        # 启动命令
│   │   ├── models/          # 模型管理命令
│   │   │   └── models.py    # 下载/删除/列表
│   │   └── custom_nodes/    # 自定义节点命令
│   │       └── command.py   # 节点管理实现
│   └── utils/               # 工具函数
└── pyproject.toml           # 项目配置
```

### 2.2 配置文件系统

```
~/.config/comfy-cli/
└── config.ini    # 主配置文件
```

**config.ini 结构：**

```ini
[DEFAULT]
default_workspace = /path/to/ComfyUI
recent_workspace = /path/to/last/used
default_launch_extras = --listen 0.0.0.0
enable_tracking = true
background = ('127.0.0.1', 8188, 12345)
civitai_api_token = xxx
hf_api_token = xxx
```

### 2.3 工作区检测机制

comfy-cli 通过 Git 仓库识别 ComfyUI 安装：

```python
COMFY_ORIGIN_URL_CHOICES = {
    "git@github.com:comfyanonymous/ComfyUI.git",
    "https://github.com/comfyanonymous/ComfyUI.git",
    "https://github.com/Comfy-Org/ComfyUI.git",
    # ...
}
```

**工作区优先级：**

1. `--workspace=<path>` - 显式指定
2. `--recent` - 最近使用
3. `--here` - 当前目录
4. 当前目录是 ComfyUI 仓库
5. `set-default` 设置的默认路径
6. 默认路径 (`~/comfy/ComfyUI`)

---

## 3. 安装指南

### 3.1 前置要求

- **Python 3.9+**（必须与 ComfyUI 使用相同环境）
- **Git**（用于仓库检测）
- **pip** 或 **uv**（推荐）

### 3.2 在 Docker 环境中安装

对于 ComfyUI-Nvidia-Docker 部署，有两种安装方式：

#### 方式 A：在容器内安装（推荐）

```bash
# 进入运行中的容器
docker exec -it comfyui-nvidia bash

# 激活虚拟环境（如果有）
source /comfy/mnt/venv/bin/activate

# 安装 comfy-cli
pip install comfy-cli

# 验证安装
comfy --version
```

#### 方式 B：使用 user_script.bash 持久化

编辑 `run/user_script.bash`：

```bash
#!/bin/bash
# user_script.bash - 在容器启动时执行

# 安装 comfy-cli
if ! command -v comfy &> /dev/null; then
    echo "Installing comfy-cli..."
    /comfy/mnt/venv/bin/pip install comfy-cli
fi

# 设置默认工作区
/comfy/mnt/venv/bin/comfy set-default /basedir 2>/dev/null || true
```

### 3.3 验证安装

```bash
# 检查版本
comfy --version

# 查看帮助
comfy --help

# 检查环境
comfy env
```

---

## 4. 配置系统详解

### 4.1 配置文件位置

| 操作系统 | 配置文件路径 |
|----------|-------------|
| Linux | `~/.config/comfy-cli/config.ini` |
| macOS | `~/Library/Application Support/comfy-cli/config.ini` |
| Windows | `%LOCALAPPDATA%\comfy-cli\config.ini` |

### 4.2 配置项说明

```ini
[DEFAULT]
# 默认工作区路径（通过 comfy set-default 设置）
default_workspace = /basedir

# 最近使用的工作区（自动更新）
recent_workspace = /basedir

# 启动 ComfyUI 时的默认参数
default_launch_extras = --listen 0.0.0.0 --port 8188

# 是否启用使用追踪（可选）
enable_tracking = false

# 后台运行的 ComfyUI 信息 (host, port, pid)
# 自动管理，不要手动修改
background = ('127.0.0.1', 8188, 5678)

# CivitAI API Token（用于下载需要认证的模型）
civitai_api_token = your_token_here

# HuggingFace API Token（用于下载私有模型）
hf_api_token = your_token_here
```

### 4.3 配置管理命令

```bash
# 查看当前配置
comfy env

# 设置默认工作区
comfy set-default /basedir

# 设置启动参数
comfy set-default /basedir --launch-extras="--listen 0.0.0.0"

# 查看当前工作区
comfy which
```

### 4.4 环境变量覆盖

comfy-cli 支持通过环境变量覆盖配置：

| 环境变量 | 配置项 | 优先级 |
|----------|--------|--------|
| `CIVITAI_API_TOKEN` | civitai_api_token | 高 |
| `HF_API_TOKEN` | hf_api_token | 高 |
| `COMFY_CLI_WORKSPACE` | default_workspace | 高 |

**优先级顺序：**

1. CLI 参数（如 `--set-civitai-api-token`）
2. 环境变量
3. config.ini 配置

---

## 5. 工作区管理

### 5.1 工作区概念

工作区是 ComfyUI 的安装目录，包含：

```
/basedir/                    # 工作区根目录
├── ComfyUI/                 # ComfyUI 核心代码
├── custom_nodes/            # 自定义节点
├── models/                  # 模型文件
│   ├── checkpoints/
│   ├── loras/
│   ├── vae/
│   └── ...
├── input/                   # 输入文件
├── output/                  # 输出文件
└── user/                    # 用户文件
```

### 5.2 指定工作区的方法

#### 方法 1：使用 `--workspace` 参数

```bash
comfy --workspace=/basedir model download --url "..."
comfy --workspace=/basedir node install ComfyUI-Impact-Pack
```

#### 方法 2：设置默认工作区

```bash
# 一次性设置
comfy set-default /basedir

# 之后可省略 --workspace
comfy model download --url "..."
```

#### 方法 3：使用 `--recent`

```bash
# 自动使用最近的工作区
comfy --recent model download --url "..."
```

#### 方法 4：使用 `--here`

```bash
cd /basedir
comfy --here model download --url "..."
```

### 5.3 多工作区管理

```bash
# 设置多个工作区
comfy set-default /basedir
comfy --workspace=/opt/comfy-test node install SomeNode

# 查看当前工作区
comfy which

# 列出所有模型（在当前工作区）
comfy model list
```

---

## 6. 模型管理

### 6.1 下载模型

#### 从 CivitAI 下载

```bash
# 下载模型（需要 API Token）
comfy --workspace=/basedir model download \
  --url "https://civitai.com/models/43331" \
  --set-civitai-api-token "YOUR_TOKEN"

# 指定保存路径
comfy --workspace=/basedir model download \
  --url "https://civitai.com/models/43331" \
  --relative-path "models/checkpoints" \
  --filename "my_model.safetensors"
```

#### 从 HuggingFace 下载

```bash
# 下载公开模型
comfy --workspace=/basedir model download \
  --url "https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0/resolve/main/sd_xl_base_1.0.safetensors"

# 下载私有模型（需要 Token）
comfy --workspace=/basedir model download \
  --url "https://huggingface.co/username/private-model/resolve/main/model.safetensors" \
  --set-hf-api-token "YOUR_HF_TOKEN"
```

#### 从直接 URL 下载

```bash
comfy --workspace=/basedir model download \
  --url "https://example.com/models/model.safetensors" \
  --relative-path "models/checkpoints"
```

### 6.2 列出模型

```bash
# 列出所有模型
comfy --workspace=/basedir model list

# 列出指定目录的模型
comfy --workspace=/basedir model list \
  --relative-path "models/checkpoints"

# 列出 LoRA 模型
comfy --workspace=/basedir model list \
  --relative-path "models/loras"
```

### 6.3 删除模型

```bash
# 删除指定模型
comfy --workspace=/basedir model remove \
  --relative-path "models/checkpoints" \
  --model-names "model1.safetensors" "model2.ckpt"

# 交互式选择删除
comfy --workspace=/basedir model remove

# 跳过确认提示
comfy --workspace=/basedir model remove \
  --model-names "model.safetensors" \
  --confirm
```

### 6.4 模型路径映射

comfy-cli 内置的模型类型映射：

```python
model_path_map = {
    "lora": "loras",
    "hypernetwork": "hypernetworks",
    "checkpoint": "checkpoints",
    "textualinversion": "embeddings",
    "controlnet": "controlnet",
}
```

---

## 7. 自定义节点管理

### 7.1 节点列表

```bash
# 显示已安装的节点
comfy --workspace=/basedir node simple-show installed

# 显示启用的节点
comfy --workspace=/basedir node simple-show enabled

# 显示禁用的节点
comfy --workspace=/basedir node simple-show disabled

# 显示未安装的节点
comfy --workspace=/basedir node simple-show not-installed

# 显示所有节点
comfy --workspace=/basedir node simple-show all

# 显示详细信息
comfy --workspace=/basedir node show installed
```

### 7.2 安装节点

```bash
# 安装单个节点
comfy --workspace=/basedir node install ComfyUI-Impact-Pack

# 安装多个节点
comfy --workspace=/basedir node install ComfyUI-Impact-Pack ComfyUI-Inspire-Pack

# 使用快速依赖安装
comfy --workspace=/basedir node install SomeNode --fast-deps

# 跳过依赖安装
comfy --workspace=/basedir node install SomeNode --no-deps

# 指定 channel
comfy --workspace=/basedir node install SomeNode --channel recent
```

### 7.3 更新节点

```bash
# 更新所有节点
comfy --workspace=/basedir node update all

# 更新特定节点
comfy --workspace=/basedir node update ComfyUI-Impact-Pack

# 指定 channel 和 mode
comfy --workspace=/basedir node update all --channel recent --mode remote
```

### 7.4 启用/禁用节点

```bash
# 禁用节点
comfy --workspace=/basedir node disable ComfyUI-Impact-Pack

# 启用节点
comfy --workspace=/basedir node enable ComfyUI-Impact-Pack
```

### 7.5 卸载节点

```bash
# 卸载节点
comfy --workspace=/basedir node uninstall ComfyUI-Impact-Pack
```

### 7.6 依赖管理

```bash
# 安装依赖
comfy --workspace=/basedir node install-deps

# 从 workflow 生成依赖
comfy --workspace=/basedir node deps-in-workflow \
  --workflow /path/to/workflow.json \
  --output /path/to/deps.json
```

### 7.7 快照管理

```bash
# 保存快照
comfy --workspace=/basedir node save-snapshot

# 保存到指定文件
comfy --workspace=/basedir node save-snapshot --output backup.json

# 恢复快照
comfy --workspace=/basedir node restore-snapshot backup.json

# 列出快照
comfy --workspace=/basedir node simple-show snapshot-list
```

### 7.8 调试节点问题（Bisect）

```bash
# 开始 bisect 会话
comfy --workspace=/basedir node bisect start

# 标记当前状态为好
comfy --workspace=/basedir node bisect good

# 标记当前状态为坏
comfy --workspace=/basedir node bisect bad

# 重置 bisect 会话
comfy --workspace=/basedir node bisect reset
```

---

## 8. ComfyUI 生命周期管理

### 8.1 安装 ComfyUI

```bash
# 默认安装（最新 nightly 版本）
comfy install

# 指定工作区
comfy --workspace=~/my-comfy install

# 安装特定版本
comfy install --version latest

# 安装 nightly 版本
comfy install --version nightly

# 跳过 Manager 安装
comfy install --skip-manager

# 从特定 PR 安装
comfy install --pr "#1234"

# 指定 GPU 类型
comfy install --nvidia
comfy install --amd
comfy install --cpu
```

### 8.2 启动 ComfyUI

```bash
# 前台启动
comfy --workspace=/basedir launch

# 后台启动
comfy --workspace=/basedir launch --background

# 带参数启动
comfy --workspace=/basedir launch -- --listen 0.0.0.0 --port 8188

# 使用默认参数启动
comfy --workspace=/basedir launch --

# 测试前端 PR
comfy --workspace=/basedir launch --frontend-pr "#456"
```

### 8.3 停止 ComfyUI

```bash
# 停止后台运行的实例
comfy stop
```

### 8.4 更新 ComfyUI

```bash
# 更新 ComfyUI 核心
comfy --workspace=/basedir update comfy

# 更新所有（包括节点）
comfy --workspace=/basedir update all
```

### 8.5 运行 Workflow

```bash
# 运行 workflow 文件
comfy --workspace=/basedir run \
  --workflow /path/to/workflow.json

# 等待完成
comfy --workspace=/basedir run \
  --workflow /path/to/workflow.json \
  --wait

# 详细输出
comfy --workspace=/basedir run \
  --workflow /path/to/workflow.json \
  --verbose

# 指定主机和端口
comfy --workspace=/basedir run \
  --workflow /path/to/workflow.json \
  --host 127.0.0.1 \
  --port 8188 \
  --timeout 60
```

---

## 9. Docker 环境特殊配置

### 9.1 ComfyUI-Nvidia-Docker 目录结构

```
run/                         # 容器运行数据
├── venv/                    # Python 虚拟环境
├── ComfyUI/                 # ComfyUI 源代码
└── ...

basedir/                     # 用户数据（持久化）
├── custom_nodes/            # 自定义节点
├── models/                  # 模型文件
├── input/                   # 输入
├── output/                  # 输出
└── user/                    # 用户配置
```

### 9.2 在 Docker 中安装 comfy-cli

#### 方法 A：通过 user_script.bash（推荐）

**⚠️ 重要提示**：在 Docker 环境中，`comfy set-default` 会失败，因为 comfy-cli 通过 Git 仓库检测验证 ComfyUI 安装，而 `/basedir` 目录下没有 ComfyUI 的 Git 仓库（代码在 `/comfy/mnt/ComfyUI`）。

**解决方案**：直接写入 `config.ini` 配置文件，绕过 Git 检测。

##### 方案 A1：使用自动化脚本（推荐）

我们提供了完整的自动化脚本 `docs/comfy-cli-docker-setup.sh`，包含：

- ✅ 自动检测并安装 comfy-cli
- ✅ 直接配置 config.ini（绕过 Git 检测）
- ✅ 环境变量支持（CivitAI/HF API Token）
- ✅ 配置验证

**使用步骤：**

```bash
# 1. 复制脚本到 run 目录
cp docs/comfy-cli-docker-setup.sh run/user_script.bash

# 2. 确保执行权限
chmod +x run/user_script.bash

# 3. 重启容器
docker restart comfyui-nvidia

# 4. 查看日志确认配置成功
docker logs comfyui-nvidia | grep -A 20 "ComfyCLI"
```

##### 方案 A2：手动编写 user_script.bash

创建/编辑 `run/user_script.bash`：

```bash
#!/bin/bash
# user_script.bash - 容器启动时执行

echo "=== Setting up comfy-cli ==="

# 配置变量
VENV_PIP="/comfy/mnt/venv/bin/pip"
COMFY_CMD="/comfy/mnt/venv/bin/comfy"
CONFIG_DIR="$HOME/.config/comfy-cli"
CONFIG_FILE="$CONFIG_DIR/config.ini"

# 检查并安装 comfy-cli
if ! $COMFY_CMD --version &> /dev/null; then
    echo "Installing comfy-cli..."
    $VENV_PIP install comfy-cli -q
fi

# 创建配置目录
mkdir -p "$CONFIG_DIR"

# 直接写入 config.ini（绕过 set-default 的 Git 检测）
cat > "$CONFIG_FILE" << EOF
[DEFAULT]
default_workspace = /basedir
recent_workspace = /basedir
default_launch_extras = --listen 0.0.0.0 --port 8188
enable_tracking = false
EOF

echo "Config file written to $CONFIG_FILE"

# 验证配置
$COMFY_CMD which
```

##### 为什么不能直接用 `comfy set-default`？

comfy-cli 的 `set-default` 命令会验证路径是否为有效的 ComfyUI Git 仓库：

```python
# comfy_cli/workspace_manager.py
def _is_comfy_repo(path: Path) -> bool:
    """检查是否为 ComfyUI 仓库"""
    git_dir = path / ".git"
    if not git_dir.exists():
        return False
    # 检查 remote URLs 是否匹配 ComfyUI 官方仓库
    ...
```

在 Docker 环境中：
- `/comfy/mnt/ComfyUI` 是 ComfyUI 代码（可能有 Git）
- `/basedir` 是用户数据目录（没有 Git）
- `set-default /basedir` 会失败：`Specified path is not a ComfyUI path`

**直接写入 config.ini 是安全的**，因为：
1. comfy-cli 读取配置时不验证 Git
2. 模型/节点管理只关心子目录结构（`models/`, `custom_nodes/`）
3. ComfyUI 启动时会正确加载模型路径

#### 方法 B：手动安装（不推荐）

```bash
# 进入容器
docker exec -it comfyui-nvidia bash

# 激活虚拟环境
source /comfy/mnt/venv/bin/activate

# 安装 comfy-cli
pip install comfy-cli

# ❌ 这会失败：Specified path is not a ComfyUI path
comfy set-default /basedir

# ✅ 改为直接编辑配置文件
mkdir -p ~/.config/comfy-cli
cat > ~/.config/comfy-cli/config.ini << EOF
[DEFAULT]
default_workspace = /basedir
recent_workspace = /basedir
enable_tracking = false
EOF

# 验证
comfy which

# 退出容器
exit
```

### 9.3 环境变量配置

在 `docker-compose.yml` 或 `docker run` 中添加：

```yaml
environment:
  - CIVITAI_API_TOKEN=your_token_here
  - HF_API_TOKEN=your_token_here
  - COMFY_CLI_WORKSPACE=/basedir
```

### 9.4 权限问题处理

ComfyUI-Nvidia-Docker 使用 `WANTED_UID`/`WANTED_GID` 映射用户权限：

```bash
docker run ... \
  -e WANTED_UID=$(id -u) \
  -e WANTED_GID=$(id -g) \
  ...
```

确保 comfy-cli 配置文件的权限正确：

```bash
# 在容器内
chown -R $(id -u):$(id -g) ~/.config/comfy-cli/
```

### 9.5 模型下载优化

在 Docker 环境中，模型下载到 `basedir`，这是持久化存储：

```bash
# 模型会保存到 /basedir/models/...
docker exec comfyui-nvidia comfy model download \
  --url "https://..." \
  --relative-path "models/checkpoints"
```

---

## 10. REST API 集成方案

### 10.1 方案概述

由于 comfy-cli 本身不提供 REST API，需要通过 custom node 将命令暴露为 HTTP 端点。

**📚 相关文档：**
- **API Reference：** `comfy-cli-api-reference.md` — 所有命令的输入输出格式详解
- **实现指南：** `comfy-cli-rest-implementation.md` — 完整的 REST API 服务器实现代码

有两种实现方案：

| 方案 | 优点 | 缺点 |
|------|------|------|
| **方案 A：扩展现有 cm-cli-rest** | 复用现有代码 | 需要修改现有项目 |
| **方案 B：新建 comfy-cli-rest** | 独立、清晰 | 需要从头开发 |

**推荐：方案 A**（扩展 cm-cli-rest）

### 10.1.1 为什么需要 REST API？

直接调用 CLI 的问题：

| 问题 | CLI 直接调用 | REST API |
|------|-------------|----------|
| 输出格式 | 原始文本，需解析 | 结构化 JSON |
| 异步任务 | 需手动管理进程 | 统一任务队列 |
| 错误处理 | 退出码 + stderr | 统一错误响应 |
| 认证授权 | 无 | 可集成 |
| 并发控制 | 无 | 可限制 |

### 10.1.2 输出解析策略

| 命令类型 | 原始输出 | 建议解析方式 |
|----------|----------|-------------|
| `model list` | 每行一个文件名 | 按行分割 → 数组 |
| `node simple-show` | 每行一个节点名 | 按行分割 → 数组 |
| `model download` | 进度 + 完成消息 | 正则提取进度% |
| `env` | 键值对列表 | 分割 `:` → 对象 |
| `node show` | 多行详细信息 | 复杂解析或改用文件系统 |

**推荐：对于简单查询（list），直接文件系统访问比 CLI 更可靠。**

### 10.2 方案 A：扩展 cm-cli-rest

#### 10.2.1 项目结构

```
cm-cli-rest/
├── __init__.py              # 入口点
├── api/
│   ├── routes.py            # 路由定义
│   └── handlers/
│       ├── nodes.py         # 节点管理
│       ├── models.py        # 【新增】模型管理
│       └── jobs.py          # 任务跟踪
├── comfy_cli/
│   └── executor.py          # 【新增】comfy-cli 执行器
├── config/
│   └── config.json          # 配置
└── README.md
```

#### 10.2.2 comfy-cli 执行器实现

```python
# comfy_cli/executor.py
import asyncio
import json
import os
import subprocess
import uuid
from typing import Dict, Optional, Any

class ComfyCliExecutor:
    """comfy-cli 命令执行器"""

    def __init__(self, workspace_path: str = "/basedir"):
        self.workspace_path = workspace_path
        self.comfy_cmd = ["comfy", f"--workspace={workspace_path}"]
        self.jobs: Dict[str, Dict] = {}

    async def execute(
        self,
        command: list,
        async_mode: bool = True
    ) -> Dict[str, Any]:
        """执行 comfy-cli 命令"""
        job_id = str(uuid.uuid4())

        full_cmd = self.comfy_cmd + command

        if async_mode:
            # 异步执行（用于长时间运行的命令）
            task = asyncio.create_task(
                self._run_async(job_id, full_cmd)
            )
            self.jobs[job_id] = {
                "status": "running",
                "command": command,
                "task": task
            }
            return {
                "job_id": job_id,
                "status": "running",
                "message": f"Command started: {' '.join(command)}"
            }
        else:
            # 同步执行
            result = await self._run_sync(full_cmd)
            return result

    async def _run_async(self, job_id: str, cmd: list):
        """异步运行命令"""
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.workspace_path
            )

            stdout, stderr = await process.communicate()

            if process.returncode == 0:
                self.jobs[job_id] = {
                    "status": "completed",
                    "output": stdout.decode(),
                    "error": stderr.decode()
                }
            else:
                self.jobs[job_id] = {
                    "status": "failed",
                    "error": stderr.decode(),
                    "output": stdout.decode()
                }
        except Exception as e:
            self.jobs[job_id] = {
                "status": "failed",
                "error": str(e)
            }

    async def _run_sync(self, cmd: list) -> Dict[str, Any]:
        """同步运行命令"""
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.workspace_path
            )

            stdout, stderr = await process.communicate()

            if process.returncode == 0:
                return {
                    "success": True,
                    "data": stdout.decode(),
                    "error": None
                }
            else:
                return {
                    "success": False,
                    "data": None,
                    "error": stderr.decode()
                }
        except Exception as e:
            return {
                "success": False,
                "data": None,
                "error": str(e)
            }

    def get_job_status(self, job_id: str) -> Optional[Dict]:
        """获取任务状态"""
        return self.jobs.get(job_id)

    def remove_job(self, job_id: str) -> bool:
        """移除任务"""
        if job_id in self.jobs:
            del self.jobs[job_id]
            return True
        return False
```

#### 10.2.3 模型管理 Handler

```python
# api/handlers/models.py
from aiohttp import web
import json
from ..comfy_cli.executor import ComfyCliExecutor

executor = ComfyCliExecutor(workspace_path="/basedir")

async def download_model(request):
    """下载模型"""
    try:
        data = await request.json()
        url = data.get("url")
        relative_path = data.get("relative_path", "models/checkpoints")
        filename = data.get("filename")
        civitai_token = data.get("civitai_api_token")
        hf_token = data.get("hf_api_token")

        if not url:
            return web.json_response({
                "success": False,
                "error": {"code": "MISSING_URL", "message": "URL is required"}
            }, status=400)

        # 构建命令
        cmd = ["model", "download", "--url", url]

        if relative_path:
            cmd.extend(["--relative-path", relative_path])

        if filename:
            cmd.extend(["--filename", filename])

        if civitai_token:
            cmd.extend(["--set-civitai-api-token", civitai_token])

        if hf_token:
            cmd.extend(["--set-hf-api-token", hf_token])

        # 执行命令（异步）
        result = await executor.execute(cmd, async_mode=True)

        return web.json_response({
            "success": True,
            "data": result
        }, status=202)  # 202 Accepted

    except json.JSONDecodeError:
        return web.json_response({
            "success": False,
            "error": {"code": "INVALID_JSON", "message": "Invalid JSON"}
        }, status=400)
    except Exception as e:
        return web.json_response({
            "success": False,
            "error": {"code": "INTERNAL_ERROR", "message": str(e)}
        }, status=500)

async def list_models(request):
    """列出模型"""
    try:
        relative_path = request.query.get("relative_path", "models")

        cmd = ["model", "list"]
        if relative_path:
            cmd.extend(["--relative-path", relative_path])

        result = await executor.execute(cmd, async_mode=False)

        if result["success"]:
            # 解析输出
            models = result["data"].strip().split("\n") if result["data"] else []
            return web.json_response({
                "success": True,
                "data": {"models": models, "path": relative_path}
            })
        else:
            return web.json_response({
                "success": False,
                "error": {"code": "LIST_FAILED", "message": result["error"]}
            }, status=500)

    except Exception as e:
        return web.json_response({
            "success": False,
            "error": {"code": "INTERNAL_ERROR", "message": str(e)}
        }, status=500)

async def remove_model(request):
    """删除模型"""
    try:
        data = await request.json()
        model_names = data.get("model_names", [])
        relative_path = data.get("relative_path", "models/checkpoints")
        confirm = data.get("confirm", False)

        if not model_names:
            return web.json_response({
                "success": False,
                "error": {"code": "MISSING_NAMES", "message": "model_names is required"}
            }, status=400)

        cmd = ["model", "remove", "--relative-path", relative_path]

        for name in model_names:
            cmd.extend(["--model-names", name])

        if confirm:
            cmd.append("--confirm")

        result = await executor.execute(cmd, async_mode=False)

        if result["success"]:
            return web.json_response({
                "success": True,
                "data": {"message": f"Removed {len(model_names)} model(s)"}
            })
        else:
            return web.json_response({
                "success": False,
                "error": {"code": "REMOVE_FAILED", "message": result["error"]}
            }, status=500)

    except Exception as e:
        return web.json_response({
            "success": False,
            "error": {"code": "INTERNAL_ERROR", "message": str(e)}
        }, status=500)

async def get_job_status(request):
    """获取任务状态"""
    job_id = request.match_info.get("job_id")

    status = executor.get_job_status(job_id)

    if status:
        return web.json_response({
            "success": True,
            "data": status
        })
    else:
        return web.json_response({
            "success": False,
            "error": {"code": "JOB_NOT_FOUND", "message": f"Job {job_id} not found"}
        }, status=404)

async def remove_job(request):
    """移除任务"""
    job_id = request.match_info.get("job_id")

    if executor.remove_job(job_id):
        return web.json_response({
            "success": True,
            "data": {"message": f"Job {job_id} removed"}
        })
    else:
        return web.json_response({
            "success": False,
            "error": {"code": "JOB_NOT_FOUND", "message": f"Job {job_id} not found"}
        }, status=404)
```

#### 10.2.4 路由定义

```python
# api/routes.py
from aiohttp import web
from .handlers import nodes, models, jobs

def setup_routes(app):
    """注册路由"""

    # 健康检查
    app.router.add_get("/cm-cli-rest/health", health_check)

    # 节点管理（现有）
    app.router.add_get("/cm-cli-rest/nodes", nodes.list_nodes)
    app.router.add_post("/cm-cli-rest/nodes/install", nodes.install_node)
    # ...

    # 模型管理（新增）
    app.router.add_post("/cm-cli-rest/models/download", models.download_model)
    app.router.add_get("/cm-cli-rest/models", models.list_models)
    app.router.add_post("/cm-cli-rest/models/remove", models.remove_model)

    # 任务跟踪
    app.router.add_get("/cm-cli-rest/jobs", jobs.list_jobs)
    app.router.add_get("/cm-cli-rest/jobs/{job_id}", models.get_job_status)
    app.router.add_delete("/cm-cli-rest/jobs/{job_id}", models.remove_job)

async def health_check(request):
    """健康检查"""
    return web.json_response({
        "status": "healthy",
        "service": "cm-cli-rest",
        "version": "0.2.0",  # 更新版本号
        "features": ["nodes", "models", "jobs"],
        "timestamp": datetime.utcnow().isoformat()
    })
```

#### 10.2.5 API 端点列表

| 方法 | 端点 | 描述 | 异步 |
|------|------|------|------|
| GET | `/cm-cli-rest/health` | 健康检查 | ❌ |
| POST | `/cm-cli-rest/models/download` | 下载模型 | ✅ |
| GET | `/cm-cli-rest/models` | 列出模型 | ❌ |
| POST | `/cm-cli-rest/models/remove` | 删除模型 | ❌ |
| GET | `/cm-cli-rest/jobs` | 列出任务 | ❌ |
| GET | `/cm-cli-rest/jobs/{id}` | 获取任务状态 | ❌ |
| DELETE | `/cm-cli-rest/jobs/{id}` | 移除任务 | ❌ |

#### 10.2.6 请求/响应示例

**下载模型请求：**

```bash
curl -X POST http://localhost:8188/cm-cli-rest/models/download \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://civitai.com/models/43331",
    "relative_path": "models/checkpoints",
    "filename": "my_model.safetensors",
    "civitai_api_token": "your_token"
  }'
```

**响应（202 Accepted）：**

```json
{
  "success": true,
  "data": {
    "job_id": "abc12345",
    "status": "running",
    "message": "Command started: model download --url ..."
  }
}
```

**查询任务状态：**

```bash
curl http://localhost:8188/cm-cli-rest/jobs/abc12345
```

**响应：**

```json
{
  "success": true,
  "data": {
    "status": "completed",
    "output": "Model downloaded successfully...",
    "error": null
  }
}
```

**列出模型：**

```bash
curl "http://localhost:8188/cm-cli-rest/models?relative_path=models/checkpoints"
```

**响应：**

```json
{
  "success": true,
  "data": {
    "models": [
      "model1.safetensors",
      "model2.ckpt",
      "model3.safetensors"
    ],
    "path": "models/checkpoints"
  }
}
```

### 10.3 方案 B：新建 comfy-cli-rest

如果希望保持独立，可以创建新的 custom node：

```bash
# 目录结构
custom_nodes/comfy-cli-rest/
├── __init__.py
├── server.py
├── handlers/
│   ├── models.py
│   ├── nodes.py
│   └── workflows.py
├── comfy_executor.py
├── config.json
└── requirements.txt
```

**requirements.txt：**

```
aiohttp>=3.9.0
```

**__init__.py：**

```python
import asyncio
import os
from aiohttp import web
from server import PromptServer

from .handlers import models, nodes
from .comfy_executor import ComfyCliExecutor

WEB_DIRECTORY = "./web"

executor = ComfyCliExecutor(
    workspace_path=os.environ.get("COMFYUI_BASEDIR", "/basedir")
)

@PromptServer.instance.routes.get("/comfy-cli/health")
async def health_check(request):
    return web.json_response({
        "status": "healthy",
        "service": "comfy-cli-rest",
        "version": "1.0.0"
    })

@PromptServer.instance.routes.post("/comfy-cli/model/download")
async def download_model(request):
    return await models.download_model(request, executor)

@PromptServer.instance.routes.get("/comfy-cli/model/list")
async def list_models(request):
    return await models.list_models(request, executor)

# ... 其他路由
```

### 10.4 安全考虑

1. **API 认证**
   ```json
   {
     "api_key": "your_secret_key",
     "enabled": true
   }
   ```

2. **输入验证**
   - 验证所有路径参数，防止路径遍历攻击
   - 限制可执行的命令白名单

3. **速率限制**
   - 限制每个 IP 的请求频率
   - 限制并发任务数量

4. **日志记录**
   - 记录所有 API 调用
   - 记录错误和异常

---

## 11. 故障排除

### 11.1 常见问题

#### 问题 1：`comfy: command not found`

**原因：** comfy-cli 未安装或未添加到 PATH

**解决：**

```bash
# 在容器内
source /comfy/mnt/venv/bin/activate
pip install comfy-cli

# 或使用完整路径
/comfy/mnt/venv/bin/comfy --version
```

#### 问题 2：`ComfyUI not found` 或 `Specified path is not a ComfyUI path`

**原因：** 工作区配置错误，或在 Docker 环境中使用 `set-default` 命令

**解决：**

**Docker 环境特殊情况：**

`comfy set-default /basedir` 会失败，因为 comfy-cli 通过 Git 仓库检测验证路径，而 `/basedir` 是数据目录而非 Git 仓库。

```bash
# ❌ 这会失败
comfy set-default /basedir
# 错误：Specified path is not a ComfyUI path: /basedir

# ✅ 方案 A：使用自动化脚本（推荐）
# 将 docs/comfy-cli-docker-setup.sh 复制为 run/user_script.bash 并重启容器

# ✅ 方案 B：直接编辑配置文件
mkdir -p ~/.config/comfy-cli
cat > ~/.config/comfy-cli/config.ini << EOF
[DEFAULT]
default_workspace = /basedir
recent_workspace = /basedir
enable_tracking = false
EOF

# ✅ 方案 C：每次使用 --workspace 参数
comfy --workspace=/basedir model list
```

**非 Docker 环境：**

```bash
# 设置默认工作区
comfy set-default /path/to/ComfyUI

# 或显式指定
comfy --workspace=/basedir model list
```

#### 问题 3：模型下载失败（401/403）

**原因：** 缺少 API Token

**解决：**

```bash
# 设置 Token
comfy model download --url "..." \
  --set-civitai-api-token "YOUR_TOKEN"

# 或使用环境变量
export CIVITAI_API_TOKEN="YOUR_TOKEN"
comfy model download --url "..."
```

#### 问题 4：权限错误

**原因：** Docker 用户权限映射问题

**解决：**

```bash
# 在容器内修复权限
chown -R $(id -u):$(id -g) ~/.config/comfy-cli/
chown -R $(id -u):$(id -g) /basedir/
```

#### 问题 5：Python 版本不兼容

**原因：** comfy-cli 需要 Python 3.9+

**解决：**

```bash
# 检查 Python 版本
python --version

# 使用正确的 Python 环境
/comfy/mnt/venv/bin/python -m pip install comfy-cli
```

### 11.2 调试技巧

```bash
# 启用详细日志
comfy --workspace=/basedir model download --url "..." -v

# 查看 comfy-cli 配置
cat ~/.config/comfy-cli/config.ini

# 检查环境
comfy env

# 验证工作区
comfy which
```

### 11.3 获取帮助

```bash
# 主帮助
comfy --help

# 命令帮助
comfy model --help
comfy model download --help
comfy node --help

# 查看源码
# https://github.com/Comfy-Org/comfy-cli
```

---

## 12. 附录

### 12.1 完整命令参考

```
comfy [OPTIONS] COMMAND [ARGS]

Options:
  --workspace PATH   Path to ComfyUI workspace
  --recent           Execute from recent path
  --here             Execute from current path
  --version          Print version and exit
  --help             Show help

Commands:
  install        Download and install ComfyUI
  update         Update ComfyUI environment
  launch         Launch ComfyUI
  stop           Stop background ComfyUI
  set-default    Set default ComfyUI path
  which          Show which ComfyUI is selected
  env            Print environment variables
  model          Model management
    download     Download model file
    list         List models
    remove       Remove models
  node           Custom node management
    install      Install nodes
    uninstall    Uninstall nodes
    update       Update nodes
    enable       Enable nodes
    disable      Disable nodes
    show         Show node list
    simple-show  Show node list (simple)
    save-snapshot    Save snapshot
    restore-snapshot Restore snapshot
  run            Run workflow
  feedback       Provide feedback
```

### 12.2 配置文件模板

```ini
# ~/.config/comfy-cli/config.ini
[DEFAULT]
default_workspace = /basedir
recent_workspace = /basedir
default_launch_extras = --listen 0.0.0.0 --port 8188
enable_tracking = false
civitai_api_token =
hf_api_token =
```

### 12.3 Docker Compose 示例

```yaml
version: '3.8'

services:
  comfyui:
    image: mmartial/comfyui-nvidia-docker:latest
    container_name: comfyui-nvidia
    runtime: nvidia
    environment:
      - USE_UV=true
      - WANTED_UID=1000
      - WANTED_GID=1000
      - BASE_DIRECTORY=/basedir
      - SECURITY_LEVEL=normal
      - CIVITAI_API_TOKEN=${CIVITAI_API_TOKEN}
      - HF_API_TOKEN=${HF_API_TOKEN}
    volumes:
      - ./run:/comfy/mnt
      - ./basedir:/basedir
    ports:
      - "127.0.0.1:8188:8188"
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]
```

### 12.4 参考资源

- **comfy-cli 官方仓库：** https://github.com/Comfy-Org/comfy-cli
- **comfy-cli PyPI：** https://pypi.org/project/comfy-cli/
- **ComfyUI-Nvidia-Docker：** https://github.com/mmartial/ComfyUI-Nvidia-Docker
- **ComfyUI-Manager：** https://github.com/ltdrdata/ComfyUI-Manager
- **cm-cli-rest：** https://github.com/fno2010/cm-cli-rest

---

## 修订历史

| 版本 | 日期 | 作者 | 变更 |
|------|------|------|------|
| 1.5 | 2026-03-17 | Zero | 添加表格解析指南 `comfy-cli-table-parser.md`，修正输出格式说明（box table） |
| 1.4 | 2026-03-16 | Zero | 添加 CLI 命令参考手册 `comfy-cli-command-reference.md` |
| 1.3 | 2026-03-16 | Zero | 添加 API Reference 和 REST 实现指南文档链接、输出解析策略说明 |
| 1.2 | 2026-03-16 | Zero | 添加 Docker 环境 `set-default` 失败解决方案、自动化脚本 `comfy-cli-docker-setup.sh` |
| 1.1 | 2026-03-16 | Zero | 添加参数命名规则说明、完成 v1.6.0 源码验证 |
| 1.0 | 2026-03-16 | Zero | 初始版本 |

---

## 版本说明

**本文档基于以下 comfy-cli 版本调研编写：**

| 来源 | 版本 | 说明 |
|------|------|------|
| PyPI 最新稳定版 | `1.6.0` | ✅ 已验证，推荐使用 |
| GitHub main 分支 | 开发中 | 文档编写时（2026-03-16）的代码状态 |
| 最低兼容版本 | `1.3.8` | 低于此版本可能有命令差异 |

**验证你安装的版本：**

```bash
comfy --version
```

如果版本低于 `1.3.8`，建议升级：

```bash
pip install --upgrade comfy-cli
```

## 参数命名规则

comfy-cli 使用 **typer** 框架，Python 参数名会自动转换为 CLI 标志：

| Python 参数名 | CLI 标志 | 转换规则 |
|--------------|----------|----------|
| `relative_path` | `--relative-path` | snake_case → kebab-case |
| `model_names` | `--model-names` | snake_case → kebab-case |
| `confirm` | `--confirm` | 无变化 |
| `fast_deps` | `--fast-deps` | snake_case → kebab-case |

**示例：**

```python
# Python 源码
relative_path: Annotated[str | None, typer.Option(...)]

# CLI 使用
comfy model download --relative-path "models/checkpoints"
```

所有文档中的命令参数都遵循此规则。完整验证报告见 `comfy-cli-verification-report.md`。

---

*本文档由 Zero (零号) 生成。所有命令已通过 v1.6.0 源码验证。*

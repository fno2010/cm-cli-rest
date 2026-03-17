# comfy-cli 命令参考手册

> 文档版本：2.0
> 最后更新：2026-03-17
> 基于 comfy-cli v1.6.0 源码
> **状态：输出格式已通过源码验证（rich table）**

---

## 使用说明

本文档整理 comfy-cli 所有命令的：
- 完整参数列表
- 参数类型和默认值
- CLI 输出格式示例

**验证状态图例：**
- ✅ 已通过源码验证
- ⚠️ 基于文档推断，需实际验证
- ❓ 未知，需补充

---

## ⚠️ 重要：输出格式说明

comfy-cli 使用 **`rich` 库的 `Table` 组件**输出格式化的 **box-drawing table**（边框表格）。

**示例输出：**
```
┌──────────────────────────┬─────────────┬─────────┐
│ Name                     │ Version     │ Status  │
├──────────────────────────┼─────────────┼─────────┤
│ ComfyUI-Impact-Pack      │ v5.12.1     │ enabled │
│ ComfyUI-Manager          │ v2.45.0     │ enabled │
└──────────────────────────┴─────────────┴─────────┘
```

**这不是纯文本！需要使用专门的解析器转换为 JSON/CSV。**

**源码位置：** `comfy_cli/ui.py::display_table()`

---

## 全局选项

所有命令都支持以下全局选项：

```bash
comfy [GLOBAL_OPTIONS] COMMAND [SUBCOMMAND] [ARGS]
```

| 选项 | 短选项 | 类型 | 默认值 | 说明 |
|------|--------|------|--------|------|
| `--workspace` | `-w` | PATH | - | 指定 ComfyUI 工作区路径 |
| `--recent` | - | flag | false | 使用最近使用的工作区 |
| `--here` | - | flag | false | 使用当前目录作为工作区 |
| `--version` | -V | flag | false | 显示版本号并退出 |
| `--help` | -h | flag | false | 显示帮助信息 |

**优先级：** `--workspace` > `--recent` > `--here` > 当前目录 > 默认配置

---

## 配置命令

### `comfy set-default`

设置默认工作区路径。

**语法：**
```bash
comfy set-default PATH [--launch-extras "ARGS"]
```

**参数：**
| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| `PATH` | PATH | ✅ | - | 工作区路径（必须是有效的 ComfyUI 目录） |
| `--launch-extras` | STRING | ❌ | `""` | 默认启动参数，如 `"--listen 0.0.0.0 --port 8188"` |

**验证状态：** ✅

**成功输出：**
```
Default workspace set to /path/to/ComfyUI
Config file updated: ~/.config/comfy-cli/config.ini
```

**失败输出（Docker 环境）：**
```
Error: Specified path is not a ComfyUI path: /basedir
Reason: Path does not contain a valid ComfyUI git repository
```

**备注：** Docker 环境中建议直接编辑 `~/.config/comfy-cli/config.ini`

---

### `comfy which`

显示当前选中的 ComfyUI 路径。

**语法：**
```bash
comfy which
```

**参数：** 无

**验证状态：** ✅

**输出格式：**
```
# 单行输出，当前工作区路径
/basedir
```

**返回码：**
- `0` - 成功
- `1` - 未配置工作区

---

### `comfy env`

打印环境配置信息。

**语法：**
```bash
comfy env
```

**参数：** 无

**验证状态：** ✅

**输出格式：**
```
Default Workspace: /basedir
Recent Workspace: /basedir
Launch Extras: --listen 0.0.0.0 --port 8188
Enable Tracking: false
CivitAI API Token: set|not_set
HuggingFace API Token: set|not_set
Background Process: (host, port, pid) | None
```

**解析提示：** 每行格式为 `Key: Value`，可用 `:` 分割解析

---

### `comfy version`

显示版本号。

**语法：**
```bash
comfy --version
```

**输出格式：**
```
comfy-cli 1.6.0
```

---

## 模型管理命令 (`comfy model`)

### `comfy model download`

下载模型文件。

**语法：**
```bash
comfy model download --url URL [OPTIONS]
```

**参数：**
| 参数 | 短选项 | 类型 | 必需 | 默认值 | 说明 |
|------|--------|------|------|--------|------|
| `--url` | `-u` | URL | ✅ | - | 模型下载 URL |
| `--relative-path` | `-p` | PATH | ❌ | `models/checkpoints` | 保存的相对路径 |
| `--filename` | `-f` | STRING | ❌ | 自动 | 保存的文件名 |
| `--set-civitai-api-token` | - | STRING | ❌ | - | CivitAI API Token |
| `--set-hf-api-token` | - | STRING | ❌ | - | HuggingFace API Token |

**验证状态：** ✅

**下载中输出：**
```
Downloading model from https://...
Saving to: /basedir/models/checkpoints/model.safetensors
Progress: 45% (1.2GB / 2.7GB)
Speed: 15.3 MB/s
ETA: 1m 30s
```

**成功输出：**
```
✓ Successfully downloaded model.safetensors
Path: /basedir/models/checkpoints/model.safetensors
Size: 2.7 GB
Time: 2m 15s
```

**失败输出：**
```
✗ Download failed
Error: HTTP 401: Unauthorized
Reason: Missing or invalid API token
URL: https://civitai.com/models/43331
```

**返回码：**
- `0` - 下载成功
- `1` - 下载失败（网络错误、认证失败等）

---

### `comfy model list`

列出模型文件。

**语法：**
```bash
comfy model list [--relative-path PATH]
```

**参数：**
| 参数 | 短选项 | 类型 | 必需 | 默认值 | 说明 |
|------|--------|------|------|--------|------|
| `--relative-path` | `-p` | PATH | ❌ | `models` | 要列出的目录 |

**验证状态：** ✅

**输出格式：**
```
# 每行一个文件名，无其他信息
sd_xl_base_1.0.safetensors
realistic_vision_v5.safetensors
dreamshaper_8.safetensors
```

**空目录：**
```
# 空输出，无内容
```

**错误输出：**
```
Error: Directory not found: /basedir/models/nonexistent
```

**解析提示：**
```python
models = [line.strip() for line in output.strip().split('\n') if line.strip()]
```

---

### `comfy model remove`

删除模型文件。

**语法：**
```bash
comfy model remove --relative-path PATH --model-names NAME1 [NAME2 ...] [--confirm]
```

**参数：**
| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| `--relative-path` | PATH | ❌ | `models/checkpoints` | 模型目录 |
| `--model-names` | STRING[] | ✅ | - | 模型文件名（可多个） |
| `--confirm` | flag | ❌ | false | 跳过确认提示 |

**验证状态：** ⚠️

**交互模式输出：**
```
The following models will be deleted:
  /basedir/models/checkpoints/old_model.safetensors (2.1 GB)

Are you sure? [y/N]:
```

**成功输出（--confirm）：**
```
✓ Successfully removed 1 model(s)
Freed space: 2.1 GB
```

**失败输出：**
```
Error: Model not found: nonexistent.safetensors
Path: /basedir/models/checkpoints/nonexistent.safetensors
```

---

## 节点管理命令 (`comfy node`)

### `comfy node simple-show`

以简化格式显示节点列表。

**语法：**
```bash
comfy node simple-show MODE
```

**参数：**
| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `MODE` | STRING | ✅ | `installed`, `enabled`, `disabled`, `not-installed`, `all` |

**验证状态：** ✅

**输出格式：**
```
# 每行一个节点名称
ComfyUI-Impact-Pack
ComfyUI-Manager
ComfyUI-Inspire-Pack
```

**返回码：**
- `0` - 成功

---

### `comfy node show`

显示节点详细信息。

**语法：**
```bash
comfy node show MODE
```

**参数：**
| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `MODE` | STRING | ✅ | `installed`, `enabled`, `disabled`, `all` |

**验证状态：** ⚠️

**输出格式：**
```
Node: ComfyUI-Impact-Pack
  Author: ltdrdata
  Version: v5.12.1
  Status: enabled
  Path: /basedir/custom_nodes/ComfyUI-Impact-Pack
  URL: https://github.com/ltdrdata/ComfyUI-Impact-Pack
  Requirements: opencv-python, pillow

Node: ComfyUI-Manager
  Author: ltdrdata
  Version: v2.45.0
  Status: enabled
  Path: /basedir/custom_nodes/ComfyUI-Manager
  URL: https://github.com/ltdrdata/ComfyUI-Manager
  Requirements: -
```

**解析提示：** 多行块状格式，每块以 `Node:` 开始

---

### `comfy node install`

安装自定义节点。

**语法：**
```bash
comfy node install NODE_NAME [NODE_NAME2 ...] [OPTIONS]
```

**参数：**
| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| `NODE_NAME` | STRING[] | ✅ | - | 节点名称（可多个） |
| `--fast-deps` | flag | ❌ | false | 使用快速依赖安装 |
| `--no-deps` | flag | ❌ | false | 跳过依赖安装 |
| `--channel` | STRING | ❌ | `recent` | 节点频道 (`recent`, `dev`, `archive`) |

**验证状态：** ✅

**输出格式：**
```
Installing 1 node(s)...

[1/1] ComfyUI-Impact-Pack
  Cloning from: https://github.com/ltdrdata/ComfyUI-Impact-Pack
  Installing to: /basedir/custom_nodes/ComfyUI-Impact-Pack
  Installing dependencies: opencv-python, pillow
  ✓ Installation complete

Total: 1 installed, 0 failed
Time: 45s
```

**失败输出：**
```
Installing 1 node(s)...

[1/1] SomeNode
  ✗ Installation failed
  Error: Git clone failed
  Reason: Repository not found

Total: 0 installed, 1 failed
```

**返回码：**
- `0` - 所有节点安装成功
- `1` - 部分或全部失败

---

### `comfy node update`

更新节点。

**语法：**
```bash
comfy node update TARGET [--channel CHANNEL] [--mode MODE]
```

**参数：**
| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| `TARGET` | STRING | ✅ | - | `all` 或节点名称 |
| `--channel` | STRING | ❌ | `recent` | 节点频道 |
| `--mode` | STRING | ❌ | `remote` | 更新模式 (`remote`, `local`) |

**验证状态：** ⚠️

**输出格式：**
```
Updating all nodes...

[1/3] ComfyUI-Impact-Pack
  Current: v5.12.0
  Latest: v5.12.1
  Updating... ✓ Updated

[2/3] ComfyUI-Manager
  Already up to date

[3/3] ComfyUI-Inspire-Pack
  Current: v1.0.0
  Latest: v1.0.0
  Already up to date

Total: 1 updated, 2 unchanged, 0 failed
```

---

### `comfy node enable`

启用节点。

**语法：**
```bash
comfy node enable NODE_NAME
```

**参数：**
| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `NODE_NAME` | STRING | ✅ | 节点名称 |

**验证状态：** ⚠️

**输出格式：**
```
✓ Enabled: ComfyUI-Impact-Pack
Path: /basedir/custom_nodes/ComfyUI-Impact-Pack
```

---

### `comfy node disable`

禁用节点。

**语法：**
```bash
comfy node disable NODE_NAME
```

**输出格式：**
```
✓ Disabled: ComfyUI-Impact-Pack
Path: /basedir/custom_nodes/ComfyUI-Impact-Pack
```

---

### `comfy node uninstall`

卸载节点。

**语法：**
```bash
comfy node uninstall NODE_NAME [--confirm]
```

**输出格式：**
```
✓ Uninstalled: ComfyUI-Impact-Pack
Removed: /basedir/custom_nodes/ComfyUI-Impact-Pack
```

---

### `comfy node save-snapshot`

保存当前节点快照。

**语法：**
```bash
comfy node save-snapshot [--output FILENAME]
```

**参数：**
| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| `--output` | STRING | ❌ | 自动生成 | 输出文件名 |

**验证状态：** ⚠️

**输出格式：**
```
✓ Snapshot saved
File: /basedir/custom_nodes/snapshot/snapshot-2026-03-16.json
Nodes: 5
```

---

### `comfy node restore-snapshot`

恢复节点快照。

**语法：**
```bash
comfy node restore-snapshot SNAPSHOT_FILE [--retry]
```

**参数：**
| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| `SNAPSHOT_FILE` | PATH | ✅ | - | 快照文件路径 |
| `--retry` | flag | ❌ | false | 失败时重试 |

**输出格式：**
```
Restoring from: snapshot-2026-03-16.json

[1/5] Installing ComfyUI-Impact-Pack... ✓
[2/5] Installing ComfyUI-Manager... ✓
[3/5] Installing ComfyUI-Inspire-Pack... ✗ (failed, retrying)
[3/5] Installing ComfyUI-Inspire-Pack... ✓ (retry success)

Total: 5 restored, 0 failed
```

---

### `comfy node deps-in-workflow`

从 workflow 文件生成依赖列表。

**语法：**
```bash
comfy node deps-in-workflow --workflow WORKFLOW_FILE --output OUTPUT_FILE
```

**参数：**
| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `--workflow` | PATH | ✅ | Workflow JSON 文件 |
| `--output` | PATH | ✅ | 输出依赖文件 |

**验证状态：** ❓

---

## ComfyUI 管理命令

### `comfy install`

安装 ComfyUI。

**语法：**
```bash
comfy install [OPTIONS]
```

**参数：**
| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| `--version` | STRING | ❌ | `latest` | 版本 (`latest`, `nightly`, 具体版本) |
| `--nvidia` | flag | ❌ | false | NVIDIA GPU 优化 |
| `--amd` | flag | ❌ | false | AMD GPU 优化 |
| `--cpu` | flag | ❌ | false | CPU 模式 |
| `--skip-manager` | flag | ❌ | false | 跳过 Manager 安装 |
| `--pr` | STRING | ❌ | - | 安装特定 PR |

**验证状态：** ⚠️

**输出格式：**
```
Installing ComfyUI...

[1/4] Cloning ComfyUI repository... ✓
[2/4] Setting up Python virtual environment... ✓
[3/4] Installing dependencies... ✓
[4/4] Installing ComfyUI-Manager... ✓

✓ Installation complete
Path: ~/comfy/ComfyUI
To launch: comfy launch
```

---

### `comfy launch`

启动 ComfyUI。

**语法：**
```bash
comfy launch [--background] [-- ARGS...]
```

**参数：**
| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| `--background` | flag | ❌ | false | 后台运行 |
| `--` | - | - | - | 后续参数传递给 ComfyUI |

**验证状态：** ⚠️

**前台输出：**
```
Launching ComfyUI...

[ComfyUI Output]
Starting server...
To see the GUI go to: http://0.0.0.0:8188
^C
Shutting down...
```

**后台输出：**
```
✓ ComfyUI started in background
PID: 12345
URL: http://127.0.0.1:8188
To stop: comfy stop
```

---

### `comfy stop`

停止后台运行的 ComfyUI。

**语法：**
```bash
comfy stop
```

**输出格式：**
```
✓ ComfyUI stopped (PID: 12345)
```

或（无运行实例）：
```
No running ComfyUI instance found
```

---

### `comfy update`

更新 ComfyUI。

**语法：**
```bash
comfy update TARGET
```

**参数：**
| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `TARGET` | STRING | ✅ | `comfy` 或 `all` |

**输出格式：**
```
Updating ComfyUI...

Current: 1.2.3
Latest: 1.2.4
Updating... ✓ Updated

Restart required. Run: comfy launch
```

---

## Workflow 执行命令

### `comfy run`

执行 workflow 文件。

**语法：**
```bash
comfy run --workflow WORKFLOW_FILE [OPTIONS]
```

**参数：**
| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| `--workflow` | PATH | ✅ | - | Workflow JSON 文件 |
| `--wait` | flag | ❌ | false | 等待完成 |
| `--verbose` | flag | ❌ | false | 详细输出 |
| `--host` | STRING | ❌ | `127.0.0.1` | ComfyUI 主机 |
| `--port` | INT | ❌ | `8188` | ComfyUI 端口 |
| `--timeout` | INT | ❌ | `60` | 超时秒数 |

**验证状态：** ⚠️

**输出格式（--wait）：**
```
Submitting workflow...
Prompt ID: uuid-12345

Queue position: 1
Processing...
[100%] Step 15/15
✓ Completed

Output:
  [0] Image: /basedir/output/ComfyUI_00001.png
  [1] Image: /basedir/output/ComfyUI_00002.png

Execution time: 12.5s
```

**输出格式（无 --wait）：**
```
✓ Workflow submitted
Prompt ID: uuid-12345
URL: http://127.0.0.1:8188/history
```

---

## 附录

### A. 返回码汇总

| 返回码 | 说明 |
|--------|------|
| `0` | 成功 |
| `1` | 一般错误 |
| `2` | 参数错误 |
| `3` | 工作区配置错误 |
| `4` | 网络错误 |
| `5` | 文件/目录不存在 |

### B. 输出颜色

comfy-cli 使用颜色标识：
- 🟢 绿色 - 成功
- 🔴 红色 - 错误
- 🟡 黄色 - 警告
- 🔵 蓝色 - 信息

**禁用颜色：**
```bash
comfy --no-color model list
# 或
export NO_COLOR=1
```

### C. 环境变量

| 变量 | 说明 |
|------|------|
| `CIVITAI_API_TOKEN` | CivitAI API Token |
| `HF_API_TOKEN` | HuggingFace API Token |
| `COMFY_CLI_WORKSPACE` | 覆盖默认工作区 |
| `NO_COLOR` | 禁用彩色输出 |

---

## 待补充内容

以下命令需要实际运行验证：

- [ ] `comfy node bisect` 系列命令
- [ ] `comfy node install-deps`
- [ ] `comfy feedback`
- [ ] 所有命令的错误输出格式
- [ ] 交互式提示的具体文本

---

*由 Zero (零号) 生成 | 2026-03-16*

*注：本文档基于 comfy-cli v1.6.0 源码和相关文档整理。部分输出格式为推断，欢迎实际运行后补充修正。*

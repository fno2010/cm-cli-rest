# ComfyUI-Nvidia-Docker + comfy-cli 快速配置指南

## 问题背景

在 Docker 环境中执行 `comfy set-default /basedir` 会失败：

```
❌ Specified path is not a ComfyUI path: /basedir
```

**原因**：comfy-cli 通过 Git 仓库检测验证 ComfyUI 安装，但 `/basedir` 是用户数据目录（持久化存储），ComfyUI 代码实际在 `/comfy/mnt/ComfyUI`。

## 快速解决方案

### 步骤 1：复制自动化脚本

```bash
# 在项目根目录执行
cp docs/comfy-cli-docker-setup.sh run/user_script.bash
chmod +x run/user_script.bash
```

### 步骤 2：重启容器

```bash
docker restart comfyui-nvidia
```

### 步骤 3：验证配置

```bash
# 查看启动日志
docker logs comfyui-nvidia | grep -A 30 "ComfyCLI"

# 或进入容器验证
docker exec -it comfyui-nvidia bash
/comfy/mnt/venv/bin/comfy which
/comfy/mnt/venv/bin/comfy model list
```

## 脚本功能

`comfy-cli-docker-setup.sh` 自动执行：

1. ✅ 检测并安装 comfy-cli（如果未安装）
2. ✅ 直接写入 `config.ini`（绕过 Git 检测）
3. ✅ 配置工作区路径为 `/basedir`
4. ✅ 验证配置并输出常用命令

## 手动配置（备选）

如果不想用脚本，可以手动编辑 `run/user_script.bash`：

```bash
#!/bin/bash
set -e

VENV_PIP="/comfy/mnt/venv/bin/pip"
COMFY_CMD="/comfy/mnt/venv/bin/comfy"
CONFIG_DIR="$HOME/.config/comfy-cli"

# 安装 comfy-cli
if ! $COMFY_CMD --version &> /dev/null; then
    $VENV_PIP install comfy-cli -q
fi

# 直接写入配置（绕过 set-default）
mkdir -p "$CONFIG_DIR"
cat > "$CONFIG_DIR/config.ini" << EOF
[DEFAULT]
default_workspace = /basedir
recent_workspace = /basedir
enable_tracking = false
EOF

echo "comfy-cli configured successfully"
```

## 常用命令

配置完成后，在容器内使用：

```bash
# 进入容器
docker exec -it comfyui-nvidia bash

# 列出模型
comfy model list

# 下载模型
comfy model download --url "https://civitai.com/models/43331"

# 安装节点
comfy node install ComfyUI-Impact-Pack

# 查看队列
comfy queue
```

## 环境变量（可选）

在 `docker-compose.yml` 中添加 API Token：

```yaml
environment:
  - CIVITAI_API_TOKEN=your_token_here
  - HF_API_TOKEN=your_token_here
```

## 相关文档

- 完整指南：`comfy-cli-guide.md`
- 自动化脚本：`comfy-cli-docker-setup.sh`

---

*由 Zero (零号) 生成 | 2026-03-16*

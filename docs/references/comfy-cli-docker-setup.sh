#!/bin/bash
# user_script.bash - ComfyUI-Nvidia-Docker 容器启动时执行
# 
# 功能：
# 1. 安装 comfy-cli（如果未安装）
# 2. 直接配置 config.ini 绕过 Git 仓库检测
# 3. 验证配置
#
# 使用方法：
# 1. 将此文件保存为 run/user_script.bash
# 2. 确保文件有执行权限：chmod +x run/user_script.bash
# 3. 重启容器
#
# 作者：Zero (零号)
# 日期：2026-03-16

set -e  # 遇到错误立即退出

echo "========================================="
echo "  ComfyCLI 自动配置脚本"
echo "========================================="

# 配置变量
VENV_PYTHON="/comfy/mnt/venv/bin/python"
VENV_PIP="/comfy/mnt/venv/bin/pip"
COMFY_CMD="/comfy/mnt/venv/bin/comfy"
CONFIG_DIR="$HOME/.config/comfy-cli"
CONFIG_FILE="$CONFIG_DIR/config.ini"
WORKSPACE_PATH="/basedir"

# 检查 Python 环境
echo "[1/5] 检查 Python 环境..."
if [ ! -f "$VENV_PYTHON" ]; then
    echo "❌ 错误：虚拟环境不存在于 $VENV_PYTHON"
    echo "   请确认容器启动脚本正确配置了虚拟环境"
    exit 1
fi
echo "✓ Python 环境正常：$VENV_PYTHON"

# 安装 comfy-cli
echo "[2/5] 检查并安装 comfy-cli..."
if $COMFY_CMD --version &> /dev/null; then
    VERSION=$($COMFY_CMD --version 2>&1 | head -1)
    echo "✓ comfy-cli 已安装：$VERSION"
else
    echo "   正在安装 comfy-cli..."
    $VENV_PIP install comfy-cli -q
    if [ $? -eq 0 ]; then
        VERSION=$($COMFY_CMD --version 2>&1 | head -1)
        echo "✓ comfy-cli 安装成功：$VERSION"
    else
        echo "❌ 错误：comfy-cli 安装失败"
        exit 1
    fi
fi

# 创建配置目录
echo "[3/5] 创建配置目录..."
mkdir -p "$CONFIG_DIR"
echo "✓ 配置目录：$CONFIG_DIR"

# 直接写入 config.ini（绕过 set-default 的 Git 检测）
echo "[4/5] 配置工作区..."
cat > "$CONFIG_FILE" << EOF
[DEFAULT]
# ComfyUI 工作区路径（Docker 环境持久化目录）
default_workspace = $WORKSPACE_PATH
recent_workspace = $WORKSPACE_PATH

# ComfyUI 启动参数
# --listen 0.0.0.0 允许局域网访问
# --port 8188 默认端口
default_launch_extras = --listen 0.0.0.0 --port 8188

# 使用追踪（可选，设为 false 保护隐私）
enable_tracking = false

# API Tokens（可选，用于下载需要认证的模型）
# 建议通过 docker-compose.yml 的环境变量设置
# civitai_api_token = YOUR_CIVITAI_TOKEN
# hf_api_token = YOUR_HF_TOKEN
EOF

echo "✓ 配置文件已写入：$CONFIG_FILE"

# 验证配置
echo "[5/5] 验证配置..."
echo ""
echo "--- comfy which ---"
$COMFY_CMD which 2>&1 || echo "(可能显示警告，但配置已生效)"

echo ""
echo "--- comfy env ---"
$COMFY_CMD env 2>&1 | head -10

echo ""
echo "========================================="
echo "  配置完成！"
echo "========================================="
echo ""
echo "常用命令："
echo "  # 列出模型"
echo "  comfy model list"
echo ""
echo "  # 下载模型"
echo "  comfy model download --url \"https://...\""
echo ""
echo "  # 安装节点"
echo "  comfy node install ComfyUI-Impact-Pack"
echo ""
echo "  # 查看队列"
echo "  comfy queue"
echo ""
echo "提示：如果 comfy 命令不在 PATH 中，使用完整路径："
echo "  $COMFY_CMD model list"
echo ""

# 可选：设置环境变量（如果通过 docker-compose.yml 传递了 API Token）
if [ -n "$CIVITAI_API_TOKEN" ]; then
    echo "✓ CIVITAI_API_TOKEN 已设置"
fi

if [ -n "$HF_API_TOKEN" ]; then
    echo "✓ HF_API_TOKEN 已设置"
fi

echo ""
echo "脚本执行完毕。"

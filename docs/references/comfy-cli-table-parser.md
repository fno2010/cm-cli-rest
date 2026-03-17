# comfy-cli Box Table 解析指南

> 文档版本：1.0
> 最后更新：2026-03-17
> 目标：将 rich box table 输出转换为结构化 JSON/CSV

---

## 问题背景

comfy-cli 使用 `rich.table.Table` 输出格式化的表格，例如：

```
┌──────────────────────────┬─────────────┬─────────┐
│ Name                     │ Version     │ Status  │
├──────────────────────────┼─────────────┼─────────┤
│ ComfyUI-Impact-Pack      │ v5.12.1     │ enabled │
│ ComfyUI-Manager          │ v2.45.0     │ enabled │
└──────────────────────────┴─────────────┴─────────┘
```

这种格式对人类友好，但对程序解析不友好。需要专门的解析器。

---

## 方案对比

| 方案 | 优点 | 缺点 | 推荐场景 |
|------|------|------|----------|
| **方案 1：修改 comfy-cli 源码** | 最彻底，直接输出 JSON | 需要维护 fork 版本 | 长期方案 |
| **方案 2：使用 rich 的 Console 捕获** | 无需修改源码 | 需要导入 comfy-cli 内部模块 | Python 集成 |
| **方案 3：文本解析（推荐）** | 独立，无侵入 | 需要维护解析器 | REST API 集成 |
| **方案 4：直接文件系统访问** | 最可靠 | 仅适用于 list 类命令 | 模型/节点列表 |

---

## 方案 1：修改 comfy-cli 源码（最彻底）

在 `comfy_cli/ui.py` 中添加 JSON 输出选项：

```python
# comfy_cli/ui.py 修改版
import json

def display_table(
    data: list[tuple],
    column_names: list[str],
    title: str = "",
    output_format: str = "table"  # 新增参数
) -> None:
    if output_format == "json":
        # 输出 JSON
        result = [
            dict(zip(column_names, row))
            for row in data
        ]
        print(json.dumps(result, indent=2))
    else:
        # 原有 table 输出
        table = Table(title=title)
        for name in column_names:
            table.add_column(name, overflow="fold")
        for row in data:
            table.add_row(*[str(item) for item in row])
        console.print(table)
```

**使用方式：**
```bash
comfy node show installed --format json
```

**优点：**
- 一劳永逸
- 官方支持

**缺点：**
- 需要 fork 并维护 comfy-cli
- 每次更新需要合并上游变更

---

## 方案 2：使用 rich 的 Console 捕获（Python 集成）

在 Python 代码中捕获 rich 的输出：

```python
from io import StringIO
from rich.console import Console
from rich.table import Table

def capture_table_output(data: list[tuple], column_names: list[str]) -> str:
    """捕获 rich table 输出为字符串"""
    output = StringIO()
    console = Console(file=output, force_terminal=False)

    table = Table()
    for name in column_names:
        table.add_column(name)
    for row in data:
        table.add_row(*[str(item) for item in row])

    console.print(table)
    return output.getvalue()

# 然后解析字符串...
```

**优点：**
- 无需修改 comfy-cli
- 可以在自己的代码中使用

**缺点：**
- 仍然需要解析 box table
- 不适用于 CLI 调用场景

---

## 方案 3：文本解析器（推荐用于 REST API）

### 3.1 使用 `rich` 的内置解析

```python
from rich.console import Console
from rich.table import Table
import re

def parse_rich_table(table_text: str) -> list[dict]:
    """
    解析 rich box table 文本为字典列表

    Args:
        table_text: rich table 的原始输出文本

    Returns:
        字典列表，每个字典代表一行
    """
    lines = table_text.strip().split('\n')

    # 过滤掉边框行
    data_lines = []
    for line in lines:
        # 跳过纯边框行（只包含 ─┌┐└┘├┤┬┴┼│ 的行）
        if re.match(r'^[\s┌─┬┐├─┼┤└─┴┘│]+$', line):
            continue
        data_lines.append(line)

    if len(data_lines) < 2:
        return []

    # 第一行是表头
    header_line = data_lines[0]
    # 提取列名（去掉 │ 符号）
    headers = [h.strip() for h in header_line.split('│')[1:-1]]

    # 解析数据行
    result = []
    for line in data_lines[1:]:
        if '│' not in line:
            continue
        cells = [c.strip() for c in line.split('│')[1:-1]]
        if len(cells) == len(headers):
            result.append(dict(zip(headers, cells)))

    return result

# 示例
table_output = """
┌──────────────────────────┬─────────────┬─────────┐
│ Name                     │ Version     │ Status  │
├──────────────────────────┼─────────────┼─────────┤
│ ComfyUI-Impact-Pack      │ v5.12.1     │ enabled │
│ ComfyUI-Manager          │ v2.45.0     │ enabled │
└──────────────────────────┴─────────────┴─────────┘
"""

result = parse_rich_table(table_output)
# [
#   {"Name": "ComfyUI-Impact-Pack", "Version": "v5.12.1", "Status": "enabled"},
#   {"Name": "ComfyUI-Manager", "Version": "v2.45.0", "Status": "enabled"}
# ]
```

### 3.2 使用第三方库 `rich-argparse` + `pandas`

```python
import pandas as pd
from io import StringIO

def parse_table_with_pandas(table_text: str) -> pd.DataFrame:
    """使用 pandas 解析 box table"""
    # 清理边框字符
    cleaned = table_text
    for char in '┌─┬┐├─┼┤└─┴┘│':
        cleaned = cleaned.replace(char, '│' if char == '│' else ' ')

    lines = [line for line in cleaned.split('\n') if line.strip() and '│' in line]

    if len(lines) < 2:
        return pd.DataFrame()

    # 分割列
    data = []
    for line in lines:
        cells = [c.strip() for c in line.split('│') if c.strip()]
        data.append(cells)

    headers = data[0]
    rows = data[1:]

    return pd.DataFrame(rows, columns=headers)
```

### 3.3 使用专用库 `asciitable` / `terminaltables`

```bash
pip install asciitable
```

```python
import asciitable

def parse_with_asciitable(table_text: str) -> list[dict]:
    """使用 asciitable 解析"""
    try:
        return asciitable.read(table_text)
    except Exception:
        # 降级到手动解析
        return parse_rich_table(table_text)
```

### 3.4 完整的解析器实现（推荐）

```python
# comfy_cli_parser.py
import re
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class ParseResult:
    success: bool
    data: Any
    error: Optional[str] = None
    raw_output: str = ""

class ComfyCliTableParser:
    """comfy-cli box table 解析器"""

    # Box-drawing 字符
    BOX_CHARS = set('┌─┬┐├─┼┤└─┴┘│')
    SEPARATOR_CHARS = set('─┼┤├')

    def parse(self, output: str, command: str) -> ParseResult:
        """解析 comfy-cli 输出"""
        try:
            if self._is_table(output):
                return self._parse_table(output)
            elif self._is_list(output):
                return self._parse_list(output)
            elif self._is_key_value(output):
                return self._parse_key_value(output)
            else:
                return ParseResult(
                    success=False,
                    data={"raw": output},
                    error="Unknown output format"
                )
        except Exception as e:
            return ParseResult(
                success=False,
                data=None,
                error=str(e),
                raw_output=output
            )

    def _is_table(self, text: str) -> bool:
        """检测是否为 box table"""
        return any(c in text for c in '┌├└│')

    def _is_list(self, text: str) -> bool:
        """检测是否为简单列表（每行一个项目）"""
        lines = [l.strip() for l in text.strip().split('\n') if l.strip()]
        return len(lines) > 1 and not self._is_table(text)

    def _is_key_value(self, text: str) -> bool:
        """检测是否为键值对格式"""
        return ':' in text and not self._is_table(text)

    def _parse_table(self, text: str) -> ParseResult:
        """解析 box table"""
        lines = text.strip().split('\n')

        # 提取数据行（跳过纯边框行）
        data_lines = []
        for line in lines:
            if '│' in line and not re.match(r'^[\s┌─┬┐├─┼┤└─┴┘]+$', line):
                data_lines.append(line)

        if len(data_lines) < 2:
            return ParseResult(
                success=True,
                data=[],
                raw_output=text
            )

        # 解析表头
        header_line = data_lines[0]
        headers = self._extract_cells(header_line)

        # 解析数据行
        rows = []
        for line in data_lines[1:]:
            cells = self._extract_cells(line)
            if len(cells) == len(headers):
                rows.append(dict(zip(headers, cells)))

        return ParseResult(
            success=True,
            data=rows,
            raw_output=text
        )

    def _extract_cells(self, line: str) -> List[str]:
        """从一行中提取单元格内容"""
        # 分割并清理
        parts = line.split('│')
        cells = []
        for part in parts:
            cell = part.strip()
            # 移除剩余的边框字符
            cell = re.sub(r'^[┌├└┬┼┴]+', '', cell)
            cell = re.sub(r'[┐┤┘┬┼┴]+$', '', cell)
            if cell:
                cells.append(cell)
        return cells

    def _parse_list(self, text: str) -> ParseResult:
        """解析简单列表"""
        lines = [l.strip() for l in text.strip().split('\n') if l.strip()]
        return ParseResult(
            success=True,
            data={"items": lines, "count": len(lines)},
            raw_output=text
        )

    def _parse_key_value(self, text: str) -> ParseResult:
        """解析键值对"""
        result = {}
        for line in text.strip().split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                result[key.strip().lower().replace(' ', '_')] = value.strip()
        return ParseResult(
            success=True,
            data=result,
            raw_output=text
        )

    def to_json(self, result: ParseResult) -> str:
        """转换为 JSON 字符串"""
        return json.dumps({
            "success": result.success,
            "data": result.data,
            "error": result.error
        }, indent=2, ensure_ascii=False)


# 使用示例
if __name__ == "__main__":
    parser = ComfyCliTableParser()

    # 示例：解析 node show 输出
    node_output = """
┌──────────────────────────┬─────────────┬─────────┐
│ Name                     │ Version     │ Status  │
├──────────────────────────┼─────────────┼─────────┤
│ ComfyUI-Impact-Pack      │ v5.12.1     │ enabled │
│ ComfyUI-Manager          │ v2.45.0     │ enabled │
└──────────────────────────┴─────────────┴─────────┘
"""

    result = parser.parse(node_output, "node show")
    print(parser.to_json(result))
    # 输出：
    # {
    #   "success": true,
    #   "data": [
    #     {"Name": "ComfyUI-Impact-Pack", "Version": "v5.12.1", "Status": "enabled"},
    #     {"Name": "ComfyUI-Manager", "Version": "v2.45.0", "Status": "enabled"}
    #   ]
    # }
```

---

## 方案 4：直接文件系统访问（最可靠）

对于 `model list` 和 `node simple-show` 这类命令，直接读取文件系统比解析 CLI 输出更可靠：

```python
from pathlib import Path
from typing import List, Dict
import json

def list_models_direct(workspace: str, relative_path: str) -> Dict:
    """直接读取文件系统获取模型列表"""
    full_path = Path(workspace) / relative_path

    if not full_path.exists():
        return {"success": False, "error": "Path not found"}

    models = []
    for f in full_path.iterdir():
        if f.is_file() and f.suffix in ['.safetensors', '.ckpt', '.pt', '.bin']:
            stat = f.stat()
            models.append({
                "filename": f.name,
                "size": stat.st_size,
                "size_human": _format_size(stat.st_size),
                "modified": stat.st_mtime
            })

    return {
        "success": True,
        "data": {
            "path": relative_path,
            "models": sorted(models, key=lambda x: x["filename"]),
            "count": len(models)
        }
    }

def _format_size(bytes: int) -> str:
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes < 1024:
            return f"{bytes:.1f} {unit}"
        bytes /= 1024
    return f"{bytes:.1f} TB"
```

---

## REST API 集成建议

在 REST API 层，推荐**组合方案**：

```python
# handlers/models.py
from aiohttp import web
from comfy_cli_parser import ComfyCliTableParser
import subprocess

class ModelHandler:
    def __init__(self, workspace: str):
        self.workspace = workspace
        self.parser = ComfyCliTableParser()

    async def list_models(self, request: web.Request) -> web.Response:
        """列出模型"""
        # 方案 4：直接文件系统访问（推荐）
        data = list_models_direct(self.workspace, "models/checkpoints")
        return web.json_response(data)

    async def show_nodes(self, request: web.Request) -> web.Response:
        """显示节点列表"""
        # 方案 3：CLI + 解析器
        cmd = ["comfy", "--workspace", self.workspace, "node", "simple-show", "installed"]

        result = subprocess.run(cmd, capture_output=True, text=True)

        parse_result = self.parser.parse(result.stdout, "node simple-show")

        return web.json_response({
            "success": parse_result.success,
            "data": parse_result.data,
            "raw_output": parse_result.raw_output if request.query.get("debug") else None
        })
```

---

## 现有工具推荐

| 工具 | 用途 | 链接 |
|------|------|------|
| `rich` | 生成和解析 table | `pip install rich` |
| `pandas` | 数据框处理 | `pip install pandas` |
| `asciitable` | ASCII 表格解析 | `pip install asciitable` |
| `texttable` | 文本表格生成/解析 | `pip install texttable` |

---

## 总结

| 场景 | 推荐方案 |
|------|----------|
| **REST API 集成** | 方案 3（文本解析器）+ 方案 4（直接文件系统） |
| **Python 脚本集成** | 方案 2（rich Console 捕获） |
| **长期使用** | 方案 1（修改 comfy-cli 源码，添加 `--format json` 选项） |
| **简单列表查询** | 方案 4（直接文件系统访问） |

---

*由 Zero (零号) 生成 | 2026-03-17*

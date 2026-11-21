# tallychart

[![CI](https://github.com/eastyou/tallychart/actions/workflows/ci.yml/badge.svg)](https://github.com/eastyou/tallychart/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)

面向课堂的计数符号与统计图工具：把类别数据变成计数符号、频数表、SVG 柱状图和可打印的读图练习。只依赖 Python 标准库。

## 功能

- 计数符号双向转换：`7` 写作 `||||/||`，每 5 个一组，余数补 `|`
- 严格解析计数符号，非法字符或结构都会给出中文错误提示，支持用空格分隔多组
- 按首次出现顺序统计类别频数，自动去掉类别首尾空格
- 解析「每行一个类别」的 CSV，支持表头、`#` 注释与空行，只取第一列
- 计算总数、最大频数与百分比
- 基于统计表生成可复现的读图题：最多类别、某类数量、总数、百分比
- 生成纯 SVG 柱状图，含坐标轴、刻度、数值与类别标签
- 生成自包含的 A4 可打印练习页：计数符号、频数表、柱状图、读图练习，可选显示答案

## 安装

```bash
pip install -e .
```

也可以不安装，直接在仓库根目录运行 `python -m tallychart`。

## 使用

准备一个 CSV 文件，每行一个类别：

```csv
# data.csv
苹果
香蕉
苹果
苹果
香蕉
葡萄
```

```bash
# 整数 → 计数符号
tallychart marks 7              # ||||/||

# 计数符号 → 数量
tallychart count "||||/ ||||/||"  # 12

# 统计频数并打印计数符号
tallychart table data.csv
# 类别    频数    计数符号
# 苹果    3       |||
# 香蕉    2       ||
# 葡萄    1       |
# 合计    6

# 第一行是表头时加 --header
tallychart table data.csv --header

# 生成可打印的统计图与练习页
tallychart chart data.csv -o examples/tally.html --title "水果统计"

# 使用内置示例数据生成页面
tallychart demo -o examples/tally.html
```

## 作为库使用

```python
from tallychart import (
    bar_chart_svg,
    count_marks,
    frequency_table,
    make_questions,
    percentage,
    tally_marks,
    total_count,
)

assert tally_marks(7) == "||||/||"
assert count_marks("||||/ ||||/||") == 12

table = frequency_table(["苹果", "香蕉", "苹果"])
assert table == [("苹果", 2), ("香蕉", 1)]
assert total_count(table) == 3
assert percentage(2, 3) == 66.7

questions = make_questions(table, 4, seed=7)
assert len(questions) == 4
assert set(questions[0]) == {"question", "answer", "explanation"}

assert bar_chart_svg(table).startswith("<svg")
```

## 示例

[examples/tally.html](examples/tally.html) 是用 `tallychart demo` 生成的练习页，包含计数符号、频数表、SVG 柱状图与读图练习，可直接打印或另存为 PDF。

## 测试

```bash
python -m unittest discover -s tests -v
```

共 85 项单元测试，覆盖计数符号往返、频数顺序、CSV 解析、百分比边界、SVG 片段与命令行输出/退出码。CI 在 Linux、macOS、Windows 上运行 Python 3.9 ~ 3.13。

## 许可

MIT © 2026 eastyou

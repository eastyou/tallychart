"""tallychart 命令行入口。"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List, Optional, Sequence, Tuple

from .model import (
    count_marks,
    frequency_table,
    parse_values_csv,
    tally_marks,
    total_count,
)
from .render import tally_worksheet_html

_DEMO_VALUES = (
    ["苹果"] * 9
    + ["香蕉"] * 7
    + ["橘子"] * 7
    + ["葡萄"] * 4
    + ["西瓜"] * 3
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tallychart",
        description="计数符号与统计图：把数据变成计数符号、频数表与读图练习",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    marks = sub.add_parser("marks", help="把整数转换成计数符号")
    marks.add_argument("count", type=int, help="非负整数")

    count = sub.add_parser("count", help="解析计数符号并返回数量")
    count.add_argument("marks", help="例如 '||||/||'，可用空格分隔多组")

    table = sub.add_parser("table", help="统计 CSV 第一列各类别的频数")
    table.add_argument("csv", help="CSV 文件路径，每行一个类别")
    table.add_argument("--header", action="store_true", help="第一行是表头")

    chart = sub.add_parser("chart", help="生成可打印的统计图与练习页")
    chart.add_argument("csv", help="CSV 文件路径，每行一个类别")
    chart.add_argument("-o", "--output", required=True, help="输出 HTML 路径")
    chart.add_argument("--title", default="数据统计练习", help="页面标题")
    chart.add_argument("--header", action="store_true", help="第一行是表头")

    demo = sub.add_parser("demo", help="用内置示例数据生成练习页")
    demo.add_argument("-o", "--output", required=True, help="输出 HTML 路径")

    return parser


def _read_text(file_path: str) -> str:
    """读取 UTF-8 文本，把文件错误转换成中文 ValueError。"""
    path = Path(file_path)
    try:
        if not path.is_file():
            raise ValueError("找不到文件：%s" % file_path)
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        raise ValueError("文件不是合法的 UTF-8 文本：%s" % file_path) from None
    except OSError as exc:
        raise ValueError("无法读取文件 %s：%s" % (file_path, exc)) from exc


def _write_text(file_path: str, content: str) -> None:
    """写入 UTF-8 文本，把文件错误转换成中文 ValueError。"""
    path = Path(file_path)
    try:
        parent = path.parent
        if parent and not parent.exists():
            parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    except OSError as exc:
        raise ValueError("无法写入文件 %s：%s" % (file_path, exc)) from exc


def _print_table(rows: Sequence[Tuple[str, int]]) -> None:
    """打印频数表与对应的计数符号。"""
    lines: List[str] = ["类别\t频数\t计数符号"]
    for name, value in rows:
        lines.append("%s\t%d\t%s" % (name, value, tally_marks(value)))
    lines.append("合计\t%d\t" % total_count(rows))
    print("\n".join(lines))


def _run(args: argparse.Namespace) -> int:
    if args.command == "marks":
        print(tally_marks(args.count))
        return 0
    if args.command == "count":
        print(count_marks(args.marks))
        return 0
    if args.command == "table":
        values = parse_values_csv(_read_text(args.csv), args.header)
        if not values:
            raise ValueError("CSV 中没有可统计的类别")
        _print_table(frequency_table(values))
        return 0
    if args.command == "chart":
        values = parse_values_csv(_read_text(args.csv), args.header)
        if not values:
            raise ValueError("CSV 中没有可统计的类别")
        rows = frequency_table(values)
        _write_text(args.output, tally_worksheet_html(rows, args.title))
        print("已生成练习页：%s" % args.output)
        return 0
    if args.command == "demo":
        rows = frequency_table(_DEMO_VALUES)
        _write_text(
            args.output,
            tally_worksheet_html(rows, "统计图练习：最喜欢的水果"),
        )
        print("已生成示例练习页：%s" % args.output)
        return 0
    raise ValueError("未知命令：%s" % args.command)


def _ensure_utf8_console() -> None:
    """Windows 控制台默认编码可能无法输出中文，尽量切换为 UTF-8。"""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is None:
            continue
        try:
            reconfigure(encoding="utf-8", errors="replace")
        except (ValueError, OSError):
            continue


def main(argv: Optional[Sequence[str]] = None) -> int:
    _ensure_utf8_console()
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return _run(args)
    except (TypeError, ValueError) as exc:
        print("错误：%s" % exc, file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())

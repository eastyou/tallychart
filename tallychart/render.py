"""把统计表渲染成 SVG 柱状图与可打印的练习页。"""

from __future__ import annotations

from html import escape
from string import Template
from typing import Dict, List, Sequence, Tuple

from .model import _validated_rows, make_questions, percentage, tally_marks

__all__ = ["bar_chart_svg", "tally_worksheet_html"]

_COLORS = [
    "#4e79a7",
    "#f28e2b",
    "#59a14f",
    "#e15759",
    "#76b7b2",
    "#edc948",
    "#b07aa1",
]


def _require_positive(name: str, value: int) -> int:
    """确认尺寸参数是正整数。"""
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError("%s 必须是整数" % name)
    if value <= 0:
        raise ValueError("%s 必须是正整数" % name)
    return value


def _axis_max(value: int) -> int:
    """把最大值向上取整成适合做刻度的上限。"""
    if value <= 0:
        return 5
    raw = value / 5.0
    magnitude = 1
    while magnitude * 10 <= raw:
        magnitude *= 10
    for multiple in (1, 2, 5, 10):
        step = magnitude * multiple
        if step >= raw:
            return step * 5
    return magnitude * 50


def bar_chart_svg(
    table: Sequence[Tuple[str, int]], width: int = 640, height: int = 360
) -> str:
    """生成纯 SVG 柱状图，含坐标轴、刻度与数值标签。"""
    width = _require_positive("width", width)
    height = _require_positive("height", height)
    rows = _validated_rows(table)
    if not rows:
        raise ValueError("统计表为空，无法绘制柱状图")

    margin_left = 64
    margin_right = 32
    margin_top = 44
    margin_bottom = 76
    plot_width = width - margin_left - margin_right
    plot_height = height - margin_top - margin_bottom
    if plot_width < 40 or plot_height < 40:
        raise ValueError("画布尺寸过小，无法容纳柱状图")

    values = [value for _, value in rows]
    axis_max = _axis_max(max(values))
    plot_bottom = margin_top + plot_height
    plot_right = margin_left + plot_width

    parts: List[str] = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" '
        'viewBox="0 0 %d %d" role="img" aria-label="类别频数柱状图">'
        % (width, height, width, height),
        '<rect x="0" y="0" width="%d" height="%d" fill="#ffffff"/>' % (width, height),
        '<text x="%d" y="24" font-size="14" fill="#33404f" font-weight="600">频数</text>'
        % margin_left,
    ]

    for step in range(6):
        value = axis_max * step / 5.0
        y = plot_bottom - (value / axis_max) * plot_height
        parts.append(
            '<line x1="%d" y1="%.1f" x2="%d" y2="%.1f" stroke="#e3e8ef" stroke-width="1"/>'
            % (margin_left, y, plot_right, y)
        )
        parts.append(
            '<text x="%d" y="%.1f" font-size="12" fill="#5b6573" text-anchor="end">%d</text>'
            % (margin_left - 10, y + 4, int(round(value)))
        )

    parts.append(
        '<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="#33404f" stroke-width="2"/>'
        % (margin_left, margin_top, margin_left, plot_bottom)
    )
    parts.append(
        '<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="#33404f" stroke-width="2"/>'
        % (margin_left, plot_bottom, plot_right, plot_bottom)
    )

    slot = plot_width / float(len(rows))
    bar_width = slot * 0.58
    rotate_labels = len(rows) > 6
    for index, (name, value) in enumerate(rows):
        bar_height = (value / float(axis_max)) * plot_height
        x = margin_left + slot * index + (slot - bar_width) / 2.0
        y = plot_bottom - bar_height
        center = x + bar_width / 2.0
        color = _COLORS[index % len(_COLORS)]
        parts.append(
            '<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="4" fill="%s"/>'
            % (x, y, bar_width, bar_height, color)
        )
        parts.append(
            '<text x="%.1f" y="%.1f" font-size="12" fill="#33404f" '
            'text-anchor="middle">%d</text>' % (center, y - 8, value)
        )
        label = escape(name)
        if rotate_labels:
            parts.append(
                '<text x="%.1f" y="%d" font-size="12" fill="#33404f" text-anchor="end" '
                'transform="rotate(-30 %.1f %d)">%s</text>'
                % (center, plot_bottom + 22, center, plot_bottom + 22, label)
            )
        else:
            parts.append(
                '<text x="%.1f" y="%d" font-size="12" fill="#33404f" '
                'text-anchor="middle">%s</text>' % (center, plot_bottom + 24, label)
            )

    parts.append("</svg>")
    return "\n".join(parts)


def _tally_rows_html(rows: Sequence[Tuple[str, int]]) -> str:
    """生成计数符号表的表格行。"""
    items: List[str] = []
    for name, value in rows:
        items.append(
            '<tr><td>%s</td><td class="tally">%s</td><td>%d</td></tr>'
            % (escape(name), tally_marks(value), value)
        )
    return "\n".join(items)


def _frequency_rows_html(rows: Sequence[Tuple[str, int]], total: int) -> str:
    """生成频数表的表格行。"""
    items: List[str] = []
    for name, value in rows:
        if total > 0:
            share = "%.1f%%" % percentage(value, total)
        else:
            share = "—"
        items.append(
            "<tr><td>%s</td><td>%d</td><td>%s</td></tr>"
            % (escape(name), value, share)
        )
    return "\n".join(items)


def _questions_html(
    questions: Sequence[Dict[str, object]], show_answers: bool
) -> str:
    """生成读图练习列表，按需显示答案与解析。"""
    items: List[str] = []
    for item in questions:
        question = escape(str(item["question"]))
        if show_answers:
            answer = escape(str(item["answer"]))
            explanation = escape(str(item["explanation"]))
            items.append(
                '<li><p class="q">%s</p><p class="answer">答案：%s</p>'
                '<p class="hint">解析：%s</p></li>' % (question, answer, explanation)
            )
        else:
            items.append(
                '<li><p class="q">%s</p><p class="blank">答：____________________</p></li>'
                % question
            )
    return "\n".join(items)


_PAGE_TEMPLATE = Template(
    """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>$title</title>
<style>
  @page { size: A4; margin: 14mm; }
  * { box-sizing: border-box; }
  body {
    margin: 0;
    padding: 16px;
    background: #eef1f5;
    color: #1f2933;
    font-family: "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
    font-size: 14px;
    line-height: 1.6;
  }
  .sheet {
    width: 210mm;
    min-height: 297mm;
    margin: 0 auto;
    padding: 16mm 18mm;
    background: #ffffff;
    box-shadow: 0 6px 24px rgba(31, 41, 51, 0.12);
  }
  h1 { font-size: 22px; margin: 0 0 4px; text-align: center; }
  .meta { margin: 0 0 18px; color: #616e7c; text-align: center; }
  h2 { font-size: 16px; margin: 22px 0 8px; padding-left: 8px; border-left: 4px solid #4e79a7; }
  table { width: 100%; border-collapse: collapse; }
  th, td { border: 1px solid #cbd2d9; padding: 6px 8px; text-align: left; }
  th { background: #f0f4f8; font-weight: 600; }
  .tally { font-family: "Menlo", "Consolas", monospace; letter-spacing: 2px; word-break: break-all; }
  .chart { margin: 8px 0 0; text-align: center; }
  .chart svg { max-width: 100%; height: auto; }
  ol { padding-left: 22px; }
  ol li { margin-bottom: 10px; }
  .q { margin: 0; }
  .blank { margin: 2px 0 0; color: #9aa5b1; }
  .answer { margin: 2px 0 0; color: #1f6f43; font-weight: 600; }
  .hint { margin: 0; color: #616e7c; font-size: 12px; }
  .total { margin-top: 8px; text-align: right; color: #33404f; }
  footer { margin-top: 26px; padding-top: 10px; border-top: 1px dashed #cbd2d9; color: #9aa5b1; font-size: 12px; text-align: center; }
  @media print {
    body { background: #ffffff; padding: 0; }
    .sheet { box-shadow: none; margin: 0; width: auto; min-height: 0; padding: 0; }
  }
</style>
</head>
<body>
<main class="sheet">
  <h1>$title</h1>
  <p class="meta">姓名：__________　班级：__________　日期：__________</p>

  <section>
    <h2>一、计数符号</h2>
    <table>
      <thead><tr><th>类别</th><th>计数符号</th><th>频数</th></tr></thead>
      <tbody>
$tally_rows
      </tbody>
    </table>
  </section>

  <section>
    <h2>二、频数表</h2>
    <table>
      <thead><tr><th>类别</th><th>频数</th><th>占比</th></tr></thead>
      <tbody>
$frequency_rows
      </tbody>
    </table>
    <p class="total">合计：$total 个</p>
  </section>

  <section>
    <h2>三、柱状图</h2>
    <div class="chart">
$chart
    </div>
  </section>

  <section>
    <h2>四、读图练习</h2>
    <ol>
$questions
    </ol>
  </section>

  <footer>tallychart · eastyou · 计数符号与统计图</footer>
</main>
</body>
</html>
"""
)


def tally_worksheet_html(
    table: Sequence[Tuple[str, int]], title: str, show_answers: bool = False
) -> str:
    """生成自包含的 A4 可打印练习页。"""
    if not isinstance(title, str):
        raise TypeError("title 必须是字符串")
    if not isinstance(show_answers, bool):
        raise TypeError("show_answers 必须是布尔值")
    clean_title = title.strip()
    if not clean_title:
        raise ValueError("title 不能为空")
    rows = _validated_rows(table)
    if not rows:
        raise ValueError("统计表为空，无法生成练习页")

    total = sum(value for _, value in rows)
    questions = make_questions(rows, 5, 20260101)
    return _PAGE_TEMPLATE.substitute(
        title=escape(clean_title),
        tally_rows=_tally_rows_html(rows),
        frequency_rows=_frequency_rows_html(rows, total),
        total=total,
        chart=bar_chart_svg(rows, 640, 300),
        questions=_questions_html(questions, show_answers),
    )

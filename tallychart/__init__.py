"""tallychart：面向课堂的计数符号与统计图工具。"""

from .model import (
    count_marks,
    frequency_table,
    make_questions,
    max_count,
    parse_values_csv,
    percentage,
    tally_marks,
    total_count,
)
from .render import bar_chart_svg, tally_worksheet_html

__all__ = [
    "tally_marks",
    "count_marks",
    "frequency_table",
    "parse_values_csv",
    "total_count",
    "max_count",
    "percentage",
    "make_questions",
    "bar_chart_svg",
    "tally_worksheet_html",
]

__version__ = "0.1.0"

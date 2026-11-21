"""计数符号与统计图的核心数据逻辑。"""

from __future__ import annotations

import random
from typing import Dict, List, Sequence, Tuple

__all__ = [
    "tally_marks",
    "count_marks",
    "frequency_table",
    "parse_values_csv",
    "total_count",
    "max_count",
    "percentage",
    "make_questions",
]

_TALLY_GROUP = "||||/"
_GROUP_SIZE = 5


def _require_int(value: object, label: str) -> int:
    """确认 value 是真正的整数（拒绝 bool），否则抛出 TypeError。"""
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError("%s 必须是整数" % label)
    return value


def _validated_rows(table: Sequence[Tuple[str, int]]) -> List[Tuple[str, int]]:
    """校验统计表，返回去掉类别首尾空格后的新列表。"""
    if isinstance(table, (str, bytes)):
        raise TypeError("统计表必须是 (类别, 频数) 序列")
    try:
        rows = list(table)
    except TypeError:
        raise TypeError("统计表必须是 (类别, 频数) 序列") from None
    result: List[Tuple[str, int]] = []
    for index, row in enumerate(rows, start=1):
        if isinstance(row, (str, bytes)):
            raise TypeError("统计表第 %d 行必须是 (类别, 频数)" % index)
        try:
            name, value = row
        except (TypeError, ValueError):
            raise TypeError("统计表第 %d 行必须是 (类别, 频数)" % index) from None
        if not isinstance(name, str):
            raise TypeError("统计表第 %d 行的类别必须是字符串" % index)
        clean = name.strip()
        if not clean:
            raise ValueError("统计表第 %d 行的类别为空" % index)
        count = _require_int(value, "统计表第 %d 行的频数" % index)
        if count < 0:
            raise ValueError("统计表第 %d 行的频数不能为负数" % index)
        result.append((clean, count))
    return result


def tally_marks(count: int) -> str:
    """把非负整数写成计数符号：每 5 个为「||||/」，余数补「|」。"""
    count = _require_int(count, "count")
    if count < 0:
        raise ValueError("count 不能为负数")
    groups, rest = divmod(count, _GROUP_SIZE)
    return _TALLY_GROUP * groups + "|" * rest


def _parse_tally_token(token: str, rank: int) -> int:
    """解析一组以空白分隔的计数符号。"""
    index = 0
    length = len(token)
    subtotal = 0
    while index < length:
        char = token[index]
        if char == "|":
            run = 0
            while index < length and token[index] == "|":
                run += 1
                index += 1
            if index == length:
                if run > 4:
                    raise ValueError(
                        "第 %d 组计数符号末尾有 %d 个「|」，余数最多 4 个" % (rank, run)
                    )
                subtotal += run
                return subtotal
            if token[index] != "/":
                raise ValueError(
                    "第 %d 组计数符号格式错误：%d 个「|」后只能是「/」" % (rank, run)
                )
            if run != 4:
                raise ValueError(
                    "第 %d 组计数符号格式错误：「/」前必须恰好 4 个「|」，实际 %d 个"
                    % (rank, run)
                )
            subtotal += _GROUP_SIZE
            index += 1
        elif char == "/":
            raise ValueError("第 %d 组计数符号中「/」前缺少 4 个「|」" % rank)
        else:
            raise ValueError("第 %d 组计数符号包含非法字符「%s」" % (rank, char))
    return subtotal


def count_marks(text: str) -> int:
    """严格解析计数符号文本；允许用空白分隔多组。"""
    if not isinstance(text, str):
        raise TypeError("计数符号必须是字符串")
    stripped = text.strip()
    if not stripped:
        return 0
    total = 0
    for rank, token in enumerate(stripped.split(), start=1):
        total += _parse_tally_token(token, rank)
    return total


def frequency_table(values: Sequence[str]) -> List[Tuple[str, int]]:
    """按首次出现顺序统计类别频数，类别首尾空格会被去掉。"""
    if isinstance(values, (str, bytes)):
        raise TypeError("values 必须是类别序列，不能是单个字符串")
    try:
        items = list(values)
    except TypeError:
        raise TypeError("values 必须是可迭代的类别序列") from None
    counts: Dict[str, int] = {}
    order: List[str] = []
    for index, item in enumerate(items, start=1):
        if not isinstance(item, str):
            raise TypeError("第 %d 个类别必须是字符串" % index)
        name = item.strip()
        if not name:
            raise ValueError("第 %d 个类别为空，无法统计频数" % index)
        if name not in counts:
            counts[name] = 0
            order.append(name)
        counts[name] += 1
    return [(name, counts[name]) for name in order]


def parse_values_csv(text: str, has_header: bool = False) -> List[str]:
    """解析每行一个类别的 CSV，只取第一列，跳过空行与 # 注释。"""
    if not isinstance(text, str):
        raise TypeError("CSV 内容必须是字符串")
    if not isinstance(has_header, bool):
        raise TypeError("has_header 必须是布尔值")
    values: List[str] = []
    header_pending = has_header
    for number, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if header_pending:
            header_pending = False
            continue
        first = line.split(",", 1)[0].strip()
        if not first:
            raise ValueError("第 %d 行的类别为空" % number)
        values.append(first)
    return values


def total_count(table: Sequence[Tuple[str, int]]) -> int:
    """统计表所有频数之和。"""
    return sum(value for _, value in _validated_rows(table))


def max_count(table: Sequence[Tuple[str, int]]) -> int:
    """统计表中最大的频数，空表返回 0。"""
    values = [value for _, value in _validated_rows(table)]
    if not values:
        return 0
    return max(values)


def percentage(count: int, total: int) -> float:
    """计算百分比（0~100，保留一位小数）。"""
    count = _require_int(count, "count")
    total = _require_int(total, "total")
    if total <= 0:
        raise ValueError("总数必须大于 0")
    if count < 0:
        raise ValueError("count 不能为负数")
    if count > total:
        raise ValueError("count 不能大于总数")
    return round(count * 100.0 / total, 1)


def make_questions(
    table: Sequence[Tuple[str, int]], count: int = 5, seed: int = 0
) -> List[Dict[str, object]]:
    """基于统计表生成可复现的读图题。"""
    rows = _validated_rows(table)
    if not rows:
        raise ValueError("统计表为空，无法生成读图题")
    count = _require_int(count, "count")
    seed = _require_int(seed, "seed")
    if count < 1:
        raise ValueError("题目数量至少为 1")
    if count > 100:
        raise ValueError("题目数量最多为 100")

    total = sum(value for _, value in rows)
    best_name, best_value = rows[0]
    for name, value in rows[1:]:
        if value > best_value:
            best_name, best_value = name, value

    kinds = ["max", "category", "total"]
    if total > 0:
        kinds.append("percent")

    rng = random.Random(seed)
    deck: List[str] = []
    while len(deck) < count:
        block = list(kinds)
        rng.shuffle(block)
        deck.extend(block)
    deck = deck[:count]

    questions: List[Dict[str, object]] = []
    for kind in deck:
        if kind == "max":
            questions.append(
                {
                    "question": "统计表中，哪个类别的频数最多？",
                    "answer": best_name,
                    "explanation": "「%s」有 %d 个，在各类别中最多。" % (best_name, best_value),
                }
            )
        elif kind == "total":
            questions.append(
                {
                    "question": "这份统计表一共有多少个数据？",
                    "answer": str(total),
                    "explanation": "把各类别的频数相加，一共是 %d 个。" % total,
                }
            )
        else:
            name, value = rows[rng.randrange(len(rows))]
            if kind == "category":
                questions.append(
                    {
                        "question": "「%s」的频数是多少？" % name,
                        "answer": str(value),
                        "explanation": "在统计表中，「%s」出现了 %d 次。" % (name, value),
                    }
                )
            else:
                share = percentage(value, total)
                questions.append(
                    {
                        "question": "「%s」占全部数据的百分比是多少？（保留一位小数）" % name,
                        "answer": "%.1f%%" % share,
                        "explanation": "%d ÷ %d × 100%% = %.1f%%。" % (value, total, share),
                    }
                )
    return questions

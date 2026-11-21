"""render 模块的单元测试。"""

import unittest

from tallychart.model import tally_marks
from tallychart.render import bar_chart_svg, tally_worksheet_html


class BarChartSvgTests(unittest.TestCase):
    def setUp(self):
        self.table = [("苹果", 6), ("香蕉", 3)]

    def test_returns_svg_document(self):
        svg = bar_chart_svg(self.table)
        self.assertTrue(svg.startswith("<svg"))
        self.assertTrue(svg.endswith("</svg>"))
        self.assertIn('xmlns="http://www.w3.org/2000/svg"', svg)
        self.assertIn('role="img"', svg)

    def test_contains_axes_and_bars(self):
        svg = bar_chart_svg(self.table)
        self.assertGreaterEqual(svg.count("<line"), 2)
        self.assertGreaterEqual(svg.count("<rect"), 3)

    def test_contains_labels_and_counts(self):
        svg = bar_chart_svg(self.table)
        self.assertIn("苹果", svg)
        self.assertIn("香蕉", svg)
        self.assertIn(">6<", svg)
        self.assertIn(">3<", svg)

    def test_custom_size_in_viewbox(self):
        svg = bar_chart_svg(self.table, width=800, height=400)
        self.assertIn('viewBox="0 0 800 400"', svg)

    def test_escapes_category_names(self):
        svg = bar_chart_svg([("<b>", 2)])
        self.assertIn("&lt;b&gt;", svg)
        self.assertNotIn("<b>", svg)

    def test_empty_table_raises(self):
        with self.assertRaises(ValueError):
            bar_chart_svg([])

    def test_single_and_zero_counts(self):
        single = bar_chart_svg([("唯一", 4)])
        self.assertIn("唯一", single)
        self.assertTrue(single.endswith("</svg>"))
        zeros = bar_chart_svg([("a", 0), ("b", 0)])
        self.assertIn("a", zeros)
        self.assertTrue(zeros.startswith("<svg"))

    def test_large_count(self):
        self.assertIn("100000", bar_chart_svg([("大", 100000)]))

    def test_invalid_sizes(self):
        with self.assertRaises(ValueError):
            bar_chart_svg(self.table, width=0)
        with self.assertRaises(ValueError):
            bar_chart_svg(self.table, height=-10)
        with self.assertRaises(TypeError):
            bar_chart_svg(self.table, width=True)
        with self.assertRaises(ValueError):
            bar_chart_svg(self.table, width=80, height=80)

    def test_many_categories_rotates_labels(self):
        table = [("类别%d" % index, index + 1) for index in range(9)]
        svg = bar_chart_svg(table)
        self.assertIn("类别8", svg)
        self.assertIn("rotate(-30", svg)


class WorksheetHtmlTests(unittest.TestCase):
    def setUp(self):
        self.table = [("苹果", 6), ("香蕉", 3), ("橘子", 1)]

    def test_is_complete_html(self):
        page = tally_worksheet_html(self.table, "水果统计")
        self.assertTrue(page.startswith("<!DOCTYPE html>"))
        self.assertIn('<meta charset="utf-8">', page)
        self.assertIn("</html>", page)

    def test_contains_print_styles(self):
        page = tally_worksheet_html(self.table, "水果统计")
        self.assertIn("@page", page)
        self.assertIn("size: A4", page)
        self.assertIn("@media print", page)

    def test_contains_sections(self):
        page = tally_worksheet_html(self.table, "水果统计")
        for heading in ("计数符号", "频数表", "柱状图", "读图练习"):
            self.assertIn(heading, page)

    def test_contains_tally_marks_and_chart(self):
        page = tally_worksheet_html(self.table, "水果统计")
        self.assertIn(tally_marks(6), page)
        self.assertIn("<svg", page)
        self.assertIn("</svg>", page)

    def test_contains_frequency_rows(self):
        page = tally_worksheet_html(self.table, "水果统计")
        self.assertIn("<td>苹果</td>", page)
        self.assertIn("<td>60.0%</td>", page)
        self.assertIn("合计：10 个", page)

    def test_answers_hidden_by_default(self):
        page = tally_worksheet_html(self.table, "水果统计")
        self.assertNotIn("答案：", page)
        self.assertIn("____", page)

    def test_answers_shown_when_requested(self):
        page = tally_worksheet_html(self.table, "水果统计", True)
        self.assertIn("答案：", page)
        self.assertIn("解析：", page)

    def test_title_and_names_are_escaped(self):
        page = tally_worksheet_html([("<b>", 2)], "<script>")
        self.assertIn("&lt;script&gt;", page)
        self.assertIn("&lt;b&gt;", page)
        self.assertNotIn("<title><script>", page)
        self.assertNotIn("<td><b></td>", page)

    def test_empty_table_or_title_raises(self):
        with self.assertRaises(ValueError):
            tally_worksheet_html([], "统计")
        with self.assertRaises(ValueError):
            tally_worksheet_html(self.table, "   ")

    def test_invalid_argument_types(self):
        with self.assertRaises(TypeError):
            tally_worksheet_html(self.table, None)
        with self.assertRaises(TypeError):
            tally_worksheet_html(self.table, "统计", "yes")

    def test_zero_table_and_self_contained(self):
        page = tally_worksheet_html([("a", 0), ("b", 0)], "统计")
        self.assertIn("—", page)
        self.assertIn("合计：0 个", page)
        clean = tally_worksheet_html(self.table, "水果统计")
        self.assertNotIn("<link", clean)
        self.assertNotIn("<script", clean)
        self.assertNotIn("https://", clean)


if __name__ == "__main__":
    unittest.main()

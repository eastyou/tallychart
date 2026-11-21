"""cli 模块的单元测试。"""

import contextlib
import io
import tempfile
import unittest
from pathlib import Path

from tallychart.cli import main


def run_cli(argv):
    """执行 main 并捕获标准输出/标准错误。"""
    out = io.StringIO()
    err = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = main(argv)
    return code, out.getvalue(), err.getvalue()


class MarksCommandTests(unittest.TestCase):
    def test_marks_seven(self):
        code, out, err = run_cli(["marks", "7"])
        self.assertEqual(code, 0)
        self.assertEqual(out, "||||/||\n")
        self.assertEqual(err, "")

    def test_marks_zero_and_ten(self):
        code, out, _ = run_cli(["marks", "0"])
        self.assertEqual(code, 0)
        self.assertEqual(out.strip(), "")
        code, out, _ = run_cli(["marks", "10"])
        self.assertEqual(code, 0)
        self.assertEqual(out.strip(), "||||/||||/")

    def test_marks_negative_exit_code(self):
        code, out, err = run_cli(["marks", "-3"])
        self.assertEqual(code, 2)
        self.assertEqual(out, "")
        self.assertIn("错误：", err)

    def test_marks_non_integer_uses_argparse(self):
        with self.assertRaises(SystemExit) as context:
            run_cli(["marks", "abc"])
        self.assertEqual(context.exception.code, 2)


class CountCommandTests(unittest.TestCase):
    def test_count_marks(self):
        code, out, _ = run_cli(["count", "||||/||"])
        self.assertEqual(code, 0)
        self.assertEqual(out, "7\n")

    def test_count_empty_string(self):
        code, out, _ = run_cli(["count", ""])
        self.assertEqual(code, 0)
        self.assertEqual(out, "0\n")

    def test_count_space_separated(self):
        code, out, _ = run_cli(["count", "||||/ ||||/"])
        self.assertEqual(code, 0)
        self.assertEqual(out, "10\n")

    def test_count_invalid_returns_two(self):
        code, out, err = run_cli(["count", "abc"])
        self.assertEqual(code, 2)
        self.assertEqual(out, "")
        self.assertIn("错误：", err)
        self.assertIn("计数符号", err)


class TableCommandTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)

    def tearDown(self):
        self.directory.cleanup()

    def write_csv(self, name, content):
        path = self.root / name
        path.write_text(content, encoding="utf-8")
        return str(path)

    def test_table_output(self):
        csv_path = self.write_csv(
            "data.csv", "苹果\n香蕉\n苹果\n苹果\n苹果\n苹果\n苹果\n"
        )
        code, out, _ = run_cli(["table", csv_path])
        self.assertEqual(code, 0)
        self.assertIn("类别", out)
        self.assertIn("苹果\t6\t||||/|", out)
        self.assertIn("合计\t7\t", out)

    def test_table_with_header(self):
        csv_path = self.write_csv("data.csv", "水果\n苹果\n苹果\n")
        code, out, _ = run_cli(["table", csv_path, "--header"])
        self.assertEqual(code, 0)
        self.assertNotIn("水果\t", out)
        self.assertIn("苹果\t2", out)

    def test_table_missing_file(self):
        code, out, err = run_cli(["table", str(self.root / "missing.csv")])
        self.assertEqual(code, 2)
        self.assertEqual(out, "")
        self.assertIn("错误：", err)

    def test_table_empty_csv(self):
        csv_path = self.write_csv("empty.csv", "# 只有注释\n\n")
        code, _, err = run_cli(["table", csv_path])
        self.assertEqual(code, 2)
        self.assertIn("没有可统计的类别", err)

    def test_table_empty_category_reports_line(self):
        csv_path = self.write_csv("bad.csv", "苹果\n,3\n")
        code, _, err = run_cli(["table", csv_path])
        self.assertEqual(code, 2)
        self.assertIn("第 2 行", err)


class ChartCommandTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)

    def tearDown(self):
        self.directory.cleanup()

    def write_csv(self, name, content):
        path = self.root / name
        path.write_text(content, encoding="utf-8")
        return str(path)

    def test_chart_writes_html(self):
        csv_path = self.write_csv("data.csv", "苹果\n香蕉\n苹果\n")
        output = self.root / "out.html"
        code, out, err = run_cli(["chart", csv_path, "-o", str(output)])
        self.assertEqual(code, 0)
        self.assertEqual(err, "")
        self.assertTrue(output.exists())
        page = output.read_text(encoding="utf-8")
        self.assertIn("<!DOCTYPE html>", page)
        self.assertIn("<svg", page)
        self.assertIn("苹果", page)
        self.assertIn("out.html", out)

    def test_chart_with_title(self):
        csv_path = self.write_csv("data.csv", "苹果\n")
        output = self.root / "title.html"
        code, _, _ = run_cli(
            ["chart", csv_path, "-o", str(output), "--title", "三年级统计"]
        )
        self.assertEqual(code, 0)
        self.assertIn("三年级统计", output.read_text(encoding="utf-8"))

    def test_chart_with_header(self):
        csv_path = self.write_csv("data.csv", "苹果\n香蕉\n")
        output = self.root / "header.html"
        code, _, _ = run_cli(["chart", csv_path, "-o", str(output), "--header"])
        self.assertEqual(code, 0)
        page = output.read_text(encoding="utf-8")
        self.assertNotIn("苹果", page)
        self.assertIn("香蕉", page)

    def test_chart_errors(self):
        code, out, err = run_cli(
            ["chart", str(self.root / "missing.csv"), "-o", str(self.root / "x.html")]
        )
        self.assertEqual(code, 2)
        self.assertEqual(out, "")
        self.assertIn("错误：", err)
        csv_path = self.write_csv("empty.csv", "\n\n")
        code, _, err = run_cli(
            ["chart", csv_path, "-o", str(self.root / "empty.html")]
        )
        self.assertEqual(code, 2)
        self.assertIn("没有可统计的类别", err)


class DemoCommandTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)

    def tearDown(self):
        self.directory.cleanup()

    def test_demo_generates_page(self):
        output = self.root / "demo.html"
        code, out, err = run_cli(["demo", "-o", str(output)])
        self.assertEqual(code, 0)
        self.assertEqual(err, "")
        self.assertTrue(output.exists())
        page = output.read_text(encoding="utf-8")
        self.assertIn("读图练习", page)
        self.assertIn("<svg", page)
        self.assertIn("苹果", page)
        self.assertNotIn("答案：", page)
        self.assertIn("demo.html", out)


class ParserTests(unittest.TestCase):
    def test_help_exits_zero(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            with self.assertRaises(SystemExit) as context:
                main(["--help"])
        self.assertEqual(context.exception.code, 0)
        text = out.getvalue()
        self.assertIn("tallychart", text)
        self.assertIn("marks", text)
        self.assertIn("demo", text)

    def test_no_arguments_exits_two(self):
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as context:
                main([])
        self.assertEqual(context.exception.code, 2)

    def test_unknown_command_exits_two(self):
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as context:
                main(["unknown"])
        self.assertEqual(context.exception.code, 2)


if __name__ == "__main__":
    unittest.main()

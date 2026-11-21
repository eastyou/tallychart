"""model 模块的单元测试。"""

import unittest

from tallychart.model import (
    count_marks,
    frequency_table,
    make_questions,
    max_count,
    parse_values_csv,
    percentage,
    tally_marks,
    total_count,
)


class TallyMarksTests(unittest.TestCase):
    def test_zero_returns_empty_string(self):
        self.assertEqual(tally_marks(0), "")

    def test_small_counts(self):
        self.assertEqual(tally_marks(1), "|")
        self.assertEqual(tally_marks(4), "||||")
        self.assertEqual(tally_marks(7), "||||/||")

    def test_multiple_groups(self):
        cases = {
            5: "||||/",
            10: "||||/||||/",
            12: "||||/||||/||",
            1003: "||||/" * 200 + "|||",
        }
        for number, expected in cases.items():
            with self.subTest(number=number):
                self.assertEqual(tally_marks(number), expected)

    def test_negative_raises_value_error(self):
        with self.assertRaises(ValueError):
            tally_marks(-1)

    def test_invalid_types_are_rejected(self):
        for value in (True, 2.0, "7", None):
            with self.subTest(value=value):
                with self.assertRaises(TypeError):
                    tally_marks(value)


class CountMarksTests(unittest.TestCase):
    def test_empty_and_whitespace(self):
        self.assertEqual(count_marks(""), 0)
        self.assertEqual(count_marks("   \n\t "), 0)

    def test_basic_tokens(self):
        cases = {
            "|": 1,
            "||||": 4,
            "||||/": 5,
            "||||/||": 7,
            "||||/||||/": 10,
        }
        for text, expected in cases.items():
            with self.subTest(text=text):
                self.assertEqual(count_marks(text), expected)

    def test_space_separated_groups(self):
        self.assertEqual(count_marks("  ||||/ ||||/| "), 11)

    def test_round_trip(self):
        for number in (0, 1, 4, 5, 7, 10, 19, 20, 123, 1000, 12345):
            with self.subTest(number=number):
                self.assertEqual(count_marks(tally_marks(number)), number)

    def test_invalid_tokens(self):
        for text in (
            "||||/x",
            "abc",
            "/",
            "||||//",
            "|||||",
            "||||||/",
            "|||/",
            "||||/|/",
            "|| ||/",
            "|||| /",
        ):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    count_marks(text)

    def test_remainder_after_group(self):
        self.assertEqual(count_marks("||||/|"), 6)

    def test_non_string_rejected(self):
        with self.assertRaises(TypeError):
            count_marks(7)

    def test_error_message_is_chinese(self):
        with self.assertRaises(ValueError) as context:
            count_marks("abc")
        self.assertIn("计数符号", str(context.exception))


class FrequencyTableTests(unittest.TestCase):
    def test_counts_and_order(self):
        self.assertEqual(
            frequency_table(["b", "a", "b", "c", "a"]),
            [("b", 2), ("a", 2), ("c", 1)],
        )

    def test_trims_whitespace(self):
        self.assertEqual(frequency_table([" 苹果 ", "苹果"]), [("苹果", 2)])

    def test_empty_and_single(self):
        self.assertEqual(frequency_table([]), [])
        self.assertEqual(frequency_table(["苹果"]), [("苹果", 1)])

    def test_empty_item_raises(self):
        with self.assertRaises(ValueError):
            frequency_table(["苹果", "   "])

    def test_invalid_inputs(self):
        with self.assertRaises(TypeError):
            frequency_table(["苹果", 3])
        with self.assertRaises(TypeError):
            frequency_table("苹果香蕉")
        with self.assertRaises(TypeError):
            frequency_table(None)

    def test_large_input(self):
        table = frequency_table(["x", "y"] * 5000)
        self.assertEqual(table, [("x", 5000), ("y", 5000)])


class ParseValuesCsvTests(unittest.TestCase):
    def test_basic_rows_and_first_column(self):
        text = "苹果,3\n香蕉,1\n苹果,2\n"
        self.assertEqual(parse_values_csv(text), ["苹果", "香蕉", "苹果"])

    def test_header_skipped(self):
        self.assertEqual(
            parse_values_csv("类别\n苹果\n香蕉\n", True), ["苹果", "香蕉"]
        )

    def test_comments_and_blank_lines(self):
        text = "# 注释\n\n苹果\n# 另一条注释\n香蕉\n"
        self.assertEqual(parse_values_csv(text), ["苹果", "香蕉"])

    def test_empty_inputs(self):
        self.assertEqual(parse_values_csv(""), [])
        self.assertEqual(parse_values_csv("# a\n# b\n"), [])
        self.assertEqual(parse_values_csv("类别\n", True), [])

    def test_header_after_comments(self):
        self.assertEqual(parse_values_csv("# 说明\n类别\n苹果\n", True), ["苹果"])

    def test_empty_category_reports_line_number(self):
        cases = (
            ("苹果\n,3\n香蕉\n", "第 2 行"),
            ("类别\n\n,1\n", "第 3 行"),
        )
        for text, expected in cases:
            with self.subTest(text=text):
                with self.assertRaises(ValueError) as context:
                    parse_values_csv(text, text.startswith("类别"))
                self.assertIn(expected, str(context.exception))

    def test_invalid_arguments(self):
        with self.assertRaises(TypeError):
            parse_values_csv(None)
        with self.assertRaises(TypeError):
            parse_values_csv("苹果\n", "yes")

    def test_crlf_input(self):
        self.assertEqual(parse_values_csv("苹果\r\n香蕉\r\n"), ["苹果", "香蕉"])


class TotalAndMaxTests(unittest.TestCase):
    def test_total(self):
        self.assertEqual(total_count([("a", 2), ("b", 3)]), 5)

    def test_total_empty_and_zeros(self):
        self.assertEqual(total_count([]), 0)
        self.assertEqual(total_count([("a", 0), ("b", 0)]), 0)

    def test_total_invalid_rows(self):
        cases = (
            ([("a", -1)], ValueError),
            ([("a",)], TypeError),
            ([("a", 1.5)], TypeError),
        )
        for table, expected in cases:
            with self.subTest(table=table):
                with self.assertRaises(expected):
                    total_count(table)

    def test_max_values(self):
        self.assertEqual(max_count([]), 0)
        self.assertEqual(max_count([("a", 2), ("b", 7), ("c", 3)]), 7)
        self.assertEqual(max_count([("a", 4)]), 4)
        self.assertEqual(max_count([("a", 0), ("b", 0)]), 0)


class PercentageTests(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(percentage(1, 4), 25.0)
        self.assertEqual(percentage(0, 5), 0.0)
        self.assertEqual(percentage(5, 5), 100.0)

    def test_rounded_to_one_decimal(self):
        self.assertEqual(percentage(2, 3), 66.7)

    def test_invalid_total(self):
        with self.assertRaises(ValueError):
            percentage(0, 0)
        with self.assertRaises(ValueError):
            percentage(1, -5)

    def test_invalid_count(self):
        with self.assertRaises(ValueError):
            percentage(-1, 5)
        with self.assertRaises(ValueError):
            percentage(6, 5)

    def test_invalid_types(self):
        with self.assertRaises(TypeError):
            percentage(True, 5)
        with self.assertRaises(TypeError):
            percentage(1.0, 5)


class MakeQuestionsTests(unittest.TestCase):
    def setUp(self):
        self.table = [("苹果", 6), ("香蕉", 3), ("橘子", 1)]

    def test_counts(self):
        self.assertEqual(len(make_questions(self.table)), 5)
        self.assertEqual(len(make_questions(self.table, 3)), 3)

    def test_reproducible_with_seed(self):
        self.assertEqual(
            make_questions(self.table, 8, 42), make_questions(self.table, 8, 42)
        )

    def test_question_fields(self):
        for item in make_questions(self.table, 10, 7):
            self.assertEqual(
                sorted(item.keys()), ["answer", "explanation", "question"]
            )
            for value in item.values():
                self.assertIsInstance(value, str)
                self.assertTrue(value)

    def test_invalid_count(self):
        with self.assertRaises(ValueError):
            make_questions(self.table, 0)
        with self.assertRaises(ValueError):
            make_questions(self.table, 101)
        with self.assertRaises(ValueError):
            make_questions([])

    def test_invalid_types(self):
        with self.assertRaises(TypeError):
            make_questions(self.table, "5")
        with self.assertRaises(TypeError):
            make_questions(self.table, 3, True)

    def test_single_and_zero_tables(self):
        single = make_questions([("唯一", 9)], 5, 1)
        self.assertEqual(len(single), 5)
        for item in single:
            if "一共" in str(item["question"]):
                self.assertEqual(item["answer"], "9")
                continue
            combined = str(item["question"]) + str(item["explanation"])
            self.assertIn("唯一", combined)
        zero = make_questions([("a", 0), ("b", 0)], 4, 3)
        self.assertEqual(len(zero), 4)
        for item in zero:
            self.assertIsInstance(item["answer"], str)

    def test_total_question(self):
        questions = make_questions(self.table, 40, 2026)
        totals = [q for q in questions if "一共" in str(q["question"])]
        self.assertTrue(totals)
        for item in totals:
            self.assertEqual(item["answer"], "10")


if __name__ == "__main__":
    unittest.main()

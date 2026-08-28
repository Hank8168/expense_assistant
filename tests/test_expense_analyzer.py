import io
import unittest

import pandas as pd

from expense_analyzer import ( #匯入測試函式
    analyze_expenses,
    calculate_category_expenses,
    calculate_total_expense,
    find_largest_expense,
    load_expenses,
)


class ExpenseAnalyzerTests(unittest.TestCase): #建立測試資料
    def setUp(self) -> None:
        self.expenses = pd.DataFrame(
            {
                "date": pd.to_datetime(["2026-08-01", "2026-08-02", "2026-08-03"]),
                "description": ["早餐", "公車", "晚餐"],
                "category": ["餐飲", "交通", "餐飲"],
                "amount": [100, 50, 300],
            }
        )

    def test_calculate_total_expense(self) -> None: #測試總輸出
        self.assertEqual(calculate_total_expense(self.expenses), 450.0)

    def test_calculate_category_expenses(self) -> None:
        result = calculate_category_expenses(self.expenses)
        self.assertEqual(result.to_dict(), {"餐飲": 400, "交通": 50})

    def test_find_largest_expense(self) -> None:
        result = find_largest_expense(self.expenses)
        self.assertIsNotNone(result)
        self.assertEqual(result["description"], "晚餐")
        self.assertEqual(result["amount"], 300)

    def test_find_largest_expense_with_empty_data(self) -> None:
        empty = self.expenses.iloc[0:0]
        self.assertIsNone(find_largest_expense(empty))

    def test_load_expenses_parses_csv(self) -> None:
        csv_data = io.StringIO(
            "date,description,category,amount\n2026-08-01,早餐,餐飲,85.5\n"
        )
        result = load_expenses(csv_data)
        self.assertEqual(result.loc[0, "amount"], 85.5)
        self.assertTrue(pd.api.types.is_datetime64_any_dtype(result["date"]))

    def test_load_expenses_rejects_missing_column(self) -> None:
        csv_data = io.StringIO("date,description,amount\n2026-08-01,早餐,85\n")
        with self.assertRaisesRegex(ValueError, "category"):
            load_expenses(csv_data)

    def test_load_expenses_rejects_invalid_amount(self) -> None:
        csv_data = io.StringIO(
            "date,description,category,amount\n2026-08-01,早餐,餐飲,錯誤\n"
        )
        with self.assertRaisesRegex(ValueError, "amount"):
            load_expenses(csv_data)

    def test_analyze_expenses_returns_all_results(self) -> None:
        result = analyze_expenses(self.expenses)
        self.assertEqual(result["total"], 450.0)
        self.assertEqual(result["by_category"].to_dict(), {"餐飲": 400, "交通": 50})
        self.assertEqual(result["largest"]["description"], "晚餐")


if __name__ == "__main__":
    unittest.main()

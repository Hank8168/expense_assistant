import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pandas as pd
from google.genai import errors

from llm_agent import (
    GeminiNetworkError,
    GeminiQuotaError,
    MissingAPIKeyError,
    ask_expense_agent,
)


class LLMAgentTests(unittest.TestCase):
    def setUp(self) -> None:
        self.expenses = pd.DataFrame(
            {
                "date": pd.to_datetime(["2026-08-01", "2026-08-02"]),
                "description": ["早餐", "車票"],
                "category": ["餐飲", "交通"],
                "amount": [100, 250],
            }
        )

    @staticmethod
    def _response(*, text=None, function_calls=None):
        return SimpleNamespace(
            text=text,
            function_calls=function_calls,
            candidates=[SimpleNamespace(content=SimpleNamespace(parts=[]))],
        )

    def test_total_expense_tool_uses_expense_analyzer(self) -> None:
        function_call = SimpleNamespace(name="get_total_expense", id="call-1")
        client = Mock()
        client.models.generate_content.side_effect = [
            self._response(function_calls=[function_call]),
            self._response(text="你的總支出是 NT$ 350.00。", function_calls=[]),
        ]

        with patch("llm_agent.calculate_total_expense", return_value=350.0) as calculate:
            result = ask_expense_agent("我的總支出是多少？", self.expenses, "fake-key", client=client)

        calculate.assert_called_once_with(self.expenses)
        self.assertEqual(result.tool_names, ["get_total_expense"])
        self.assertIn("350", result.answer)
        self.assertEqual(client.models.generate_content.call_count, 2)

    def test_category_and_largest_tools_are_available(self) -> None:
        calls = [
            SimpleNamespace(name="get_category_expenses", id="call-1"),
            SimpleNamespace(name="get_largest_expense", id="call-2"),
        ]
        client = Mock()
        client.models.generate_content.side_effect = [
            self._response(function_calls=calls),
            self._response(text="交通分類最高，最大筆是車票。", function_calls=[]),
        ]

        result = ask_expense_agent("哪個分類最高，最大筆是什麼？", self.expenses, "fake-key", client=client)

        self.assertEqual(
            result.tool_names,
            ["get_category_expenses", "get_largest_expense"],
        )

    def test_missing_api_key_does_not_call_api(self) -> None:
        client = Mock()
        with self.assertRaises(MissingAPIKeyError):
            ask_expense_agent("總支出？", self.expenses, None, client=client)
        client.models.generate_content.assert_not_called()

    def test_question_over_200_characters_does_not_call_api(self) -> None:
        client = Mock()
        with self.assertRaisesRegex(ValueError, "200"):
            ask_expense_agent("問" * 201, self.expenses, "fake-key", client=client)
        client.models.generate_content.assert_not_called()

    def test_quota_error_is_converted_to_chinese_message(self) -> None:
        client = Mock()
        client.models.generate_content.side_effect = errors.ClientError(
            429,
            {"error": {"code": 429, "status": "RESOURCE_EXHAUSTED"}},
        )
        with self.assertRaisesRegex(GeminiQuotaError, "免費額度"):
            ask_expense_agent("總支出？", self.expenses, "fake-key", client=client)

    def test_network_error_is_converted_to_chinese_message(self) -> None:
        client = Mock()
        client.models.generate_content.side_effect = errors.ServerError(
            503,
            {"error": {"code": 503, "status": "UNAVAILABLE"}},
        )
        with self.assertRaisesRegex(GeminiNetworkError, "暫時無法連線"):
            ask_expense_agent("總支出？", self.expenses, "fake-key", client=client)


if __name__ == "__main__":
    unittest.main()

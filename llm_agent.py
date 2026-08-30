#使用Gemini Function Calling回答消費分析問題
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx
import pandas as pd
from google import genai
from google.genai import errors, types

from expense_analyzer import (
    calculate_category_expenses,
    calculate_total_expense,
    find_largest_expense,
)


MODEL_NAME = "gemini-3.5-flash-lite"
MAX_QUESTION_LENGTH = 200
MAX_TOOL_ROUNDS = 3


class GeminiAgentError(Exception):
    """可安全顯示給使用者的Gemini Agent 錯誤"""


class MissingAPIKeyError(GeminiAgentError):
    """找不到Gemini API Key"""


class GeminiQuotaError(GeminiAgentError):
    """Gemini免費額度或速率限制已用完"""


class GeminiNetworkError(GeminiAgentError):
    """Gemini網路或暫時性服務錯誤"""


@dataclass(frozen=True)
class AgentResult:
    """AI最終回答與實際呼叫的工具名稱"""

    answer: str
    tool_names: list[str]


def _build_tools(expenses: pd.DataFrame) -> tuple[list[Any], dict[str, Any]]:
    """建立只能透過expense_analyzer計算金額的三個工具"""

    def get_total_expense() -> dict[str, float]:
        """查詢目前消費資料的總支出"""
        return {"total_expense": calculate_total_expense(expenses)}

    def get_category_expenses() -> dict[str, list[dict[str, Any]]]:
        """查詢目前消費資料中每個分類的支出總額"""
        category_expenses = calculate_category_expenses(expenses)
        return {
            "category_expenses": [
                {"category": str(category), "amount": float(amount)}
                for category, amount in category_expenses.items()
            ]
        }

    def get_largest_expense() -> dict[str, Any]:
        """查詢目前消費資料中金額最大的單筆支出"""
        largest = find_largest_expense(expenses)
        if largest is None:
            return {"largest_expense": None}
        return {
            "largest_expense": {
                "date": largest["date"].strftime("%Y-%m-%d"),
                "description": str(largest["description"]),
                "category": str(largest["category"]),
                "amount": float(largest["amount"]),
            }
        }

    functions = {
        "get_total_expense": get_total_expense,
        "get_category_expenses": get_category_expenses,
        "get_largest_expense": get_largest_expense,
    }
    declarations = [
        types.FunctionDeclaration(
            name=name,
            description=function.__doc__,
            parameters_json_schema={"type": "object", "properties": {}},
        )
        for name, function in functions.items()
    ]
    return [types.Tool(function_declarations=declarations)], functions


def _generate_content(client: Any, **kwargs: Any) -> Any:
    """呼叫Gemini並將外部服務錯誤轉成中文友善錯誤"""
    try:
        return client.models.generate_content(**kwargs)
    except errors.APIError as exc:
        if exc.code == 429:
            raise GeminiQuotaError(
                "Gemini免費額度或速率限制已用完，請稍後再試。"
            ) from exc
        if exc.code in {408, 500, 502, 503, 504}:
            raise GeminiNetworkError(
                "Gemini服務暫時無法連線，請稍後再試，原本的消費分析仍可使用。"
            ) from exc
        raise GeminiAgentError(
            "Gemini API無法處理此請求，請確認API Key與模型存取權限。"
        ) from exc
    except httpx.HTTPError as exc:
        raise GeminiNetworkError(
            "無法連線到Gemini，請檢查網路後再試，原本的消費分析仍可使用。"
        ) from exc


def ask_expense_agent(
    question: str,
    expenses: pd.DataFrame,
    api_key: str | None,
    *,
    client: Any | None = None,
) -> AgentResult:
    """讓Gemini選擇分析工具，並根據工具結果產生中文回答。"""
    question = question.strip()
    if not question:
        raise ValueError("請輸入問題。")
    if len(question) > MAX_QUESTION_LENGTH:
        raise ValueError(f"問題不可超過 {MAX_QUESTION_LENGTH} 個字。")
    if expenses.empty:
        raise ValueError("目前沒有可供AI分析的消費資料。")
    if not api_key:
        raise MissingAPIKeyError(
            "找不到Gemini API Key，請設定GEMINI_API_KEY環境變數或Streamlit secrets。"
        )

    gemini_client = client or genai.Client(api_key=api_key)
    tools, available_functions = _build_tools(expenses)
    config_values = {
        "system_instruction": (
            "你是個人消費分析助手。請使用繁體中文簡潔回答。"
            "凡是涉及金額、分類加總或最大支出，都必須先呼叫提供的工具；"
            "不可自行計算、猜測、修改或捏造任何金額。"
            "工具回傳值是唯一可信的金額來源。"
        ),
        "tools": tools,
        "automatic_function_calling": types.AutomaticFunctionCallingConfig(
            disable=True
        ),
        "temperature": 0,
    }
    first_call_config = types.GenerateContentConfig(
        **config_values,
        tool_config=types.ToolConfig(
            function_calling_config=types.FunctionCallingConfig(mode="ANY")
        ),
    )
    answer_config = types.GenerateContentConfig(
        **config_values,
        tool_config=types.ToolConfig(
            function_calling_config=types.FunctionCallingConfig(mode="AUTO")
        ),
    )
    contents: list[Any] = [
        types.Content(role="user", parts=[types.Part.from_text(text=question)])
    ]
    called_tools: list[str] = []

    for _ in range(MAX_TOOL_ROUNDS):
        response = _generate_content(
            gemini_client,
            model=MODEL_NAME,
            contents=contents,
            config=first_call_config if not called_tools else answer_config,
        )
        function_calls = response.function_calls or []
        if not function_calls:
            answer = (response.text or "").strip()
            if not answer:
                raise GeminiAgentError("Gemini沒有產生可顯示的回答，請換個方式提問。")
            return AgentResult(answer=answer, tool_names=called_tools)

        contents.append(response.candidates[0].content)
        function_response_parts = []
        for function_call in function_calls:
            tool_name = function_call.name
            function = available_functions.get(tool_name)
            if function is None:
                tool_result = {"error": f"不支援的工具：{tool_name}"}
            else:
                tool_result = {"result": function()}
                called_tools.append(tool_name)
            function_response_parts.append(
                types.Part.from_function_response(
                    name=tool_name,
                    response=tool_result,
                )
            )
        contents.append(types.Content(role="user", parts=function_response_parts))

    raise GeminiAgentError("Gemini呼叫工具次數過多，請將問題簡化後再試。")

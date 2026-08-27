"""消費紀錄的讀取、驗證與統計功能。"""

from __future__ import annotations

from pathlib import Path
from typing import IO, Any

import pandas as pd


REQUIRED_COLUMNS = ("date", "description", "category", "amount")


def load_expenses(source: str | Path | IO[Any]) -> pd.DataFrame:
    """從 CSV 讀取並驗證消費紀錄。"""
    try:
        expenses = pd.read_csv(source)
    except (pd.errors.EmptyDataError, pd.errors.ParserError, UnicodeDecodeError) as exc:
        raise ValueError("無法讀取 CSV，請確認檔案包含有效的 UTF-8 CSV 資料。") from exc

    missing_columns = [
        column for column in REQUIRED_COLUMNS if column not in expenses.columns
    ]
    if missing_columns:
        raise ValueError(f"CSV 缺少必要欄位：{', '.join(missing_columns)}")

    expenses = expenses.loc[:, list(REQUIRED_COLUMNS)].copy()

    try:
        expenses["amount"] = pd.to_numeric(expenses["amount"], errors="raise")
    except (TypeError, ValueError) as exc:
        raise ValueError("amount 欄位必須全部為數字。") from exc

    invalid_text = expenses[["description", "category"]].isna().any(axis=1)
    invalid_text |= (
        expenses[["description", "category"]]
        .astype(str)
        .apply(lambda column: column.str.strip().eq(""))
        .any(axis=1)
    )
    if invalid_text.any():
        raise ValueError("description 與 category 欄位不可為空白。")

    try:
        expenses["date"] = pd.to_datetime(expenses["date"], errors="raise")
    except (TypeError, ValueError) as exc:
        raise ValueError("date 欄位包含無效日期。") from exc

    return expenses


def calculate_total_expense(expenses: pd.DataFrame) -> float:
    """計算總支出。"""
    return float(expenses["amount"].sum())


def calculate_category_expenses(expenses: pd.DataFrame) -> pd.Series:
    """依分類加總支出，並由高至低排序。"""
    return (
        expenses.groupby("category", sort=False)["amount"]
        .sum()
        .sort_values(ascending=False)
    )


def find_largest_expense(expenses: pd.DataFrame) -> pd.Series | None:
    """找出最大筆支出；空資料時回傳 None。"""
    if expenses.empty:
        return None
    return expenses.loc[expenses["amount"].idxmax()].copy()


def analyze_expenses(expenses: pd.DataFrame) -> dict[str, object]:
    """產生介面所需的完整分析結果。"""
    return {
        "total": calculate_total_expense(expenses),
        "by_category": calculate_category_expenses(expenses),
        "largest": find_largest_expense(expenses),
    }

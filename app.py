"""個人消費分析助手的 Streamlit 介面。"""

from pathlib import Path

import streamlit as st

from expense_analyzer import analyze_expenses, load_expenses


SAMPLE_CSV_PATH = Path(__file__).with_name("sample_expenses.csv")

st.set_page_config(page_title="個人消費分析助手", page_icon="💰", layout="wide")
st.title("💰 個人消費分析助手")
st.write("上傳消費紀錄 CSV，即可查看總支出、分類支出與最大筆支出。")

with SAMPLE_CSV_PATH.open("rb") as sample_file:
    st.download_button(
        "下載範例 CSV",
        data=sample_file.read(),
        file_name="sample_expenses.csv",
        mime="text/csv",
    )

uploaded_file = st.file_uploader("上傳 CSV", type=["csv"])

if uploaded_file is not None:
    try:
        expense_data = load_expenses(uploaded_file)
        analysis = analyze_expenses(expense_data)
    except ValueError as error:
        st.error(str(error))
    else:
        if expense_data.empty:
            st.warning("CSV 沒有任何消費紀錄。")
        else:
            largest = analysis["largest"]
            total_column, largest_column = st.columns(2)
            total_column.metric("總支出", f"NT$ {analysis['total']:,.2f}")
            largest_column.metric(
                "最大筆支出",
                f"NT$ {largest['amount']:,.2f}",
                help=f"{largest['date']:%Y-%m-%d}｜{largest['description']}｜{largest['category']}",
            )

            st.subheader("分類支出")
            category_expenses = analysis["by_category"].rename("支出金額")
            st.bar_chart(category_expenses)
            st.dataframe(category_expenses.to_frame(), use_container_width=True)

            st.subheader("消費明細")
            display_data = expense_data.copy()
            display_data["date"] = display_data["date"].dt.strftime("%Y-%m-%d")
            st.dataframe(display_data, use_container_width=True, hide_index=True)

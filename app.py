#個人消費分析助手的 Streamlit 介面

import os
from pathlib import Path
import streamlit as st
from expense_analyzer import analyze_expenses, load_expenses #呼叫
from llm_agent import (
    GeminiAgentError,
    MAX_QUESTION_LENGTH,
    MissingAPIKeyError,
    ask_expense_agent,
)


SAMPLE_CSV_PATH = Path(__file__).with_name("sample_expenses.csv")

st.set_page_config(page_title="個人消費分析助手", page_icon="💰", layout="wide")
st.title("💰 個人消費分析助手")
st.write("上傳消費紀錄 CSV，即可查看總支出、分類支出與最大筆支出。")

sample_csv_bytes = SAMPLE_CSV_PATH.read_text(encoding="utf-8-sig").encode("utf-8-sig")
st.download_button(
    "下載範例 CSV",
    data=sample_csv_bytes,
    file_name="sample_expenses.csv",
    mime="text/csv",
)

uploaded_file = st.file_uploader("上傳 CSV", type=["csv"])

if uploaded_file is not None:
    try:
        expense_data = load_expenses(uploaded_file) #讀取並驗證CSV
        analysis = analyze_expenses(expense_data)#計算統計結果並存入analysis
    except ValueError as error:
        st.error(str(error))
    else:
        if expense_data.empty:
            st.warning("CSV 沒有任何消費紀錄。")
        else:
            largest = analysis["largest"]
            total_column, largest_column = st.columns(2)
            total_column.metric("總支出", f"NT$ {analysis['total']:,.2f}")#顯示總輸出
            largest_column.metric(
                "最大筆支出",
                f"NT$ {largest['amount']:,.2f}",#顯示最大筆輸出
                help=f"{largest['date']:%Y-%m-%d}｜{largest['description']}｜{largest['category']}",
            )

            st.subheader("分類支出")
            category_expenses = analysis["by_category"].rename("支出金額")#取出各分類支出
            st.bar_chart(category_expenses)#長條圖
            st.dataframe(category_expenses.to_frame(), use_container_width=True)#數字表格

            st.subheader("消費明細")
            display_data = expense_data.copy()
            display_data["date"] = display_data["date"].dt.strftime("%Y-%m-%d")
            st.dataframe(display_data, use_container_width=True, hide_index=True)#顯示消費明細

            st.subheader("AI 消費問答")
            if "ai_question_count" not in st.session_state:
                st.session_state.ai_question_count = 0

            remaining_questions = 5 - st.session_state.ai_question_count
            st.caption(f"本次工作階段剩餘提問次數：{remaining_questions} / 5")
            question = st.text_input(
                "輸入中文問題",
                placeholder="例如：我的總支出是多少？哪個分類花最多？",
                max_chars=MAX_QUESTION_LENGTH,
                disabled=remaining_questions <= 0,
            )

            if st.button("詢問 AI", disabled=remaining_questions <= 0):
                api_key = os.getenv("GEMINI_API_KEY")
                if not api_key:
                    try:
                        api_key = st.secrets.get("GEMINI_API_KEY")
                    except Exception:
                        api_key = None

                try:
                    if not question.strip():
                        raise ValueError("請輸入問題。")
                    if not api_key:
                        raise MissingAPIKeyError(
                            "找不到 Gemini API Key，請設定 GEMINI_API_KEY 環境變數或 Streamlit secrets。"
                        )
                    st.session_state.ai_question_count += 1
                    with st.spinner("Gemini 分析中…"):
                        agent_result = ask_expense_agent(
                            question, expense_data, api_key
                        )
                except (ValueError, GeminiAgentError) as error:
                    st.warning(str(error))
                else:
                    st.markdown(agent_result.answer)
                    with st.expander("查看本次呼叫的工具"):
                        if agent_result.tool_names:
                            for tool_name in agent_result.tool_names:
                                st.code(tool_name)
                        else:
                            st.write("本次回答未呼叫分析工具。")

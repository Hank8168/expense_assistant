# 個人消費分析助手

使用 Streamlit 與 pandas 製作的本機消費分析工具。第一階段不串接 LLM，也不使用任何付費 API。

## 功能

- 上傳消費紀錄 CSV
- 計算總支出
- 彙整各分類支出並顯示圖表
- 顯示最大筆支出
- 提供可下載的範例 CSV

## 環境需求

- Python 3.10 以上

## 安裝與執行

建議先建立並啟用虛擬環境，再安裝套件：

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
streamlit run app.py
```

接著依終端機提示，用瀏覽器開啟 Streamlit 頁面。

## CSV 格式

CSV 必須使用 UTF-8 編碼並包含以下欄位：

| 欄位 | 說明 | 範例 |
| --- | --- | --- |
| `date` | 消費日期 | `2026-08-01` |
| `description` | 消費說明 | `早餐` |
| `category` | 消費分類 | `餐飲` |
| `amount` | 支出金額（數字） | `85` |

可使用專案內的 `sample_expenses.csv`，或從網頁介面下載範例。

## 執行測試

```powershell
python -m unittest discover -s tests -v
```

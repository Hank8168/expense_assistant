# 個人消費分析助手

使用 Streamlit、pandas 與 Google Gemini 製作的個人消費分析工具。AI 問答使用 Gemini API 免費額度，不需要付費 API。

## 功能

- 上傳消費紀錄 CSV
- 計算總支出
- 彙整各分類支出並顯示圖表
- 顯示最大筆支出
- 提供可下載的範例 CSV
- 使用 Gemini `gemini-3.5-flash-lite` 與 Function Calling 回答中文問題
- AI 的金額資料全部由本機 `expense_analyzer.py` 計算

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

## 設定 Gemini API Key

請先在 Google AI Studio 建立 Gemini API Key。程式只會從下列其中一處讀取 Key：

1. `GEMINI_API_KEY` 環境變數
2. `.streamlit/secrets.toml` 中的 `GEMINI_API_KEY`

PowerShell 環境變數範例（請自行填入 Key，不要提交到 Git）：

```powershell
$env:GEMINI_API_KEY = "你的 Gemini API Key"
streamlit run app.py
```

Streamlit secrets 格式：

```toml
GEMINI_API_KEY = "你的 Gemini API Key"
```

`.env` 與 `.streamlit/secrets.toml` 都已加入 `.gitignore`。每個 Streamlit 工作階段最多可向 AI 提問 5 次，每題最多 200 字。若沒有 Key、免費額度用完或網路異常，既有的統計數字與圖表仍可正常使用。

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

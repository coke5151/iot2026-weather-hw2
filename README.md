# 114-2 智慧物聯網 HW2
> 氣象局爬蟲與 AIoT 網站

這個專案會使用 CWA `F-A0010-001` API 抓取 7 日農業天氣資料，解析六大區域（北部、中部、南部、東北部、東部、東南部）最低/最高溫，輸出 `weather_data.csv`，並以 Streamlit + Folium 顯示互動式地圖與資料表。
另外也提供可直接部署到 Vercel 的前後端版本（靜態前端 `index.html` + Python Serverless API `/api/weather`）。

## 1) 安裝與環境
使用 `uv` 管理虛擬環境與依賴：

```powershell
uv add requests
uv add pandas
uv add streamlit
uv add folium
uv add python-dotenv
```

建立本地環境變數：

```powershell
Copy-Item .env.example .env
```

把 `.env` 裡的 `CWA_API_KEY` 改成你的 key。

## 2) 抓資料並輸出 CSV

```powershell
uv run python fetch_weather_data.py
```

成功後會產生：
- `weather_data.csv`

## 3) 啟動 Streamlit App

```powershell
uv run streamlit run app.py
```

功能包含：
- 重整後的儀表板版面（主畫面控制列、摘要卡片、地圖與明細分區）
- 日期下拉選單動態篩選
- Folium 圓形標記 + popup 區域明細
- 平均溫色階：藍 `<20°C`、綠 `20-25°C`、黃 `25-30°C`、紅 `>30°C`
- API Key 只從 `.env` 或 Streamlit Secrets 讀取，不會顯示在前端頁面
- 若遇 SSL 驗證問題會自動 fallback 到 `verify=False` 重試
- `F-A0010-001` 若 `rest/datastore` 回傳 404，程式會自動 fallback 到 `fileapi/v1/opendataapi`

## 4) 免費部署

### Streamlit Cloud（推薦）
- 入口檔：`app.py`
- 依賴：`requirements.txt`
- Secrets 設定：`CWA_API_KEY`
- 前端不提供 API Key 輸入欄位，更新資料時會直接使用伺服器端 Secrets

### Vercel（前後端）
- 前端：`index.html`（靜態頁，含地圖 + 日期篩選 + 表格）
- 後端：`api/weather.py`（Python Serverless）
- 路由設定：`vercel.json`
- API 路徑：`/api/weather`
- 在 Vercel Project > Settings > Environment Variables 設定：`CWA_API_KEY`

部署後，使用者不需要也不會看到 CWA Token，token 只存在伺服器端環境變數。

API 回傳 JSON 格式：
- `count`: 筆數
- `cache_ttl_seconds`: API 快取秒數（目前 1800 秒）
- `data`: 各區域每日溫度資料（含 `min_temp`, `max_temp`, `avg_temp`, `lat`, `lon`）


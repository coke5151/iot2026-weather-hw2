# 114-2 智慧物聯網 HW2
> 氣象局爬蟲與 AIoT 網站

這個專案會使用 CWA `F-A0010-001` API 抓取 7 日農業天氣資料，解析六大區域（北部、中部、南部、東北部、東部、東南部）最低/最高溫，輸出 `weather_data.csv`，並以 Streamlit + Folium 顯示互動式地圖與資料表。
另外也提供可直接部署到 Vercel 的前後端版本（靜態前端 `index.html` + Python API `/api/weather`）。
目前資料流已改成「後端排程更新共享快取，前端只讀取快取」，使用者不會直接觸發 CWA API。

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

部署時建議把這個指令交給排程工作執行，而不是交給前端按鈕觸發。

## 3) 啟動 Streamlit App

```powershell
uv run streamlit run app.py
```

功能包含：
- 重整後的儀表板版面（主畫面控制列、摘要卡片、地圖與明細分區）
- 日期下拉選單動態篩選
- Folium 圓形標記 + popup 區域明細
- 平均溫色階：藍 `<20°C`、綠 `20-25°C`、黃 `25-30°C`、紅 `>30°C`
- 前端只讀取共享快取 `weather_data.csv`，不提供手動刷新按鈕
- 若遇 SSL 驗證問題會自動 fallback 到 `verify=False` 重試
- `F-A0010-001` 若 `rest/datastore` 回傳 404，程式會自動 fallback 到 `fileapi/v1/opendataapi`

## 4) 免費部署

### 共用資料模型
- 後端排程執行：`python fetch_weather_data.py`
- 排程產物：`weather_data.csv`
- Streamlit 與 `/api/weather` 都只讀這份 CSV
- 所有使用者看到的是同一份共享資料，不會有人直接打到 CWA API

### GitHub Actions 自動更新（推薦）
- 已內建工作流：[`.github/workflows/refresh-weather-data.yml`](.github/workflows/refresh-weather-data.yml)
- 預設每 6 小時更新一次，也可手動執行 `workflow_dispatch`
- 需要在 GitHub repository secrets 設定：`CWA_API_KEY`
- 工作流更新 `weather_data.csv` 後會自動 commit，部署平台只要接 GitHub 就會跟著拿到新資料

### Streamlit Cloud（推薦）
- 入口檔：`app.py`
- 依賴：`requirements.txt`
- 前端不提供 API Key 輸入欄位，也不提供更新按鈕
- 建議搭配 GitHub Actions 排程更新 `weather_data.csv`

### Vercel（前後端）
- 前端：`index.html`（靜態頁，含地圖 + 日期篩選 + 表格）
- 後端：`api/weather.py`（只回傳共享 CSV，不直接呼叫 CWA）
- 路由設定：`vercel.json`
- API 路徑：`/api/weather`

部署後，使用者不需要也不會看到 CWA Token，也不能透過畫面觸發抓資料。

API 回傳 JSON 格式：
- `count`: 筆數
- `cache_ttl_seconds`: API 快取秒數（目前 1800 秒）
- `data`: 各區域每日溫度資料（含 `min_temp`, `max_temp`, `avg_temp`, `lat`, `lon`）


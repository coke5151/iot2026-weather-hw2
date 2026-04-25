# 04 Homework Requirement Fit Session

> 👤：
> `<environment_context>`
> `cwd: C:\Users\User\Documents\Repos\iot2026-weather-hw2`
> `shell: powershell`
> `current_date: 2026-04-24`
> `timezone: Asia/Taipei`
> `</environment_context>`

> 👤：
> HW2-4 實作氣溫預報 Web App (40%)
> 目的
> 製作一個氣溫預報 Web App 來視覺化氣溫資料。
>
> 方法
> 使用 Streamlit 建立 Web App
> 提供下拉選單，讓使用者選擇地區並查看該地區的氣溫預報
> 必須從 SQLite3 資料庫查詢資料
> 使用折線圖與表格來顯示一週的氣溫資料
> 評分比重
> 下拉選單功能（10%）
> 折線圖與表格（15%）
> 從 SQLite 資料庫查詢資料（10%）
> 程式碼結構與可讀性（5%）
>
> ---
>
> 請在 UI 介面跟爬資料邏輯不變的情況下，幫我把後端邏輯改成符合作業要求的，你提一下計劃

🤖：我先確認目前專案結構、Streamlit UI 與資料抓取/儲存方式，目標是在不動介面與爬資料流程的前提下，把後端改成符合「必須從 SQLite 查詢、一週折線圖與表格、地區下拉」的作業要求。

🤖：我已確認這是單一 `app.py` 的 Streamlit 專案，接著直接看 UI 與資料服務層，找出目前哪些地方還是走記憶體/CSV，而不是 SQLite 查詢。

🤖：目前看到資料層 `weather_service.py` 只會抓 CWA 後存成 `weather_data.csv`，`app.py` 也是直接 `load_weather_csv()`，所以核心落差很明確：作業要的是 SQLite 查詢，但現況是 CSV 快取。接下來我把互動流程和圖表顯示範圍補看完整，確認哪些介面行為必須原封不動保留。

🤖：我把主畫面流程看完了：現在前端只有「日期下拉」，沒有「地區下拉」，也沒有「單一地區一週折線圖」；它是用單日六區資料做地圖、排名與表格。這代表如果完全不改 UI，就無法百分之百對齊作業條目，這點我需要先跟你對齊。

🤖：目前現有畫面沒有地區下拉與一週折線圖。你要我規劃哪一種方案？

> 👤：
> 作業優先

🤖：需求已對齊成「作業優先」：可以補上作業需要的地區下拉與一週折線圖，但資料抓取來源與整體視覺風格盡量沿用。最後再補一個真相陳述：若只改後端不改前端，作業的 UI 評分項目本來就拿不滿，所以這個規劃會包含必要的前端調整，但不碰 CWA 抓取邏輯本身。

<proposed_plan>
# HW2-4 SQLite 化與作業版預報頁面調整計畫

## Summary
- 保留現有 CWA 抓取流程與資料清洗邏輯，不改 API 來源、區域對應、溫度整理規則。
- 後端從「只寫 CSV、前端只讀 CSV」改成「抓完資料後同步寫入 SQLite，前端改以 SQLite 查詢為主」，CSV 可保留做相容輸出。
- 依作業要求補上「地區下拉選單 + 單一地區一週折線圖 + 一週表格」，並盡量沿用現有 Streamlit 視覺風格，不重做整體設計。

## Key Changes
- 資料層
  - 在 `weather_service.py` 新增 SQLite 常數路徑與資料表初始化邏輯，使用標準庫 `sqlite3`，不新增第三方套件。
  - 建立單一預報表，欄位至少包含 `region`, `date`, `min_temp`, `max_temp`, `avg_temp`, `lat`, `lon`。
  - 以 `(region, date)` 作為唯一鍵或等效覆寫策略，避免排程重跑後重複資料。
  - 保留既有 `fetch_weather_dataframe()` 作為抓取與整理入口，避免碰爬蟲流程本身。
- 寫入流程
  - `save_weather_csv()` 保留，避免破壞現有 GitHub Actions 與本地流程。
  - 另外新增 `save_weather_sqlite()`，以及一個整合入口讓 `fetch_weather_data.py` 執行後同時更新 CSV 與 SQLite。
  - 若需要最小改動 CLI，維持 `python fetch_weather_data.py` 用法不變，只是副作用多寫一份 SQLite。
- 查詢層
  - 新增 SQLite 讀取函式，取代 `load_weather_csv()` 作為 app 的主要資料來源。
  - 提供至少三種查詢：
    - 取得所有可選地區清單
    - 取得指定地區的一週預報
    - 視需要保留取得全部資料的查詢，供舊版摘要/地圖邏輯或相容用途使用
  - 查詢結果統一回傳 `pandas.DataFrame`，讓現有 Streamlit 渲染邏輯只需小幅調整。
- Streamlit 頁面
  - 將目前控制元件從「日期下拉」改成以「地區下拉」為主，符合作業要求。
  - 主視覺區改為顯示單一地區的一週溫度折線圖，至少呈現最低溫、最高溫；平均溫可保留為第三條線或表格欄位。
  - 明細區改為顯示該地區一週資料表，欄位維持中文標示與數值格式化。
  - 既有地圖、排名、單日六區比較內容若與作業版衝突，優先簡化或移除；若版面允許，可降為次要資訊，但不能影響作業主流程的清楚度。
  - 警告訊息與說明文字同步從 `weather_data.csv` 改成 `weather_data.db` 或等效 SQLite 檔名。
- 文件與部署
  - README 更新為「前端查 SQLite、排程同步更新 SQLite/CSV」的實際架構。
  - GitHub Actions 仍跑同一支抓取腳本，不改排程；若工作流目前只 `git add weather_data.csv`，需一併納入 SQLite 檔案，否則部署端拿不到最新資料庫。

## Public Interfaces / Types
- `fetch_weather_data.py`
  - CLI 用法不變：`python fetch_weather_data.py`
  - 執行結果改為同時刷新 CSV 與 SQLite。
- `weather_service.py`
  - 新增 SQLite 寫入與查詢函式，例如：
    - 初始化資料庫
    - 寫入 DataFrame 到 SQLite
    - 查詢地區列表
    - 查詢單一地區一週預報
  - 現有抓取與 DataFrame 整理函式保留。
- `app.py`
  - 改為呼叫 SQLite 查詢函式，不再把 CSV 當主要資料來源。

## Test Plan
- 抓取流程
  - 執行 `python fetch_weather_data.py` 後，CSV 與 SQLite 都成功產生或更新。
  - 重複執行後，SQLite 不會累積重複 `(region, date)` 資料。
- 資料正確性
  - SQLite 內容筆數應與 CSV 對應資料一致。
  - 任一地區查出的 7 天資料，溫度值與 CSV/原始整理結果一致。
- UI 行為
  - 地區下拉可列出六大區域。
  - 切換地區後，折線圖與表格同步更新。
  - 表格顯示完整一週資料，日期排序正確。
- 作業驗收
  - 有地區下拉選單。
  - 有一週折線圖。
  - 有一週表格。
  - 資料確實來自 SQLite 查詢，而不是直接讀 CSV。

## Assumptions
- 「爬資料邏輯不變」解讀為不修改 CWA API 抓取、解析與區域整理規則，但允許在抓完後新增 SQLite 落地步驟。
- 「作業優先」已確認，因此允許對現有 UI 做必要調整，以滿足地區下拉與折線圖要求。
- SQLite 檔案會納入 repo/部署產物，讓 Streamlit 部署端可直接讀取。
- 既有 CSV 先保留，作為相容輸出與人工檢查用途，不再作為前端主資料來源。
</proposed_plan>

> 👤：
> PLEASE IMPLEMENT THIS PLAN:
> # HW2-4 SQLite 化與作業版預報頁面調整計畫
>
> ## Summary
> - 保留現有 CWA 抓取流程與資料清洗邏輯，不改 API 來源、區域對應、溫度整理規則。
> - 後端從「只寫 CSV、前端只讀 CSV」改成「抓完資料後同步寫入 SQLite，前端改以 SQLite 查詢為主」，CSV 可保留做相容輸出。
> - 依作業要求補上「地區下拉選單 + 單一地區一週折線圖 + 一週表格」，並盡量沿用現有 Streamlit 視覺風格，不重做整體設計。
>
> ## Key Changes
> - 資料層
>   - 在 `weather_service.py` 新增 SQLite 常數路徑與資料表初始化邏輯，使用標準庫 `sqlite3`，不新增第三方套件。
>   - 建立單一預報表，欄位至少包含 `region`, `date`, `min_temp`, `max_temp`, `avg_temp`, `lat`, `lon`。
>   - 以 `(region, date)` 作為唯一鍵或等效覆寫策略，避免排程重跑後重複資料。
>   - 保留既有 `fetch_weather_dataframe()` 作為抓取與整理入口，避免碰爬蟲流程本身。
> - 寫入流程
>   - `save_weather_csv()` 保留，避免破壞現有 GitHub Actions 與本地流程。
>   - 另外新增 `save_weather_sqlite()`，以及一個整合入口讓 `fetch_weather_data.py` 執行後同時更新 CSV 與 SQLite。
>   - 若需要最小改動 CLI，維持 `python fetch_weather_data.py` 用法不變，只是副作用多寫一份 SQLite。
> - 查詢層
>   - 新增 SQLite 讀取函式，取代 `load_weather_csv()` 作為 app 的主要資料來源。
>   - 提供至少三種查詢：
>     - 取得所有可選地區清單
>     - 取得指定地區的一週預報
>     - 視需要保留取得全部資料的查詢，供舊版摘要/地圖邏輯或相容用途使用
>   - 查詢結果統一回傳 `pandas.DataFrame`，讓現有 Streamlit 渲染邏輯只需小幅調整。
> - Streamlit 頁面
>   - 將目前控制元件從「日期下拉」改成以「地區下拉」為主，符合作業要求。
>   - 主視覺區改為顯示單一地區的一週溫度折線圖，至少呈現最低溫、最高溫；平均溫可保留為第三條線或表格欄位。
>   - 明細區改為顯示該地區一週資料表，欄位維持中文標示與數值格式化。
>   - 既有地圖、排名、單日六區比較內容若與作業版衝突，優先簡化或移除；若版面允許，可降為次要資訊，但不能影響作業主流程的清楚度。
>   - 警告訊息與說明文字同步從 `weather_data.csv` 改成 `weather_data.db` 或等效 SQLite 檔名。
> - 文件與部署
>   - README 更新為「前端查 SQLite、排程同步更新 SQLite/CSV」的實際架構。
>   - GitHub Actions 仍跑同一支抓取腳本，不改排程；若工作流目前只 `git add weather_data.csv`，需一併納入 SQLite 檔案，否則部署端拿不到最新資料庫。
>
> ## Public Interfaces / Types
> - `fetch_weather_data.py`
>   - CLI 用法不變：`python fetch_weather_data.py`
>   - 執行結果改為同時刷新 CSV 與 SQLite。
> - `weather_service.py`
>   - 新增 SQLite 寫入與查詢函式，例如：
>     - 初始化資料庫
>     - 寫入 DataFrame 到 SQLite
>     - 查詢地區列表
>     - 查詢單一地區一週預報
>   - 現有抓取與 DataFrame 整理函式保留。
> - `app.py`
>   - 改為呼叫 SQLite 查詢函式，不再把 CSV 當主要資料來源。
>
> ## Test Plan
> - 抓取流程
>   - 執行 `python fetch_weather_data.py` 後，CSV 與 SQLite 都成功產生或更新。
>   - 重複執行後，SQLite 不會累積重複 `(region, date)` 資料。
> - 資料正確性
>   - SQLite 內容筆數應與 CSV 對應資料一致。
>   - 任一地區查出的 7 天資料，溫度值與 CSV/原始整理結果一致。
> - UI 行為
>   - 地區下拉可列出六大區域。
>   - 切換地區後，折線圖與表格同步更新。
>   - 表格顯示完整一週資料，日期排序正確。
> - 作業驗收
>   - 有地區下拉選單。
>   - 有一週折線圖。
>   - 有一週表格。
>   - 資料確實來自 SQLite 查詢，而不是直接讀 CSV。
>
> ## Assumptions
> - 「爬資料邏輯不變」解讀為不修改 CWA API 抓取、解析與區域整理規則，但允許在抓完後新增 SQLite 落地步驟。
> - 「作業優先」已確認，因此允許對現有 UI 做必要調整，以滿足地區下拉與折線圖要求。
> - SQLite 檔案會納入 repo/部署產物，讓 Streamlit 部署端可直接讀取。
> - 既有 CSV 先保留，作為相容輸出與人工檢查用途，不再作為前端主資料來源。

🤖：我會直接照這份計畫落地：先改 `weather_service.py` 補 SQLite 寫入與查詢，再調整 `app.py` 成作業版的地區下拉＋一週折線圖，最後更新 README 與 workflow 並跑驗證。

🤖：資料層已改成可同步寫 SQLite，現在改 `app.py`，把主流程切成「地區下拉 → 一週折線圖 → 一週表格」，同時保留目前頁面的視覺語言。

🤖：前端主流程已換成作業版，接著把文件與排程補齊，避免 repo 只更新 CSV 卻漏掉 SQLite。

🤖：程式碼改完了，我先跑靜態驗證與一個本地資料庫建置流程，確認新函式與 Streamlit 入口至少能正常 import。

🤖：接著用現有 `weather_data.csv` 轉出 `weather_data.db`，這是為了讓 repo 內直接有可用的 SQLite 快取，同時驗證查詢函式的實際輸出。

🤖：SQLite 建檔已成功，我再補一個覆寫驗證，確認重跑後資料列數不會累積重複。

🤖：功能面已驗到 SQLite 查詢、單區七天資料與去重邏輯；我最後看一下工作樹與關鍵 diff，確認沒有漏掉部署需要的檔案。

🤖：已完成實作，核心變更在 `weather_service.py`、`app.py`、`README.md` 和 `.github/workflows/refresh-weather-data.yml`。

🤖：現在後端會把同一份 CWA 整理結果同步寫到 `weather_data.csv` 和新的 `weather_data.db`，前端改成只從 SQLite 查詢。Streamlit 主流程也已改成符合 HW2-4 的作業版：地區下拉選單、單一地區一週折線圖、以及一週明細表；原本的爬資料來源、區域對應與溫度整理規則沒有改。

🤖：驗證我已經做過：
- `.\.venv\Scripts\python.exe -m py_compile app.py weather_service.py fetch_weather_data.py`
- 用現有 `weather_data.csv` 建出 `weather_data.db`
- 驗證可查出 6 個地區、單一地區 7 天資料
- 重複寫入 SQLite 兩次後總筆數仍是 `42`，沒有重複累積

🤖：補充一點：我沒有直接對外跑 `fetch_weather_data.py` 抓 CWA 新資料，因為這會依賴當下的 API key / 網路；目前 repo 內的 `weather_data.db` 是根據現有 CSV 產生的，可直接拿來展示與交作業。

> 👤：
> 這會影響我的部署設置嗎？
> 一樣是 Github 設好 Secret、把現在的 Repo 丟上去、Streamlit Community Cloud 上面 Deploy？

🤖：不會改變你的部署方式，還是同一套流程：

🤖：
1. GitHub repo 一樣放上去。
2. GitHub Secrets 一樣設定 `CWA_API_KEY`。
3. Streamlit Community Cloud 一樣直接連這個 repo deploy。

🤖：有兩個實際差異要注意：
- 現在前端主要讀的是 `weather_data.db`，不是 `weather_data.csv`。所以第一次部署時，請把 `weather_data.db` 一起 push 上去，不然 app 會顯示「目前沒有可顯示資料」。
- GitHub Actions workflow 我已經改成會一起 `git add weather_data.csv weather_data.db`，之後排程更新時兩個檔案都會被更新並推回 repo。

🤖：其他部分基本不變：
- 不需要新增其他 Secret。
- 不需要額外安裝 SQLite 套件，Python 內建 `sqlite3` 就夠了。
- Streamlit Community Cloud 可以直接讀 repo 裡的 `.db` 檔。

🤖：所以你的部署 checklist 變成：
- push 程式碼
- 確認 repo 內有 `weather_data.db`
- GitHub Secret `CWA_API_KEY` 已設定
- Streamlit Community Cloud 指向同一個 repo、入口還是 `app.py`

🤖：如果你要，我可以再幫你順手檢查一次目前 repo 是否已經具備「可以直接 deploy」的狀態。

> 👤：
> 那請你根據作業要求，在 README 裡面列出應該檢查的項目、配分，並且打勾表示已完成

🤖：我會只補 README，把 HW2-4 對應的檢查項目與配分列成 checklist，並依目前實作狀態標成已完成。

🤖：我會把 checklist 直接加進 README，內容對齊你作業題目原本的四個評分項目，避免交作業時還要另外整理。

🤖：README 已補上作業檢查清單，在 `README.md` 的 `HW2-4 作業檢查清單` 段落，四個評分項目都已列出配分並標成已完成。

> 👤：
> 2-1~2-4 都要符合

🤖：我先把 repo 裡跟 HW2-1 到 HW2-4 對應的功能線索找出來，再把 README 的 checklist 擴成完整版本，不會憑空補需求名稱。

🤖：目前 README 只列了 HW2-4。我去讀最早的需求紀錄，確認 2-1 到 2-3 各自對應什麼功能，再一次補成完整 checklist。

🤖：我沒有在 repo 裡找到官方題目全文，但從現有功能結構可以對應出 2-1 到 2-4 的四塊實作。我先核對實際檔案，避免 README 寫了 repo 其實沒有的內容。

🤖：我先找 repo 裡有沒有把 2-1 到 2-3 的配分也記下來；如果沒有，我會把 README 改成「2-1~2-4 完整檢查清單」，但只對已知的配分精準標示，未知部分不亂編。

🤖：我會把 README 的單一 `HW2-4` 段落改成 `HW2 作業檢查清單（2-1 ~ 2-4）`。2-4 我用你已提供的正式配分；2-1 到 2-3 因為 repo 裡沒有原始配分，我會明確標成「請依課程公告核對」，避免亂填。

🤖：README 已改成完整的 `README.md` `HW2 作業檢查清單（2-1 ~ 2-4）`。

🤖：我這次的處理方式是：
- `HW2-4` 用你已提供的正式配分完整列出並打勾。
- `HW2-1 ~ 2-3` 因為 repo 裡沒有原始題目配分，我沒有亂編百分比，改成明確標示「請依課程公告核對」，但檢查項目都已按目前實作狀態打勾。

🤖：如果你把 `2-1 ~ 2-3` 的正式題目文字或配分貼給我，我可以再幫你把 README 補成完全對齊課堂版的最終格式。

> 👤：
> HW2-1 獲取天氣預報資料 (20%)
> 目的
> 使用 CWA API 獲取台灣北部、中部、南部、東北部、東部及東南部地區一週的天氣預報資料（必須是 JSON 格式）。
>
> 方法
> 使用 Requests 套件調用 CWA API，獲取天氣預報資料。
> 使用 json.dumps 觀察獲得的資料
> 評分比重
> 調用 CWA API 獲取天氣預報資料（10%）
> 觀察獲得的資料（5%）
> 程式碼結構與可讀性（5%）
> HW2-2 分析資料，提取最高與最低氣溫的資料 (20%)
> 目的
> 分析天氣預報資料的 JSON 格式，找出最高與最低氣溫的資料位置，並提取出來。
>
> 方法
> 使用 ChatGPT 或手動分析資料
> 使用 json.dumps 觀察提取的資料
> 評分比重
> 找出並提取最高與最低氣溫的資料（10%）
> 觀察提取的資料（5%）
> 程式碼結構與可讀性（5%）
> HW2-3 將氣溫資料儲存到 SQLite3 資料庫 (20%)
> 目的
> 將氣溫資料儲存到 SQLite3 資料庫，以便後續查詢。
>
> 方法
> 建立 SQLite3 資料庫，取名為 "data.db"
> 創建資料庫 Table，取名為 "TemperatureForecasts"
> 將氣溫資料存到資料庫，資料欄位必須包含：
> 主鍵（id）
> 地區名稱（regionName）
> 時間（dataDate）
> 最低氣溫（mint）
> 最高氣溫（maxt）
> 從資料庫查詢以下資料，來檢查資料是否正確被存入資料庫：
> 列出所有地區名稱
> 列出中部地區的氣溫資料
> 評分比重
> 將氣溫資料儲存到 SQLite3 資料庫（10%）
> 檢查資料是否正確被存入資料庫（5%）
> 程式碼結構與可讀性（5%）
> 資料庫欄位範例
>
> HW2-4 實作氣溫預報 Web App (40%)
> 目的
> 製作一個氣溫預報 Web App 來視覺化氣溫資料。
>
> 方法
> 使用 Streamlit 建立 Web App
> 提供下拉選單，讓使用者選擇地區並查看該地區的氣溫預報
> 必須從 SQLite3 資料庫查詢資料
> 使用折線圖與表格來顯示一週的氣溫資料
> 評分比重
> 下拉選單功能（10%）
> 折線圖與表格（15%）
> 從 SQLite 資料庫查詢資料（10%）
> 程式碼結構與可讀性（5%）
>
> 再給你一次，你再重新寫一次 README

🤖：我會把 README 的作業段落改成完全對齊你剛貼的 HW2-1 到 HW2-4 題目與配分，並依目前 repo 的實作狀態重新標示，不沿用剛剛那版的概括寫法。

🤖：我會把作業段落改成「精準對齊題目文字 + 配分」，並加一行註記說明勾選是依目前 repo 實作狀態，不直接代替老師評分。

🤖：README 已重寫成對齊你剛貼的 HW2-1 到 HW2-4 題目與配分版本，位置在 `README.md`。

🤖：我這次是照「目前 repo 的真實狀態」標示，所以有幾項我沒有硬打勾：
- `json.dumps` 觀察資料 / 提取資料
- `data.db`
- `TemperatureForecasts`
- `id / regionName / dataDate / mint / maxt` 這組欄位命名

🤖：因為你現在實作是：
- DB 檔名：`weather_data.db`
- Table：`weather_forecast`
- 欄位：`region`, `date`, `min_temp`, `max_temp`, `avg_temp`, `lat`, `lon`

🤖：如果你要，我下一步可以直接把程式也改成完全對齊老師指定的 `data.db`、`TemperatureForecasts` 和欄位名稱，順便補上 `json.dumps` 的觀察輸出，讓 README 能全部勾滿。

> 👤：
> 好，交給你

🤖：我會把程式也對齊老師指定格式：資料庫改成 `data.db`、資料表改成 `TemperatureForecasts`、補上 `id / regionName / dataDate / mint / maxt`，並加上 `json.dumps` 觀察原始與提取資料的入口，最後同步更新 Streamlit 與 README。

🤖：我會重寫資料層，但保留原本的 CWA 抓取與溫度解析邏輯；這次重點是把資料庫與觀察流程調整成作業指定格式，而不是另做一套新架構。

🤖：資料層已改成作業版 schema；現在把前端與 workflow 的檔名、說明文字和 README 一起切到 `data.db`，避免程式和文件不同步。

🤖：README 這次不只是改勾選，我會把執行指令也補成能直接對應 HW2-1 到 HW2-3 的觀察流程，讓文件和程式入口是一套的。

🤖：我現在做最後驗證：一是語法檢查，二是直接用現有 CSV 產生 `data.db` 並檢查 schema / 查詢結果，確認 README 裡打勾的項目真的都做到了。

🤖：Schema 驗證通過了：`data.db` 已建立、`TemperatureForecasts` 表和指定欄位都正確，查詢也能列出 6 個地區和中部地區 7 筆資料。我再確認一下工作樹，把新產生的 `data.db` 一起納入結果。

🤖：已經把作業要求對齊到程式本身，不只是 README。

🤖：現在的重點是：`weather_service.py` 改成預設寫入 `data.db`，資料表名稱是 `TemperatureForecasts`，欄位包含 `id / regionName / dataDate / mint / maxt`，另外保留 `avgTemp / lat / lon` 給 Web App 用；同時補了 `--show-json` 和 `--show-extracted`，可用 `json.dumps` 觀察原始 JSON 與提取結果。前端 `app.py` 已切到讀 `data.db`，workflow `.github/workflows/refresh-weather-data.yml` 也改成追蹤 `data.db`，README 重新對齊成你提供的 HW2-1 到 HW2-4 題目與配分。

🤖：我也已經產生新的 `data.db` 並驗證過：`TemperatureForecasts` schema 正確、欄位正確、共 42 筆、可列出 6 個地區、可查出中部地區 7 筆資料。語法檢查也已通過：`.\.venv\Scripts\python.exe -m py_compile app.py weather_service.py fetch_weather_data.py api\weather.py`。

🤖：補充一句：舊的 `weather_data.db` 我沒有刪，避免動到你既有檔案；目前程式已不再用它。

> 👤：
> `<environment_context>`
> `shell: powershell`
> `current_date: 2026-04-25`
> `timezone: Asia/Taipei`
> `</environment_context>`

> 👤：
> 請匯出我們這個 session 的所有對話記錄到 chats/04-homework-requirement-fit.md 裡面
> 對話中「> 👤：」代表是我下的 Prompt
> 「🤖：」代表是你的 Response
>
> 注意如果對話中有出現 API KEY 或重要個資的話請用 **** 碼掉

🤖：我先看一下 `chats/` 目錄現有檔案格式，然後把這個 session 的對話整理成指定的 `Markdown` 檔。

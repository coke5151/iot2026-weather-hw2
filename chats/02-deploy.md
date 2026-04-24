# 02 Deploy Session

> 👤：幫我重構一下，我覺得目前 Streamlit 不夠美觀，而且我發現 Streamlit 的頁面左側有設定 API KEY 的地方，這邊可以查看我的 API KEY，這不安全

🤖：先檢查目前的 Streamlit 結構、API key 設定方式，以及哪些元件把敏感資訊暴露在左側欄。我會先定位入口檔和相關設定，再直接調整介面與金鑰讀取流程。

🤖：`rg` 在這個環境啟動失敗，我改用 PowerShell 原生命令讀檔。接下來會直接看 `app.py`、`.streamlit` 設定和金鑰載入邏輯，確認問題點後重構版面。

🤖：問題已經很明確了：目前 `app.py` 會把環境中的 `CWA_API_KEY` 預填進 `st.text_input`，只是遮罩，不是隔離；任何能操作頁面的人都能看見或改出來。除了 UI 美觀，我也會把金鑰流程改成「不顯示、不回填、只在後端環境讀取」，並順手整理頁面資訊層級。

🤖：我準備直接改兩塊：

1. 安全性：移除所有「畫面上輸入/回填 API key」的邏輯，改成只從伺服器端環境變數或 Streamlit Secrets 讀取，而且畫面只顯示「已設定 / 未設定」。
2. 視覺層：把目前左側操作欄改成主畫面控制列，補上摘要指標、較乾淨的資訊分區和自訂樣式，避免看起來像預設模板。

🤖：現在開始改檔。`app.py` 會是主要重寫，另外我會同步調整 `.streamlit/config.toml`，把主題和基礎安全設定拉回比較合理的狀態。

🤖：版面主體已經改完，現在在做收尾檢查。我先跑語法驗證，順便抓一下是否有因為 Streamlit 元件包裝方式造成的問題，再做最後修正。

🤖：我把最後一個實作細節修一下：Streamlit 的 widget 不能真的被自訂 HTML `div` 包起來，否則外觀卡片有機會不如預期。這一段我會改成穩定的原生排法，保留樣式但避免 DOM 包裝失效。

🤖：語法沒問題；額外的 import 檢查失敗只是因為目前 shell 的系統 Python 沒裝專案依賴，不是這次改動本身出錯。我再用專案自己的 `uv` 環境補做一次驗證。

🤖：最後補一輪定位資訊，我要把實際改到的檔案和位置整理成可追的摘要，避免只說概念。

🤖：已完成重構，重點是把「UI 變乾淨」和「API key 不再暴露」一起處理。

**變更**
- 移除前端的 API key 輸入與預填，現在只從伺服器端 `.env` / Streamlit Secrets 讀取，畫面只顯示是否已設定，不會回填實際值。
- 把原本側欄操作改成主畫面的控制列，並重做整體版面：hero 區、摘要卡片、地圖、區域排名、明細表，視覺層次比原本清楚很多。
- Streamlit 設定改回較安全的預設方向，重新開啟 `CORS` / `XSRF` 保護，並補上主題色。
- README 也同步更新成新的使用方式與安全說明。

**驗證**
- `python -m py_compile app.py weather_service.py`
- `uv run python -c "import app; print('import-ok')"`

**安全提醒**
- 我在你的本機工作區看到 `.env` 已經有一把真實的 CWA key。因為舊版頁面曾經把 key 放到前端欄位，這把 key 建議直接輪替，再把新的值寫回本機或部署環境。

**你現在可以做的事**
1. 執行 `uv run streamlit run app.py` 看新版畫面。
2. 到 CWA 後台輪替目前那把 API key。

> 👤：我希望到時候部署，會是每過一段時間會被呼叫一次，使用者不能點按扭讓我去叫 API（不然我可能會被用到撞 limit）
> 大家看到的數據都是一起存在我後端的

🤖：我會把前端改成純讀取模式，完全移除使用者觸發 API 的路徑；同時檢查你現有的後端 / 排程入口，改成「由後端定時更新一次，所有人讀同一份快取資料」。

🤖：我先把現況拆清楚：你目前其實有兩條路，一條是 Streamlit 直接碰 CWA，另一條是 `Vercel + /api/weather`。如果要保證所有人看同一份資料、而且不能由使用者觸發 API，合理做法是把更新責任收斂到後端排程。接下來我會直接把程式改成這個模型。

🤖：我不打算只把按鈕拿掉而已，會順手把資料流改正：前端只讀 `weather_data.csv`，API 也只回傳這份快取；真正打 CWA 的行為留給排程腳本。這樣使用者路徑就不會再碰到第三方 API。

🤖：我會補一個排程工作流，讓更新動作留在後端流程而不是 UI。這樣部署後就算是靜態前端或唯讀 Streamlit，資料也會自動更新。

🤖：我已經把核心資料流改掉了，現在在驗證兩件事：`app.py` / `api/weather.py` 都不再走即時 CWA，以及排程工作流的內容沒有打壞現有專案。

🤖：實作已經到位。最後我只補一個檢查：確認新 workflow 有被納入版本控制，然後把你接下來部署時該用哪條路說清楚。

🤖：已改成「前端唯讀、後端排程更新共享快取」的模型。

**你要的行為**
- 使用者不能再按按鈕觸發 CWA API。
- Streamlit 和前端頁面都只讀同一份 `weather_data.csv`。
- 更新動作交給排程，不走使用者路徑。

**我改了什麼**
- Streamlit 移除手動更新流程，只保留日期切換與唯讀說明。
- `/api/weather` 不再打 CWA，只回傳共享 CSV 快取。
- 靜態前端 `index.html` 也移除了「重新載入」按鈕。
- 新增 GitHub Actions 排程，每 6 小時執行一次 `fetch_weather_data.py`，更新 `weather_data.csv` 後自動 commit。
- README 改成新的部署模型說明。

**驗證**
- `python -m py_compile app.py weather_service.py api\weather.py fetch_weather_data.py`

**部署上的實話**
- 這版現在是「共享快取檔案」模型，不是每個 viewer 即時打第三方 API。
- 如果你用 GitHub 連動部署，這樣很合適：排程更新 CSV，平台重新部署，所有人都看到同一份資料。
- 如果你以後要做「真正 runtime 後端儲存」而且不靠 redeploy，同時又放在 serverless 平台，那就該改成 KV / DB / object storage，不要靠檔案系統。

**我選 GitHub Actions 當排程的原因**
- Vercel 官方文件目前寫明 Hobby 方案的 Cron 只能 `每天一次`，不適合較頻繁更新；Pro 才支援更細頻率。
- Streamlit Community Cloud 官方文件有部署與設定說明，但我沒有找到內建排程機制；這是我選擇把排程放在 GitHub Actions 的原因，這點屬於基於官方文件內容的推論。

**你現在要做**
1. 到 GitHub repository secrets 新增 `CWA_API_KEY`
2. 啟用 workflow `Refresh Weather Data`
3. 部署平台改成讀 repo 最新內容，不要再讓前端碰 CWA

如果你要，我下一步可以直接幫你把 GitHub Actions 的排程頻率從每 6 小時改成你要的值。

> 👤：所以現在這個 Streamlit 帳號要怎麼部署？用 Github？

🤖：我先用官方文件確認 Streamlit Community Cloud 目前的部署入口，避免講成舊流程。接著我會直接告訴你這個專案該怎麼佈署、Secrets 放哪裡、以及 GitHub 在這個流程裡扮演什麼角色。

🤖：對，現在這個 Streamlit 最合理的部署方式就是「用 GitHub 當來源」。

**你現在的架構**
- Streamlit 只讀 `app.py` 和 `weather_data.csv`
- GitHub Actions 定時更新 `weather_data.csv`
- Streamlit Community Cloud 連你的 GitHub repo，自動部署最新版本

**你要怎麼做**
1. 把這個 repo 推到 GitHub
2. 到 `share.streamlit.io` 登入
3. 連接 GitHub 帳號
4. 按 `Create app`
5. 選你的 repo、branch、entrypoint file 填 `app.py`
6. Deploy

這是官方現在的部署流程，Community Cloud 直接從 GitHub repo 選 branch 和入口檔部署。

**Secrets 要放哪裡**
- `CWA_API_KEY` 不用放在 Streamlit Secrets
- 因為現在 Streamlit 前端不會直接打 CWA
- `CWA_API_KEY` 應該放在 GitHub repository secret，給 GitHub Actions 排程用

你現在需要的 secret 是：
- GitHub repo secrets: `CWA_API_KEY`

不需要的：
- Streamlit app secrets: `CWA_API_KEY`

**資料更新流程**
- GitHub Actions 跑 `refresh-weather-data.yml`
- 它會執行 `python fetch_weather_data.py`
- 更新 `weather_data.csv`
- commit 回 repo
- Streamlit 因為 repo 有更新，會跟著拿到新資料

**結論**
- 是，用 GitHub 部署 Streamlit
- Streamlit 負責顯示
- GitHub Actions 負責排程抓資料
- 使用者不會碰到你的 API key，也不能手動觸發 CWA

如果你要，我下一步可以直接幫你整理成一份「從 0 到部署完成」的實際操作清單。

> 👤：現在每隔多久會自動爬一次

🤖：現在是每 `6 小時` 一次。

設定在：
- `.github/workflows/refresh-weather-data.yml`

目前 cron 是：
```yaml
- cron: "0 */6 * * *"
```

這代表用 `UTC` 時區在：
- `00:00`
- `06:00`
- `12:00`
- `18:00`

各跑一次。

換成台灣時間 `Asia/Taipei` 是：
- `08:00`
- `14:00`
- `20:00`
- `02:00`

如果你要，我可以直接幫你改成：
1. 每天一次
2. 每 12 小時
3. 每 3 小時
4. 指定台灣時間每天某個固定時間

> 👤：每小時的話會太頻繁嗎？

🤖：不算太頻繁，技術上完全可行，但對你這個資料型態來說通常是「偏勤」。

原因：
- GitHub Actions 排程最短可到每 `5 分鐘`，所以每小時一次本身沒問題。
- 如果 repo 是 `public`，標準 GitHub-hosted runner 的 Actions 分鐘是免費的。
- 如果 repo 是 `private`，GitHub Free 每月有 `2,000` 分鐘；每小時一次大約是 `24 x 30 = 720` 次/月，而且 GitHub 會把每個 job 向上進位到整分鐘，所以光排程本身至少就吃掉約 `720` 分鐘/月，實際通常會更高。

就你的專案來看，我的建議是：
- `每 6 小時`：穩健，最合理
- `每 3 小時`：如果你想讓資料新一點，也還算合理
- `每 1 小時`：可以，但多半沒有必要，因為這是 7 日預報，不是即時觀測

還有一個實務點：
- 你現在的 workflow 會更新 `weather_data.csv` 並 `commit + push`
- 如果真的每小時都變動，就等於 repo 和 Streamlit 都可能每小時觸發一次更新
- 這不是不能做，只是噪音會比較多

結論：
- `技術上不會太頻繁`
- `產品上對這份資料多半沒必要`
- 我會建議維持 `6 小時`，最多改成 `3 小時`

如果你要，我可以直接幫你把排程改成 `3 小時` 或 `1 小時`。

> 👤：1s
> Current runner version: '2.333.1'
> Runner Image Provisioner
> Operating System
> Runner Image
> GITHUB_TOKEN Permissions
> Secret source: Actions
> Prepare workflow directory
> Prepare all required actions
> Getting action download info
> Download action repository 'actions/checkout@v4' (SHA:34e114876b0b11c390a56381ad16ebd13914f8d5)
> Download action repository 'actions/setup-python@v5' (SHA:a26af69be951a213d495a4c3e4e4022e16d87065)
> Complete job name: refresh
> 1s
> Run actions/checkout@v4
> Syncing repository: ****/iot2026-weather-hw2
> Getting Git version info
> Temporarily overriding HOME='/home/runner/work/_temp/****' before making global git config changes
> Adding repository directory to the temporary git global config as a safe directory
> /usr/bin/git config --global --add safe.directory /home/runner/work/iot2026-weather-hw2/iot2026-weather-hw2
> Deleting the contents of '/home/runner/work/iot2026-weather-hw2/iot2026-weather-hw2'
> Initializing the repository
> Disabling automatic garbage collection
> Setting up auth
> Fetching the repository
> Determining the checkout info
> /usr/bin/git sparse-checkout disable
> /usr/bin/git config --local --unset-all extensions.worktreeConfig
> Checking out the ref
> /usr/bin/git log -1 --format=%H
> ****
> 0s
> Run actions/setup-python@v5
> Installed versions
> 16s
> Run pip install -r requirements.txt
> ...（安裝依賴輸出略）
> 6s
> Run python fetch_weather_data.py
> Saved 42 rows to /home/runner/work/iot2026-weather-hw2/iot2026-weather-hw2/weather_data.csv
> region       date  min_temp  max_temp  avg_temp   lat    lon
>   北部地區 2026-04-24      20.0      24.0      22.0 25.05 121.53
>   中部地區 2026-04-24      22.0      28.0      25.0 24.15 120.67
>   南部地區 2026-04-24      24.0      31.0      27.5 22.63 120.30
>  東北部地區 2026-04-24      20.0      22.0      21.0 24.75 121.75
>   東部地區 2026-04-24      21.0      24.0      22.5 23.99 121.60
>  東南部地區 2026-04-24      23.0      27.0      25.0 22.76 121.15
>   北部地區 2026-04-25      19.0      24.0      21.5 25.05 121.53
>   中部地區 2026-04-25      21.0      27.0      24.0 24.15 120.67
>   南部地區 2026-04-25      23.0      29.0      26.0 22.63 120.30
>  東北部地區 2026-04-25      20.0      22.0      21.0 24.75 121.75
>   東部地區 2026-04-25      21.0      24.0      22.5 23.99 121.60
>  東南部地區 2026-04-25      22.0      27.0      24.5 22.76 121.15
> 0s
> Run git config user.name "github-actions[bot]"
> ...（commit / push 輸出略）
> Warning: Node.js 20 actions are deprecated. ...
>
> ---
>
> 跑完 workflow 我的倉庫沒有新增的 commit，我要怎麼確定是真的沒資料還是新資料跟舊資料一樣所以沒變化？

🤖：從這份 log 來看，這次不是「沒資料」，而是「抓到資料，但 CSV 內容和 repo 目前版本一樣，所以沒有 commit」。我直接把 workflow 補成會明確印出 `changed=true/false`，之後你每次看 log 就不需要猜。

🤖：我只改了 workflow 判斷邏輯，不動抓資料本身。現在會先把 `weather_data.csv` 暫存，明確印出「有沒有變」，只有真的變更才 commit。

🤖：這次的 log 代表「有抓到資料，而且寫出 `42` 筆」，不是沒資料。

判斷依據：
- `python fetch_weather_data.py` 已經成功跑完
- 它印了 `Saved 42 rows to .../weather_data.csv`
- 如果真的抓不到有效資料，照目前 `weather_service.py` 的邏輯，workflow 會直接失敗，不會安靜結束

所以這次沒有新增 commit，基本上就是：
- 新抓到的 `weather_data.csv`
- 和 repo 裡原本那份內容一樣
- 因此 `git diff --cached --quiet` 判定「沒變更」

我已經把 workflow 改成之後會明確顯示這件事：
- `.github/workflows/refresh-weather-data.yml`

新邏輯會先跑：
- `Check cache diff`

然後在 log 裡直接印：
- `No changes detected in weather_data.csv`
- 或
- `Detected updates in weather_data.csv`

而且只有真的有變更時才會進入 commit step。

你之後看 workflow，只要找這一步就知道：
- 有資料但沒變：`No changes detected...`
- 有資料而且變了：`Detected updates...`
- 沒資料或抓取失敗：workflow 會在 `python fetch_weather_data.py` 那步直接報錯

如果你要，我可以再幫你加一個更明確的輸出，例如每次都印：
1. 最新資料日期範圍
2. 總筆數
3. 前後檔案 hash 是否相同

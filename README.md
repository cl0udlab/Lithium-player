# Lithium Player

Lithium Player 是一個現代化的多媒體播放應用程式，支援音樂、影片和多種格式檔案的播放與管理。

## 部署方式

### Docker Compose 部署

```sh
git clone https://github.com/cl0udlab/Lithium-player
cd lithium-player
vim docker-compose.yml # 修改compose文件
```

```yml
backend:
    image: phillychi3/lithium-player-backend:latest
    container_name: lithium-backend
    volumes:
        - backend:/app/data
        - C:\Users\user\Music:/media # 前面換成自己的音樂目錄
    ports:
        - "8000:8000"
    environment:
        SQLIP: postgres
        APP_URL: 前端的網址(如果有的話
    networks:
        - lithium-network
    depends_on:
        - postgres
```

```sh
docker-compose up -d
```

## Subsonic / Navidrome 音樂來源

1. 登入後開啟側邊欄「Subsonic」。管理員輸入伺服器網址、使用者名稱與密碼，按「儲存並測試連線」。網址可包含子路徑，也可帶 `/rest`。
2. 按「同步曲目」匯入遠端音樂。曲目沿用網路音訊的播放佇列與播放清單格式；同步失敗不會清除既有曲目，重複同步不會新增重複曲目。
3. 按曲目旁的「快取」可預先下載，也會在首次播放前完整下載。大檔案首次播放需等待下載完成。帳號需有 Subsonic `download` 權限。
4. 遠端伺服器離線或按「中斷連結」後，曲目、播放清單及已下載的音訊仍保留。可使用「播放已快取歌曲」；未下載的曲目會顯示錯誤，可於恢復連線後重試。

使用 Subsonic API 1.16.1 JSON 與每次請求產生的 salt / MD5 token 驗證；詳見 [Subsonic 官方 API](https://www.subsonic.org/pages/api.jsp)。連線設定與快取保存在後端 `data/subsonic/`，既有 Docker `/app/data` 掛載會保存這些檔案。密碼只存於後端連線設定檔，設定查詢不會回傳密碼；正式部署請使用 HTTPS 並限制 data 目錄存取權限。

此快取支援 **Subsonic 來源斷線**，瀏覽器仍需連線至 Lithium 後端，不提供整個網站斷網後的離線啟動。換用其他伺服器或帳號時，舊曲目快取仍保留，未快取的舊曲目需重新連回原來源。同步採保留策略，不會自動刪除遠端已移除的曲目。

後端測試（安裝既有後端依賴後）：`cd backend`，執行 `python -m unittest discover -s tests`。
播放器斷線與競態測試：`cd frontend/web`，執行 `npm run test:player`。

## 開發環境

1. clone專案:

```sh
git clone https://github.com/cl0udlab/Lithium-player
cd lithium-player
```

2. 安裝依賴:

```sh
pnpm install

cd backend
poetry install
```

3. 啟動開發環境:

```sh
# 後端
cd backend
poetry run uvicorn src.main:app --reload
# 前端
pnpm dev:web
```

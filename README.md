# Lithium Player

Lithium Player 是一個現代化的多媒體播放應用程式，支援音樂、影片和多種格式檔案的播放與管理。

## 部署方式

### Docker Compose 部署

```sh
git clone https://github.com/your-username/lithium-player.git
cd lithium-player
docker-compose up -d
```

## 開發

1. clone專案:

```sh
git clone https://github.com/your-username/lithium-player.git
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

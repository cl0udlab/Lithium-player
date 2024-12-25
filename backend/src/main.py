from db import engine, SQLModel
from fastapi import FastAPI
import json
from pathlib import Path
from core.setting import Setting
from routers.authr import auth_router
from routers.file import file_router
from routers.stream import stream_router
from routers.user import user_router
from core.logger import logger
from starlette.middleware.cors import CORSMiddleware

SQLModel.metadata.create_all(engine)

data_path = Path("data")
data_path.mkdir(parents=True, exist_ok=True)

if not (data_path / "settings.json").exists():
    with open(data_path / "settings.json", "w") as f:
        json.dump(Setting().model_dump(), f, indent=4)


app = FastAPI()


@app.get("/ping")
def ping():
    return {"ping": "pong"}


app.include_router(auth_router)
app.include_router(file_router)
app.include_router(stream_router)
app.include_router(user_router)
logger.info("Server started")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173","http://localhost:4173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

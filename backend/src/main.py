from db import engine, SQLModel
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import json
from pathlib import Path
from core.setting import Setting

SQLModel.metadata.create_all(engine)

if not Path("data/settings.json").exists():
    with open("data/settings.json", "w") as f:
        json.dump(Setting().model_dump(), f)


app = FastAPI()


@app.get("/ping")
def ping():
    return {"ping": "pong"}


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

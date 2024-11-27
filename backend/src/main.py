from db import engine, SQLModel
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


SQLModel.metadata.create_all(engine)

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
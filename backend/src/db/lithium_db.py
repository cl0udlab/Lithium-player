from sqlmodel import SQLModel, create_engine, Session  # noqa: F401
import models  # noqa: F401 # for creating tables
from typing import Generator
import os

dbhost = os.getenv("SQLIP", "localhost")

postgres_url = f"postgresql://postgres:postgres@{dbhost}:5432/lithium"

engine = create_engine(postgres_url, echo=True)


def get_db() -> Generator[Session, None, None]:
    """獲取資料庫連線"""
    with Session(engine) as session:
        try:
            yield session
        finally:
            session.close()

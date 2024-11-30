from sqlmodel import SQLModel, create_engine, Session
import models  # noqa: F401 # for creating tables
from typing import Generator

postgres_url = "postgresql://postgres:postgres@localhost:5432/lithium"

engine = create_engine(postgres_url, echo=True)  # Debug mode enabled

def get_db() -> Generator[Session]:
    with Session(engine) as session:
        yield session
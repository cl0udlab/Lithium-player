from sqlmodel import SQLModel, create_engine
import models  # noqa: F401 # for creating tables

sqlite_url = "postgresql://postgres:postgres@localhost:5432/lithium"

connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, connect_args=connect_args,echo=True) # Debug

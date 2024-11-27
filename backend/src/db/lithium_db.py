from sqlalchemy import create_engine

sqlite_url = "postgresql://postgres:postgres@localhost:5432/lithium"

connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, connect_args=connect_args)

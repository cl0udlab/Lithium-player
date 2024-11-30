from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field, Column, JSON


class BaseModel(SQLModel):
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = Field(default=None)

class BasicFileModel(BaseModel):
    filename: str
    filepath: str

class ChangeLog(BaseModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    table_name: str
    record_id: int
    action: str
    changed_fields: dict =  Field(default_factory=dict, sa_column=Column(JSON))
    changed_by: int = Field(foreign_key="user.id")
    changed_at: datetime = Field(default_factory=datetime.now)
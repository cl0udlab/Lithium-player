from typing import Optional
from sqlmodel import Field
from enum import Enum

from .common import BasicFileModel


class FileFormat(str, Enum):
    PDF = "pdf"
    EPUB = "epub"
    MOBI = "mobi"
    TXT = "txt"


class FileModal(BasicFileModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    file_format: FileFormat
    size: int = Field(default=0)
    pages: Optional[int] = Field(default=None)
    author: Optional[str] = Field(default=None)
    publisher: Optional[str] = Field(default=None)

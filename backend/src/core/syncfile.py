from pathlib import Path
import os
from db import get_db
from core.fileparser import FileParser
from sqlmodel import Session, select, union
from models import VideoFile, MusicTrackFile


def scan_dir_file(dir_path: Path) -> list:
    db: Session = get_db()
    if not dir_path.is_dir():
        raise ValueError("Invalid directory path")
    query = union(select(VideoFile.filepath), select(MusicTrackFile.filepath))
    exist_files = db.exec(query).all()
    files = []
    for root, _, files in os.walk(dir_path):
        for file in files:
            file_path = Path(root) / file
            # TODO: Error log
            if file_path in exist_files:
                continue
            try:
                files.append(FileParser().parse_file(file_path))
            except Exception:
                pass
    return files


def scan_one_file(file_path: Path):
    db: Session = get_db()
    if not file_path.is_file():
        raise ValueError("Invalid file path")
    query = union(select(VideoFile.filepath), select(MusicTrackFile.filepath))
    exist_files = db.exec(query).all()
    if file_path in exist_files:
        raise ValueError("File already exists")
    try:
        file = FileParser().parse_file(file_path)
    except Exception:
        return
    return file

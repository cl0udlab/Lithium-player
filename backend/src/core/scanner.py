import threading
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional
from core.logger import logger
from core.syncfile import remove_missing_music, sync_dir_file


@dataclass
class ScanStatus:
    running: bool = False
    paths: list[str] = field(default_factory=list)

    processed: int = 0
    total: int = 0
    current_file: Optional[str] = None
    added: int = 0

    removed: int = 0
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None


class LibraryScanner:
    def __init__(self):
        self._lock = threading.Lock()
        self._status = ScanStatus()

    def status(self) -> dict:
        with self._lock:
            return asdict(self._status)

    def start(self, paths: list[Path]) -> bool:
        with self._lock:
            if self._status.running:
                return False
            self._status = ScanStatus(
                running=True,
                paths=[str(p) for p in paths],
                started_at=datetime.now(),
            )
        threading.Thread(
            target=self._run, args=(paths,), name="library-scan", daemon=True
        ).start()
        return True

    def _on_progress(self, processed: int, total: int, file_path: Path):
        with self._lock:
            self._status.processed = processed
            self._status.total = total
            self._status.current_file = str(file_path)

    def _run(self, paths: list[Path]):
        added, removed, error = 0, 0, None
        for path in paths:
            try:
                removed += remove_missing_music(path)
                with self._lock:
                    self._status.removed = removed
                added += len(sync_dir_file(path, self._on_progress))
            except Exception as e:
                logger.error(f"掃描 {path} 失敗: {str(e)}")
                error = f"{path}: {str(e)}"
            with self._lock:
                self._status.added = added
        with self._lock:
            self._status.running = False
            self._status.current_file = None
            self._status.error = error
            self._status.finished_at = datetime.now()
        logger.info(f"媒體庫掃描完成, 新增 {added} 個檔案, 移除 {removed} 首遺失的音樂")


scanner = LibraryScanner()

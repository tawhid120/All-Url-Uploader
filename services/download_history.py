from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class DownloadHistoryItem:
    """Represents a single download in user history"""
    file_name: str
    file_size: int
    file_ext: str
    source_url: str
    download_date: str  # ISO format
    send_type: str  # 'video', 'audio', 'document'
    title: str | None = None


class DownloadHistoryManager:
    """Manages per-user download history"""
    
    def __init__(self, history_dir: Path) -> None:
        self.history_dir = history_dir.resolve()
        self.history_dir.mkdir(parents=True, exist_ok=True)
    
    def _history_path(self, user_id: int) -> Path:
        return self.history_dir / f"user_{user_id}_history.json"
    
    def get_user_history(self, user_id: int) -> list[DownloadHistoryItem]:
        """Get all download history for a user"""
        path = self._history_path(user_id)
        if not path.exists():
            return []
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return [DownloadHistoryItem(**item) for item in data]
        except Exception as exc:
            logger.warning("Failed to load history for user %s: %s", user_id, exc)
            return []
    
    def add_to_history(
        self, 
        user_id: int, 
        file_name: str, 
        file_size: int,
        file_ext: str,
        source_url: str,
        send_type: str,
        title: str | None = None
    ) -> None:
        """Add a new download to user history"""
        history = self.get_user_history(user_id)
        
        item = DownloadHistoryItem(
            file_name=file_name,
            file_size=file_size,
            file_ext=file_ext,
            source_url=source_url,
            download_date=datetime.now().isoformat(),
            send_type=send_type,
            title=title,
        )
        
        history.append(item)
        
        # Keep only last 50 downloads to save space
        if len(history) > 50:
            history = history[-50:]
        
        path = self._history_path(user_id)
        path.write_text(
            json.dumps([asdict(item) for item in history]),
            encoding="utf-8",
        )
        logger.info("Added to history | user=%s file=%s", user_id, file_name)
    
    def get_last_download(self, user_id: int) -> DownloadHistoryItem | None:
        """Get the most recent download"""
        history = self.get_user_history(user_id)
        return history[-1] if history else None
    
    def cleanup(self, user_id: int) -> int:
        """Delete all downloads except the last 2"""
        history = self.get_user_history(user_id)
        if len(history) <= 2:
            return 0
        
        removed = len(history) - 2
        history = history[-2:]
        
        path = self._history_path(user_id)
        path.write_text(
            json.dumps([asdict(item) for item in history]),
            encoding="utf-8",
        )
        logger.info("Cleanup completed | user=%s removed=%s", user_id, removed)
        return removed

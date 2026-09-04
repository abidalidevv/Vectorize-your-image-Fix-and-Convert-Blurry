"""
VectorForge AI — Session Manager
Manages per-upload sessions with temp file lifecycle.
"""
import uuid
import time
import shutil
import logging
from pathlib import Path
from threading import Lock
from typing import Optional

from core.config import settings

logger = logging.getLogger(__name__)


class Session:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.created_at = time.time()
        self.last_accessed = time.time()
        self.session_dir = settings.temp_dir / session_id
        self.session_dir.mkdir(parents=True, exist_ok=True)

        # File paths (set as processing progresses)
        self.original_path: Optional[Path] = None
        self.preprocessed_path: Optional[Path] = None
        self.quantized_path: Optional[Path] = None
        self.svg_path: Optional[Path] = None

        # Metadata
        self.original_filename: str = ""
        self.image_width: int = 0
        self.image_height: int = 0
        self.image_format: str = ""
        self.has_alpha: bool = False

        # Pipeline state
        self.last_pipeline_params: dict = {}

    def touch(self):
        self.last_accessed = time.time()

    def is_expired(self) -> bool:
        return time.time() - self.last_accessed > settings.session_ttl_seconds

    def get_path(self, name: str, suffix: str = "") -> Path:
        """Get a path within this session directory."""
        return self.session_dir / f"{name}{suffix}"

    def cleanup(self):
        """Remove all temp files for this session."""
        if self.session_dir.exists():
            shutil.rmtree(self.session_dir, ignore_errors=True)
            logger.info(f"Cleaned up session {self.session_id}")


class SessionManager:
    def __init__(self):
        self._sessions: dict[str, Session] = {}
        self._lock = Lock()

    def create_session(self) -> Session:
        session_id = str(uuid.uuid4())
        session = Session(session_id)
        with self._lock:
            self._sessions[session_id] = session
        logger.info(f"Created session {session_id}")
        return session

    def get_session(self, session_id: str) -> Optional[Session]:
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                return None
            if session.is_expired():
                session.cleanup()
                del self._sessions[session_id]
                return None
            session.touch()
            return session

    def get_or_error(self, session_id: str) -> Session:
        session = self.get_session(session_id)
        if session is None:
            raise ValueError(f"Session '{session_id}' not found or expired")
        return session

    def delete_session(self, session_id: str):
        with self._lock:
            session = self._sessions.pop(session_id, None)
        if session:
            session.cleanup()

    def cleanup_expired(self):
        with self._lock:
            expired = [sid for sid, s in self._sessions.items() if s.is_expired()]
            for sid in expired:
                self._sessions[sid].cleanup()
                del self._sessions[sid]
        if expired:
            logger.info(f"Cleaned up {len(expired)} expired sessions")

    def cleanup_all(self):
        with self._lock:
            for session in self._sessions.values():
                session.cleanup()
            self._sessions.clear()


session_manager = SessionManager()

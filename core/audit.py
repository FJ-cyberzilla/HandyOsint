"""
Audit logging for HandyOsint.
"""

import logging
import json
import sqlite3
from typing import List, Dict, Any

from core.models import AuditLogEntry

logger = logging.getLogger(__name__)


class AuditLogger:
    """Enterprise audit logging."""

    def __init__(self, db_path: str = "audit.db") -> None:
        """Initialize audit logger."""
        self.db_path = db_path
        self._init_db()
        logger.info("Audit logger initialized with DB: %s", db_path)

    def _init_db(self) -> None:
        """Initialize SQLite database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                action TEXT NOT NULL,
                username TEXT NOT NULL,
                scan_id TEXT NOT NULL,
                details TEXT,
                status TEXT NOT NULL,
                error_message TEXT
            )
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_scan_id ON audit_logs(scan_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_username ON audit_logs(username)
        """)

        conn.commit()
        conn.close()

    def log(self, entry: AuditLogEntry) -> None:
        """Log audit entry."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO audit_logs
                (timestamp, action, username, scan_id, details, status, error_message)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                entry.timestamp,
                entry.action,
                entry.username,
                entry.scan_id,
                json.dumps(entry.details),
                entry.status,
                entry.error_message,
            ))

            conn.commit()
            conn.close()
        except sqlite3.Error as e:
            logger.error("Audit logging failed: %s", e)

    def get_scan_history(self, username: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get scan history for username."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT timestamp, action, scan_id, status
                FROM audit_logs
                WHERE username = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (username, limit))

            results = cursor.fetchall()
            conn.close()

            return [
                {
                    "timestamp": r[0],
                    "action": r[1],
                    "scan_id": r[2],
                    "status": r[3],
                }
                for r in results
            ]
        except sqlite3.Error as e:
            logger.error("Failed to retrieve scan history: %s", e)
            return []

"""
Async job persistence layer for HandyOsint using SQLite.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiosqlite

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = _PROJECT_ROOT / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "jobs.db"


@dataclass
class JobRecord:
    """In-memory representation of a persisted job."""

    job_id: str
    username: str
    status: str
    created_at: datetime
    updated_at: datetime
    raw_payload: Optional[str]


class JobRepository:
    """Async repository for job persistence backed by SQLite."""

    def __init__(self) -> None:
        self._db_path = DB_PATH
        self._conn: Optional[aiosqlite.Connection] = None

    async def connect(self) -> None:
        """Open a connection and ensure schema exists."""
        self._conn = await aiosqlite.connect(self._db_path.as_posix())
        await self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS jobs (
                job_id TEXT PRIMARY KEY,
                username TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                raw_payload TEXT
            )
            """
        )
        await self._conn.commit()

    async def disconnect(self) -> None:
        """Close the connection if open."""
        if self._conn:
            await self._conn.close()
            self._conn = None

    async def save_job(
        self,
        job_id: str,
        username: str,
        status: str,
        raw_payload: Optional[str],
    ) -> None:
        """Persist a new job record."""
        if not self._conn:
            raise RuntimeError("JobRepository not connected")

        now = datetime.now(timezone.utc).isoformat()
        await self._conn.execute(
            """
            INSERT OR REPLACE INTO jobs (
                job_id, username, status, created_at, updated_at, raw_payload
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (job_id, username, status, now, now, raw_payload),
        )
        await self._conn.commit()

    async def update_job_status(self, job_id: str, status: str) -> None:
        """Update the status field of an existing job."""
        if not self._conn:
            raise RuntimeError("JobRepository not connected")

        now = datetime.now(timezone.utc).isoformat()
        await self._conn.execute(
            """
            UPDATE jobs
            SET status = ?, updated_at = ?
            WHERE job_id = ?
            """,
            (status, now, job_id),
        )
        await self._conn.commit()

    async def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a job by ID as a plain dict."""
        if not self._conn:
            raise RuntimeError("JobRepository not connected")

        cursor = await self._conn.execute(
            """
            SELECT job_id, username, status, created_at, updated_at, raw_payload
            FROM jobs
            WHERE job_id = ?
            """,
            (job_id,),
        )
        row = await cursor.fetchone()
        await cursor.close()

        if row is None:
            return None

        return {
            "job_id": row[0],
            "username": row[1],
            "status": row[2],
            "created_at": row[3],
            "updated_at": row[4],
            "raw_payload": row[5],
        }

    async def save_platform_result(self, job_id: str, result: Dict[str, Any]) -> None:
        """Persist a single platform result for a job."""
        if not self._conn:
            raise RuntimeError("JobRepository not connected")

        await self._conn.execute(
            """
            INSERT INTO results (
                job_id, platform, exists, profile_url, confidence,
                response_time_ms, metadata, error
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                job_id,
                result["platform"],
                1 if result["exists"] else 0,
                result["profile_url"],
                result["confidence"],
                result["response_time_ms"],
                json.dumps(result["metadata"]),
                result["error"],
            ),
        )
        await self._conn.commit()

    async def get_results_for_job(self, job_id: str) -> List[Dict[str, Any]]:
        """Retrieve all platform results for a given job."""
        if not self._conn:
            raise RuntimeError("JobRepository not connected")

        cursor = await self._conn.execute(
            """
            SELECT platform, exists, profile_url, confidence,
                   response_time_ms, metadata, error
            FROM results
            WHERE job_id = ?
            """,
            (job_id,),
        )
        rows = await cursor.fetchall()
        await cursor.close()

        results: List[Dict[str, Any]] = []
        for row in rows:
            results.append(
                {
                    "platform": row[0],
                    "exists": bool(row[1]),
                    "profile_url": row[2],
                    "confidence": row[3],
                    "response_time_ms": row[4],
                    "metadata": json.loads(row[5]) if row[5] else {},
                    "error": row[6],
                }
            )
        return results

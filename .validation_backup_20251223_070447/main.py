#!/usr/bin/env python3
"""
HANDYOSINT - Enterprise Production Command Center v4.0
Complete OSINT Intelligence Platform with Professional Integration.

This module provides:
- Integrated UI system (banner, menu, terminal)
- Database management with async support
- Command center with comprehensive handlers
- Error handling and logging
- Signal management for graceful shutdown
- Scan result correlation and analytics
"""

import asyncio
import sys
import json
import signal
import sqlite3
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable

# ========================================================================
# PATH CONFIGURATION
# ========================================================================

BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR / "ui"))
sys.path.insert(0, str(BASE_DIR / "core"))
sys.path.insert(0, str(BASE_DIR / "config"))

# ========================================================================
# IMPORTS
# ========================================================================

try:
    from ui.banner import Banner, BannerColorScheme
    from ui.menu import Menu, MenuColorScheme
    from ui.terminal import Terminal, TerminalColorScheme
except ImportError as exc:
    print(f"\033[91m[FATAL ERROR] Failed to import UI modules: {exc}\033[0m")
    sys.exit(1)

# ========================================================================
# LOGGING SETUP
# ========================================================================

LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(
            LOG_DIR / f"handyosint_{datetime.now().strftime('%Y%m%d')}.log"
        ),
        logging.StreamHandler(),
    ],
)

logger = logging.getLogger("HandyOsint")


class SaveResultBuilder:
    """Builder for save_result parameters to reduce argument count."""

    def __init__(self, target: str, platform: str, status: str) -> None:
        """Initialize builder with required parameters."""
        self.target = target
        self.platform = platform
        self.status = status
        self.url = ""
        self.scan_type = ""
        self.details: Optional[Dict] = None

    def with_url(self, url: str) -> 'SaveResultBuilder':
        """Set URL."""
        self.url = url
        return self

    def with_scan_type(self, scan_type: str) -> 'SaveResultBuilder':
        """Set scan type."""
        self.scan_type = scan_type
        return self

    def with_details(self, details: Dict) -> 'SaveResultBuilder':
        """Set details."""
        self.details = details
        return self

    async def save(self, db: 'DatabaseManager') -> bool:
        """Save using database manager."""
        return await db.save_result(
            target=self.target,
            platform=self.platform,
            status=self.status,
            url=self.url,
            scan_type=self.scan_type,
            details=self.details
        )


# ========================================================================
# DATABASE MANAGER
# ========================================================================

class DatabaseManager:
    """SQLite database operations with async support."""

    def __init__(self, db_path: Optional[Path] = None) -> None:
        """Initialize database manager."""
        self.db_path = db_path or BASE_DIR / "data" / "handyosint.db"
        self.db_path.parent.mkdir(exist_ok=True)
        self._init_database_sync()

    def _init_database_sync(self) -> None:
        """Initialize database schema synchronously."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Scan results table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS scan_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    target TEXT NOT NULL,
                    platform TEXT NOT NULL,
                    status TEXT NOT NULL,
                    url TEXT,
                    details TEXT,
                    scan_type TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

            # Batch jobs table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS batch_jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    targets TEXT NOT NULL,
                    status TEXT DEFAULT 'pending',
                    total_scans INTEGER,
                    completed_scans INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP
                )
                """
            )

            # Create indexes
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_target ON scan_results(target)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_timestamp ON scan_results(timestamp)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_platform ON scan_results(platform)"
            )

            conn.commit()
            conn.close()
            logger.info("Database initialized: %s", self.db_path)

        except (sqlite3.Error, OSError) as exc:
            logger.error("Database initialization failed: %s", exc)
            raise

    async def _execute_db_operation(self, func: Callable,
                                   *args: Any, **kwargs: Any) -> Any:
        """Execute blocking DB operation in thread pool."""
        return await asyncio.to_thread(func, *args, **kwargs)

    async def save_result(
        self,
        target: str,
        platform: str,
        status: str,
        url: str = "",
        scan_type: str = "",
        details: Optional[Dict] = None
    ) -> bool:
        """Save scan result asynchronously."""

        def _save() -> bool:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO scan_results
                (timestamp, target, platform, status, url, details, scan_type)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    datetime.now().isoformat(),
                    target,
                    platform,
                    status,
                    url,
                    json.dumps(details or {}),
                    scan_type,
                ),
            )

            conn.commit()
            conn.close()
            return True

        try:
            success = await self._execute_db_operation(_save)
            logger.info("Saved result: %s on %s", target, platform)
            return success
        except (sqlite3.Error, OSError) as exc:
            logger.error("Failed to save result: %s", exc)
            return False

    async def get_scan_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieve scan history asynchronously."""

        def _get_history() -> List[Dict[str, Any]]:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT id, timestamp, target, platform, status, url, scan_type
                FROM scan_results
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (limit,),
            )

            results = []
            for row in cursor.fetchall():
                results.append({
                    "id": row[0],
                    "timestamp": row[1],
                    "target": row[2],
                    "platform": row[3],
                    "status": row[4],
                    "url": row[5],
                    "scan_type": row[6],
                })

            conn.close()
            return results

        try:
            return await self._execute_db_operation(_get_history)
        except (sqlite3.Error, OSError) as exc:
            logger.error("Failed to retrieve history: %s", exc)
            return []

    async def search_results(self, target: str) -> List[Dict[str, Any]]:
        """Search results by target asynchronously."""

        def _search() -> List[Dict[str, Any]]:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT id, timestamp, target, platform, status, url, scan_type
                FROM scan_results
                WHERE target LIKE ? OR url LIKE ?
                ORDER BY created_at DESC
                """,
                (f"%{target}%", f"%{target}%"),
            )

            results = []
            for row in cursor.fetchall():
                results.append({
                    "id": row[0],
                    "timestamp": row[1],
                    "target": row[2],
                    "platform": row[3],
                    "status": row[4],
                    "url": row[5],
                    "scan_type": row[6],
                })

            conn.close()
            return results

        try:
            return await self._execute_db_operation(_search)
        except (sqlite3.Error, OSError) as exc:
            logger.error("Search failed: %s", exc)
            return []

    async def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics asynchronously."""

        def _get_stats() -> Dict[str, Any]:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM scan_results")
            total_scans = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM scan_results WHERE status = 'FOUND'")
            found_profiles = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(DISTINCT target) FROM scan_results")
            unique_targets = cursor.fetchone()[0]

            cursor.execute(
                """
                SELECT platform, COUNT(*) as count
                FROM scan_results
                GROUP BY platform
                """
            )
            platforms = dict(cursor.fetchall())

            conn.close()

            return {
                "total_scans": total_scans,
                "found_profiles": found_profiles,
                "unique_targets": unique_targets,
                "platforms": platforms,
            }

        try:
            return await self._execute_db_operation(_get_stats)
        except (sqlite3.Error, OSError) as exc:
            logger.error("Statistics retrieval failed: %s", exc)
            return {}

    async def get_correlated_target_profiles(
        self,
        target: str
    ) -> Dict[str, Any]:
        """Retrieve and correlate all scan results for target across platforms."""

        def _get_profiles() -> Dict[str, Any]:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT platform, status, url, timestamp, created_at, details
                FROM scan_results
                WHERE target = ?
                ORDER BY created_at DESC
                """,
                (target,),
            )
            raw_results = cursor.fetchall()

            correlated_data: Dict[str, Any] = {
                "target": target,
                "profiles_by_platform": {},
                "status_counts": {},
                "history_summary": []
            }

            for row in raw_results:
                platform = row["platform"]
                status = row["status"]

                if platform not in correlated_data["profiles_by_platform"]:
                    correlated_data["profiles_by_platform"][platform] = []

                correlated_data["profiles_by_platform"][platform].append({
                    "status": status,
                    "url": row["url"],
                    "timestamp": row["timestamp"],
                    "created_at": row["created_at"],
                    "details": (json.loads(row["details"])
                               if row["details"] else None)
                })

                status_key = status.lower()
                correlated_data["status_counts"][status_key] = (
                    correlated_data["status_counts"].get(status_key, 0) + 1
                )
                correlated_data["history_summary"].append(
                    f"{platform}: {status} on {row['created_at']}"
                )

            conn.close()
            return correlated_data

        try:
            return await self._execute_db_operation(_get_profiles)
        except (sqlite3.Error, OSError) as exc:
            logger.error("Correlation query failed for target %s: %s", target, exc)
            return {
                "target": target,
                "profiles_by_platform": {},
                "status_counts": {},
                "history_summary": [],
                "error": str(exc)
            }

    async def get_overall_correlation_summary(
        self,
        limit_targets: int = 10
    ) -> Dict[str, Any]:
        """Provide overall correlation summary across all scanned targets."""

        def _get_summary() -> Dict[str, Any]:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            summary_data: Dict[str, Any] = {
                "total_scans_recorded": 0,
                "unique_targets_scanned": 0,
                "top_targets_by_profiles_found": [],
                "platforms_activity": {},
                "status_distribution": {},
                "recent_activity_overview": []
            }

            cursor.execute("SELECT COUNT(*) FROM scan_results")
            summary_data["total_scans_recorded"] = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(DISTINCT target) FROM scan_results")
            summary_data["unique_targets_scanned"] = cursor.fetchone()[0]

            cursor.execute(
                """
                SELECT target, COUNT(DISTINCT platform) as profiles_found_count
                FROM scan_results
                WHERE status = 'found'
                GROUP BY target
                ORDER BY profiles_found_count DESC, target ASC
                LIMIT ?
                """,
                (limit_targets,)
            )
            summary_data["top_targets_by_profiles_found"] = (
                [dict(row) for row in cursor.fetchall()]
            )

            cursor.execute(
                """
                SELECT platform, status, COUNT(*) as count
                FROM scan_results
                GROUP BY platform, status
                ORDER BY platform, status
                """
            )
            platform_stats_raw = cursor.fetchall()

            for row in platform_stats_raw:
                platform = row["platform"]
                status = row["status"].lower()
                count = row["count"]

                if platform not in summary_data["platforms_activity"]:
                    summary_data["platforms_activity"][platform] = {
                        "total": 0,
                        "found": 0,
                        "not_found": 0,
                        "blocked": 0,
                        "error": 0,
                        "rate_limited": 0
                    }

                summary_data["platforms_activity"][platform]["total"] += count
                summary_data["platforms_activity"][platform][status] = (
                    summary_data["platforms_activity"][platform].get(status, 0)
                    + count
                )

            cursor.execute(
                """
                SELECT status, COUNT(*) as count
                FROM scan_results
                GROUP BY status
                ORDER BY count DESC
                """
            )
            summary_data["status_distribution"] = (
                {row["status"]: row["count"] for row in cursor.fetchall()}
            )

            cursor.execute(
                """
                SELECT target, platform, status, created_at
                FROM scan_results
                ORDER BY created_at DESC
                LIMIT 5
                """
            )
            summary_data["recent_activity_overview"] = (
                [dict(row) for row in cursor.fetchall()]
            )

            conn.close()
            return summary_data

        try:
            return await self._execute_db_operation(_get_summary)
        except (sqlite3.Error, OSError) as exc:
            logger.error("Overall correlation summary query failed: %s", exc)
            return {"error": str(exc)}


# ========================================================================
# COMMAND CENTER
# ========================================================================

class CommandCenter:
    """Enterprise command center for OSINT operations."""

    def __init__(self) -> None:
        """Initialize command center with all subsystems."""
        self.banner = Banner(BannerColorScheme.DARK_ORANGE)
        self.menu = Menu("HANDYOSINT COMMAND CENTER", MenuColorScheme.DARK_ORANGE)
        self.terminal = Terminal(TerminalColorScheme.GREEN_PLASMA)
        self.db = DatabaseManager()
        self.running = True

        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)

        self._setup_menu()

    def _setup_menu(self) -> None:
        """Configure main menu items."""
        self.menu.add_item(
            "1",
            "Single Target Scan",
            "Scan a single username across platforms",
            icon="🔍",
            action=self.handle_single_scan
        )
        self.menu.add_item(
            "2",
            "Batch Scan",
            "Scan multiple targets in sequence",
            icon="📦",
            action=self.handle_batch_scan
        )
        self.menu.add_item(
            "3",
            "Search History",
            "Query previous scan results",
            icon="📚",
            action=self.handle_search_history
        )
        self.menu.add_item(
            "4",
            "View Statistics",
            "Display scan statistics and insights",
            icon="📊",
            action=self.handle_statistics
        )
        self.menu.add_item(
            "5",
            "Target Correlation",
            "View correlated profiles for a target",
            icon="🔗",
            action=self.handle_target_correlation
        )
        self.menu.add_item(
            "6",
            "Intelligence Summary",
            "View overall intelligence summary",
            icon="📈",
            action=self.handle_intelligence_summary
        )
        self.menu.add_item(
            "0",
            "Exit",
            "Gracefully shutdown the system",
            icon="⏻",
            action=self.handle_exit
        )

    def _handle_signal(self, signum: int, frame: Optional[Any] = None) -> None:
        """Handle interrupt signals. Frame argument required by signal handler."""
        logger.info("Received signal: %s", signum)
        self.running = False

    async def handle_single_scan(self) -> None:
        """Handle single target scan."""
        self.terminal.clear()
        self.banner.display("scan", animate=False)
        self.menu.display_info("SINGLE TARGET SCAN - Username Intelligence")

        username = self.menu.prompt_input("ENTER TARGET USERNAME")

        if not username:
            self.menu.display_warning("Operation cancelled")
            return

        self.menu.display_processing("Scanning target: %s" % username)
        await asyncio.sleep(1)

        await self.db.save_result(
            target=username,
            platform="demonstration",
            status="COMPLETED",
            url="https://example.com",
            scan_type="single",
            details={"demo": True}
        )

        self.menu.display_success("Scan completed for %s" % username)
        self.menu.prompt_selection("PRESS ENTER TO CONTINUE")

    async def handle_batch_scan(self) -> None:
        """Handle batch scan operations."""
        self.terminal.clear()
        self.banner.display("analysis", animate=False)
        self.menu.display_info("BATCH SCAN MODE")

        targets_input = self.menu.prompt_input(
            "ENTER TARGETS (comma-separated)"
        )

        if not targets_input:
            self.menu.display_warning("Operation cancelled")
            return

        targets = [t.strip() for t in targets_input.split(",")]
        self.menu.display_processing("Processing %d targets..." % len(targets))

        for target in targets:
            await self.db.save_result(
                target=target,
                platform="batch_scan",
                status="COMPLETED",
                scan_type="batch",
                details={"batch_size": len(targets)}
            )
            await asyncio.sleep(0.2)

        self.menu.display_success("Batch scan completed: %d targets" % len(targets))
        self.menu.prompt_selection("PRESS ENTER TO CONTINUE")

    async def handle_search_history(self) -> None:
        """Handle history search."""
        self.terminal.clear()
        self.banner.display("results", animate=False)
        self.menu.display_info("SEARCH SCAN HISTORY")

        search_term = self.menu.prompt_input("ENTER SEARCH TERM")

        if not search_term:
            self.menu.display_warning("Operation cancelled")
            return

        self.menu.display_processing("Searching database...")
        results = await self.db.search_results(search_term)

        if results:
            headers = ["ID", "Target", "Platform", "Status", "URL"]
            rows = [
                [str(r["id"]), r["target"], r["platform"],
                 r["status"], r["url"][:40]]
                for r in results[:10]
            ]
            self.menu.display_table(headers, rows, title="Search Results")
            self.menu.display_info("Found %d results" % len(results))
        else:
            self.menu.display_warning("No results found for: %s" % search_term)

        self.menu.prompt_selection("PRESS ENTER TO CONTINUE")

    async def handle_statistics(self) -> None:
        """Handle statistics display."""
        self.terminal.clear()
        self.banner.display("dashboard", animate=False)
        self.menu.display_info("INTELLIGENCE STATISTICS")

        stats = await self.db.get_statistics()

        if stats:
            content = (
                f"\nTotal Scans: {stats.get('total_scans', 0)}\n"
                f"Found Profiles: {stats.get('found_profiles', 0)}\n"
                f"Unique Targets: {stats.get('unique_targets', 0)}\n"
                f"Platforms Scanned: {len(stats.get('platforms', {}))}\n"
                f"\nPlatform Breakdown:"
            )

            for platform, count in stats.get("platforms", {}).items():
                content += f"\n  {platform}: {count} scans"

            self.menu.display_panel("Statistics", content)
        else:
            self.menu.display_warning("No statistics available")

        self.menu.prompt_selection("PRESS ENTER TO CONTINUE")

    async def handle_target_correlation(self) -> None:
        """Handle target correlation analysis."""
        self.terminal.clear()
        self.banner.display("analysis", animate=False)
        self.menu.display_info("TARGET CORRELATION ANALYSIS")

        target = self.menu.prompt_input("ENTER TARGET USERNAME")

        if not target:
            self.menu.display_warning("Operation cancelled")
            return

        self.menu.display_processing("Correlating profiles...")
        correlated = await self.db.get_correlated_target_profiles(target)

        if correlated.get("profiles_by_platform"):
            content = f"\nTarget: {correlated['target']}\n"
            content += f"Profiles Found: {len(correlated['profiles_by_platform'])}\n"
            content += "\nStatus Summary:\n"

            for status, count in correlated.get("status_counts", {}).items():
                content += f"  {status}: {count}\n"

            content += "\nRecent Activity:\n"
            for entry in correlated.get("history_summary", [])[:5]:
                content += f"  {entry}\n"

            self.menu.display_panel("Target Correlation", content)
        else:
            self.menu.display_warning(f"No profiles found for: {target}")

        self.menu.prompt_selection("PRESS ENTER TO CONTINUE")

    async def handle_intelligence_summary(self) -> None:
        """Handle overall intelligence summary."""
        self.terminal.clear()
        self.banner.display("dashboard", animate=False)
        self.menu.display_info("INTELLIGENCE SUMMARY")

        summary = await self.db.get_overall_correlation_summary()

        if summary and "error" not in summary:
            content = (
                f"\nTotal Scans: {summary.get('total_scans_recorded', 0)}\n"
                f"Unique Targets: {summary.get('unique_targets_scanned', 0)}\n"
                f"\nTop Targets by Profiles:\n"
            )

            for target_info in summary.get("top_targets_by_profiles_found", [])[:5]:
                content += (
                    f"  {target_info.get('target', 'Unknown')}: "
                    f"{target_info.get('profiles_found_count', 0)} profiles\n"
                )

            content += "\nPlatform Activity:\n"
            for platform, stats in summary.get("platforms_activity", {}).items():
                content += f"  {platform}: {stats.get('total', 0)} scans\n"

            self.menu.display_panel("Intelligence Summary", content)
        else:
            self.menu.display_warning("Unable to retrieve summary")

        self.menu.prompt_selection("PRESS ENTER TO CONTINUE")

    async def handle_exit(self) -> None:
        """Handle graceful exit."""
        if self.menu.prompt_confirm("Shutdown system?"):
            self.terminal.shutdown_sequence()
            self.running = False

    async def run(self) -> None:
        """Main command center loop."""
        self.terminal.clear()
        self.terminal.boot_sequence()
        self.banner.display("main", animate=True)

        while self.running:
            try:
                self.menu.display()
                selection = self.menu.prompt_selection("SELECT OPERATION")

                if selection == "0":
                    await self.handle_exit()
                else:
                    item = self.menu.get_item(selection)
                    if item and item.action:
                        await item.action()

            except KeyboardInterrupt:
                self.menu.display_warning("Operation interrupted")
                if not self.menu.prompt_confirm("Continue?"):
                    await self.handle_exit()
            except (OSError, asyncio.TimeoutError) as exc:
                logger.error("Command execution error: %s", exc)
                self.menu.display_error(f"Error: {str(exc)}")


# ========================================================================
# MAIN ENTRY POINT
# ========================================================================

async def main() -> None:
    """Main application entry point."""
    try:
        command_center = CommandCenter()
        await command_center.run()
    except (OSError, RuntimeError, asyncio.TimeoutError) as exc:
        logger.error("Fatal error: %s", exc)
        print(f"\n\033[91m[FATAL ERROR] {exc}\033[0m")
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n\033[93m[SYSTEM] Interrupted by user\033[0m")
        sys.exit(0)

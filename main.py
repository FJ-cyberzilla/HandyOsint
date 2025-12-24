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
import json
import logging
import signal
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from rich.panel import Panel
from rich.table import Table

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
    from core.analysis import AdvancedAnalysisEngine
    from core.audit import AuditLogger
    from core.integration import ExportFormat, IntegrationCoordinator, ScanPriority
    from core.models import AuditAction, AuditLogEntry, PlatformResult, ScanAnalysis
    from core.production_scanner import (  # Split into two lines
        ProductionScanner,
        UsernameSearchResult,
    )
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

    async def _execute_db_operation(
        self, func: Callable, *args: Any, **kwargs: Any
    ) -> Any:
        """Execute blocking DB operation in thread pool."""
        return await asyncio.to_thread(func, *args, **kwargs)

    async def save_result(
        self,
        target: str,
        platform: str,
        status: str,  # pylint: disable=too-many-arguments,too-many-positional-arguments
        url: str = "",
        scan_type: str = "",
        details: Optional[Dict] = None,
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
                results.append(
                    {
                        "id": row[0],
                        "timestamp": row[1],
                        "target": row[2],
                        "platform": row[3],
                        "status": row[4],
                        "url": row[5],
                        "scan_type": row[6],
                    }
                )

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
                results.append(
                    {
                        "id": row[0],
                        "timestamp": row[1],
                        "target": row[2],
                        "platform": row[3],
                        "status": row[4],
                        "url": row[5],
                        "scan_type": row[6],
                    }
                )

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

    async def get_correlated_target_profiles(self, target: str) -> Dict[str, Any]:
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
                "history_summary": [],
            }

            for row in raw_results:
                platform = row["platform"]
                status = row["status"]

                if platform not in correlated_data["profiles_by_platform"]:
                    correlated_data["profiles_by_platform"][platform] = []

                correlated_data["profiles_by_platform"][platform].append(
                    {
                        "status": status,
                        "url": row["url"],
                        "timestamp": row["timestamp"],
                        "created_at": row["created_at"],
                        "details": (
                            json.loads(row["details"]) if row["details"] else None
                        ),
                    }
                )

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
                "error": str(exc),
            }

    async def get_overall_correlation_summary(
        self, limit_targets: int = 10
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
                "recent_activity_overview": [],
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
                (limit_targets,),
            )
            summary_data["top_targets_by_profiles_found"] = [
                dict(row) for row in cursor.fetchall()
            ]

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
                        "rate_limited": 0,
                    }

                summary_data["platforms_activity"][platform]["total"] += count
                summary_data["platforms_activity"][platform][status] = (
                    summary_data["platforms_activity"][platform].get(status, 0) + count
                )

            cursor.execute(
                """
                SELECT status, COUNT(*) as count
                FROM scan_results
                GROUP BY status
                ORDER BY count DESC
                """
            )
            summary_data["status_distribution"] = {
                row["status"]: row["count"] for row in cursor.fetchall()
            }

            cursor.execute(
                """
                SELECT target, platform, status, created_at
                FROM scan_results
                ORDER BY created_at DESC
                LIMIT 5
                """
            )
            summary_data["recent_activity_overview"] = [
                dict(row) for row in cursor.fetchall()
            ]

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


class CommandCenter:  # pylint: disable=too-many-instance-attributes,no-member
    """Enterprise command center for OSINT operations."""

    def __init__(self) -> None:
        """Initialize command center with all subsystems."""
        self.banner = Banner(BannerColorScheme.DARK_ORANGE)
        self.menu = Menu("HANDYOSINT COMMAND CENTER", MenuColorScheme.DARK_ORANGE)
        self.terminal = Terminal(TerminalColorScheme.GREEN_PLASMA)
        self.db = DatabaseManager()
        self.audit_logger = AuditLogger(db_path=str(BASE_DIR / "data" / "audit.db"))
        self.analysis_engine = AdvancedAnalysisEngine()
        self.coordinator = IntegrationCoordinator()
        self.scanner = ProductionScanner()  # Initialize the actual scanner
        self.running = True
        self.worker_task: Optional[asyncio.Task] = None  # To hold the worker task

        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)

        self._setup_menu()

    async def _scan_worker_task(self) -> None:
        """Asynchronous worker to process scan tasks from the queue."""
        logger.info("Scan worker task started.")
        async with self.scanner:  # Use async with for proper context management
            while self.running:
                try:
                    task = await self.coordinator.orchestrator.task_queue.dequeue()
                    if task:
                        logger.info(
                            "Worker dequeued task: %s for user %s",
                            task.task_id,
                            task.username,
                        )
                        task.metadata.status = "in_progress"
                        task.metadata.started_at = datetime.now().isoformat()

                        scan_result: UsernameSearchResult = (
                            await self.scanner.scan_username(task.username)
                        )

                        # --- Data Transformation & Analysis ---
                        scan_analysis = ScanAnalysis(
                            username=scan_result.username,
                            scan_id=task.task_id,  # Use task_id as scan_id for now
                            timestamp=scan_result.timestamp,
                            total_platforms=scan_result.total_platforms,
                            profiles_found=scan_result.profiles_found,
                            scan_duration=scan_result.scan_duration,
                            errors=scan_result.errors,
                            platforms={
                                p_id: PlatformResult(
                                    platform_id=p_id,
                                    platform_name=p_detail.platform,
                                    found=p_detail.found,
                                    url=p_detail.url,
                                    status=p_detail.status,
                                    response_time=p_detail.response_time,
                                    status_code=p_detail.status_code,
                                )
                                for p_id, p_detail in scan_result.platforms.items()
                            },
                        )

                        # Perform analysis
                        risk_score, risk_level = (
                            self.analysis_engine.calculate_risk_score(scan_analysis)
                        )
                        scan_analysis.overall_risk_score = risk_score
                        scan_analysis.risk_level = risk_level.label

                        correlation_data = self.analysis_engine.analyze_correlations(
                            scan_analysis
                        )
                        scan_analysis.correlation_data = correlation_data
                        # --- End Data Transformation & Analysis ---

                        # Save individual platform results to the database
                        for platform_id, detail in scan_result.platforms.items():
                            await self.db.save_result(
                                target=scan_result.username,
                                platform=platform_id,
                                status=detail.status,
                                url=detail.url,
                                scan_type="batch",
                                details=detail.to_dict(),
                            )

                        # Update Orchestrator with result (using the analyzed scan_analysis)
                        self.coordinator.update_task_result(
                            task.task_id,
                            scan_analysis.to_dict(),  # Pass the full analyzed data # pylint: disable=no-member
                            status="completed" if not scan_result.errors else "failed",
                        )
                        logger.info("Worker completed task: %s", task.task_id)
                    else:
                        await asyncio.sleep(0.5)  # Wait if queue is empty
                except asyncio.CancelledError:
                    logger.info("Scan worker task cancelled.")
                    break
                except Exception as exc:  # pylint: disable=broad-except
                    logger.error("Error in scan worker task: %s", exc, exc_info=True)
                    # Attempt to mark task as failed if an exception occurs
                    if task:
                        self.coordinator.update_task_result(
                            task.task_id, {"error": str(exc)}, status="failed"
                        )
                    await asyncio.sleep(1)  # Prevent busy-loop on persistent errors
        logger.info("Scan worker task stopped.")

    async def _start_worker(self) -> None:
        """Start the background worker task."""
        if self.worker_task is None or self.worker_task.done():
            self.worker_task = asyncio.create_task(self._scan_worker_task())
            logger.info("Background scan worker task initiated.")

    async def _stop_worker(self) -> None:
        """Stop the background worker task."""
        if self.worker_task and not self.worker_task.done():
            self.worker_task.cancel()
            await self.worker_task
            logger.info("Background scan worker task stopped.")

    def _handle_signal(
        self, signum: int, frame: Optional[Any] = None
    ) -> None:  # pylint: disable=unused-argument
        """Handle interrupt signals. Frame argument required by signal handler."""
        logger.info("Received signal: %s", signum)
        self.running = False
        # The worker will be gracefully stopped in run() and main()

    def _display_scan_results(self, scan_analysis: ScanAnalysis):
        """Displays the results of a scan analysis."""
        self.terminal.clear()
        self.banner.display("results", animate=False)

        risk_level = scan_analysis.risk_level
        risk_score = scan_analysis.overall_risk_score

        # Summary Panel
        summary_panel = Panel(
            f"[bold]Username:[/bold] {scan_analysis.username}\n"
            f"[bold]Profiles Found:[/bold] {scan_analysis.profiles_found}/{scan_analysis.total_platforms}\n"
            f"[bold]Risk Score:[/bold] {risk_score:.2f}\n"
            f"[bold]Risk Level:[/bold] {risk_level}\n"
            f"[bold]Scan Duration:[/bold] {scan_analysis.scan_duration:.2f}s",
            title="Scan Summary",
            border_style="cyan",
        )
        self.terminal.console.print(summary_panel)

        # Results Table
        table_title = "Platform Scan Results"
        results_table = Table(  # pylint: disable=line-too-long
            title=table_title, border_style="magenta"
        )
        results_table.add_column("Platform", style="cyan", no_wrap=True)
        results_table.add_column("Status", style="green")
        results_table.add_column("URL", style="yellow")

        for result in sorted(
            scan_analysis.platforms.values(), key=lambda r: r.platform_name
        ):
            status = (
                "[green]✓ Found[/green]" if result.found else "[red]✗ Not Found[/red]"
            )
            results_table.add_row(result.platform_name, status, result.url)

        self.terminal.console.print(results_table)

        # Correlation Panel
        correlation_data = scan_analysis.correlation_data
        if correlation_data:
            corr_content = ""
            if correlation_data.common_patterns:
                corr_content += "[bold]Common Patterns:[/bold]\n"
                corr_content += "\n".join(
                    f"- {p}" for p in correlation_data.common_patterns
                )
                corr_content += "\n\n"
            if correlation_data.likely_connections:
                corr_content += "[bold]Likely Connections:[/bold]\n"
                for p, conns in correlation_data.likely_connections.items():
                    if conns:
                        corr_content += f"- {p} -> {', '.join(conns)}\n"

            if corr_content:
                correlation_panel = Panel(
                    corr_content, title="Correlation Analysis", border_style="yellow"
                )
                self.terminal.console.print(correlation_panel)

    async def handle_single_scan(self) -> None:
        """Handle single target scan by submitting it as a high-priority job."""
        self.terminal.clear()
        self.banner.display("scan", animate=False)
        self.menu.display_info("SINGLE TARGET SCAN - Username Intelligence")

        username = self.menu.prompt_input("ENTER TARGET USERNAME")

        if not username:
            self.menu.display_warning("Operation cancelled")
            return

        self.menu.display_processing(
            f"Submitting single target scan for: {username}..."
        )

        # Create a batch job with a single username, high priority
        job = self.coordinator.execute_batch_scan(
            usernames=[username],
            priority=ScanPriority.CRITICAL,  # Single scans are critical/high priority
            export_formats=[],  # No immediate export for single scans, handled by worker
        )

        self.audit_logger.log(
            AuditLogEntry(
                timestamp=datetime.now().isoformat(),
                action=AuditAction.SCAN_COMPLETE.value,  # Log as COMPLETE after job submission
                username=username,
                scan_id=job.job_id,
                details={
                    "duration": "N/A (background)",
                    "profiles_found": "N/A (background)",
                    "status": "Job submitted",
                    "type": "single_target",
                },
            )
        )

        self.menu.display_success(
            f"Single target scan job '{job.job_id}' created for '{username}'. "
            "Monitoring its status via 'View Batch Job Status'."
        )
        self.menu.prompt_selection("PRESS ENTER TO CONTINUE")

    async def handle_batch_scan(self) -> None:
        """Handle batch scan operations."""
        self.terminal.clear()
        self.banner.display("analysis", animate=False)
        self.menu.display_info("BATCH SCAN MODE")

        targets_input = self.menu.prompt_input("ENTER TARGETS (comma-separated)")

        if not targets_input:
            self.menu.display_warning("Operation cancelled")
            return

        usernames = [t.strip() for t in targets_input.split(",")]

        # Prompt for export formats
        export_choices = {
            "1": ExportFormat.JSON,
            "2": ExportFormat.CSV,
            "3": ExportFormat.TEXT,
            "4": ExportFormat.HTML,
        }
        export_format_options_str = (
            "1: JSON, 2: CSV, 3: TEXT, 4: HTML (comma-separated, e.g., 1,3)"
        )
        selected_formats = []
        while True:
            format_input = self.menu.prompt_input(
                f"SELECT EXPORT FORMATS ({export_format_options_str} - empty for default JSON,HTML)"
            )
            if not format_input:
                selected_formats = [ExportFormat.JSON, ExportFormat.HTML]
                break

            try:
                choices = [c.strip() for c in format_input.split(",")]
                temp_formats = []
                for choice in choices:
                    if choice in export_choices:
                        temp_formats.append(export_choices[choice])
                    else:
                        self.menu.display_warning(f"Invalid format choice: {choice}")
                if temp_formats:
                    selected_formats = temp_formats
                    break

                self.menu.display_warning(
                    "No valid export formats selected. Please try again."
                )
            except Exception:  # pylint: disable=broad-except
                self.menu.display_warning(
                    "Invalid input. Please use comma-separated numbers."
                )

        self.menu.display_processing(
            f"Initiating batch scan for {len(usernames)} targets..."
        )

        job = self.coordinator.execute_batch_scan(
            usernames=usernames,
            priority=ScanPriority.NORMAL,  # Default to NORMAL priority for now
            export_formats=selected_formats,
        )
        # The orchestration is handled internally by IntegrationCoordinator,
        # so we just need to confirm the job creation.
        self.menu.display_success(
            f"Batch scan job '{job.job_id}' created for {len(usernames)} targets. "
            f"Status: {job.status}"
        )
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
                [str(r["id"]), r["target"], r["platform"], r["status"], r["url"][:40]]
                for r in results[:10]
            ]
            self.menu.display_table(headers, rows, title="Search Results")
            self.menu.display_info(f"Found {len(results)} results")
        else:
            self.menu.display_warning(f"No results found for: {search_term}")

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
                "\nPlatform Breakdown:"
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
                    f"{target_info.get('profiles_found_count', 0)} "
                    "profiles\n"
                )

            content += "\nPlatform Activity:\n"
            for platform, stats in summary.get("platforms_activity", {}).items():
                content += f"  {platform}: {stats.get('total', 0)} scans\n"

            self.menu.display_panel("Intelligence Summary", content)
        else:
            self.menu.display_warning("Unable to retrieve summary")

        self.menu.prompt_selection("PRESS ENTER TO CONTINUE")

    async def handle_view_batch_jobs(self) -> None:
        """Handle viewing batch job status."""
        self.terminal.clear()
        self.banner.display("dashboard", animate=False)
        self.menu.display_info("BATCH JOB STATUS")
        self.coordinator.display_all_jobs()
        self.menu.prompt_selection("PRESS ENTER TO CONTINUE")

    async def handle_view_metrics(self) -> None:
        """Handle viewing aggregated scan metrics."""
        self.terminal.clear()
        self.banner.display("dashboard", animate=False)
        self.menu.display_info("AGGREGATED SCAN METRICS")
        self.coordinator.display_metrics()
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

        await self._start_worker()  # Start the background worker task

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

        await self._stop_worker()  # Stop the background worker task


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

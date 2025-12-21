#!/usr/bin/env python3
"""
HANDYOSINT - Enterprise Production Command Center v3.0
Complete OSINT Intelligence Platform with 16-bit Vintage Aesthetics
"""

import asyncio
import sys
import shutil
import json
import signal
import sqlite3
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List
from config.app_config import AppConfig

# ============================================================================
# PATH CONFIGURATION
# ============================================================================

BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR / "ui"))
sys.path.insert(0, str(BASE_DIR / "core"))

# Initialize app_config here
from config.app_config import AppConfig
app_config = AppConfig(BASE_DIR)

# ============================================================================
# IMPORTS
# ============================================================================

try:
    from ui.banner import Banner, BannerColorScheme
    from ui.menu import Menu, MenuColorScheme
    from ui.terminal import Terminal, TerminalColorScheme
except ImportError as e:
    print(f"\033[91m[FATAL ERROR] Failed to import UI modules: {e}\033[0m")
    sys.exit(1)

# Optional core modules
try:
    from core.error_handler import get_error_handler, ErrorSeverity

    DOCS_AVAILABLE = True
except ImportError:
    DOCS_AVAILABLE = False

try:
    from core.production_scanner import ProductionScanner as SocialScanApp

    SCANNER_AVAILABLE = True
except ImportError:
    SCANNER_AVAILABLE = False

# ============================================================================
# LOGGING SETUP
# ============================================================================

LOG_FILE_BASE_PATH = BASE_DIR / Path(app_config.get('logging.file'))
LOG_DIR = LOG_FILE_BASE_PATH.parent
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=app_config.get('logging.level', 'INFO'),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(
            LOG_DIR / f'handyosint_{datetime.now().strftime("%Y%m%d")}.log'
        ),
        logging.StreamHandler(),
    ],
)

logger = logging.getLogger("HandyOsint")
error_handler = get_error_handler(log_dir=LOG_DIR)

# ============================================================================
# DATABASE MANAGER
# ============================================================================


class DatabaseManager:
    """SQLite database operations"""

    def __init__(self):
        self.db_path = BASE_DIR / Path(app_config.get('database.path'))
        self.db_path.parent.mkdir(exist_ok=True)
        self._init_database_sync()

    def _init_database_sync(self) -> None:
        """Initialize database schema (synchronous version for init)"""
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
                "CREATE INDEX IF NOT EXISTS idx_timestamp ON " "scan_results(timestamp)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_platform ON " "scan_results(platform)"
            )

            conn.commit()
            conn.close()
            error_handler.log_info(
                "Database initialized successfully",
                context={"db_path": str(self.db_path)},
            )
        except (sqlite3.Error, OSError) as err:
            error_handler.handle_exception(
                err,
                context={"function": "_init_database_sync"},
                severity=ErrorSeverity.CRITICAL,
            )

    async def _execute_db_operation(self, func: callable, *args, **kwargs) -> Any:
        """Helper to run blocking DB operations in a thread pool."""
        return await asyncio.to_thread(func, *args, **kwargs)

    async def save_result(
        self, target: str, platform: str, status: str, details: Dict = None, **kwargs
    ) -> bool:
        """Save scan result asynchronously"""
        url = kwargs.get("url", "")
        scan_type = kwargs.get("scan_type", "")

        def _save():
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
            error_handler.log_info(
                f"Saved result: {target} on {platform}",
                context={"target": target, "platform": platform},
            )
            return success
        except (sqlite3.Error, OSError) as err:
            error_handler.handle_database_error(
                f"Failed to save result: {err}",
                operation="save_result",
                context={"target": target, "platform": platform},
            )
            return False

    async def get_scan_history(self, limit: int = 50) -> List[Dict]:
        """Retrieve scan history asynchronously"""

        def _get_history():
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
        except (sqlite3.Error, OSError) as err:
            error_handler.handle_database_error(
                f"Failed to retrieve history: {err}", operation="get_scan_history"
            )
            return []

    async def search_results(self, target: str) -> List[Dict]:
        """Search results by target asynchronously"""

        def _search():
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
        except (sqlite3.Error, OSError) as err:
            error_handler.handle_database_error(
                f"Search failed: {err}",
                operation="search_results",
                context={"query_target": target},
            )
            return []

    async def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics asynchronously"""

        def _get_stats():
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
        except (sqlite3.Error, OSError) as err:
            error_handler.handle_database_error(
                f"Statistics retrieval failed: {err}", operation="get_statistics"
            )
            return {}


# ============================================================================
# COMMAND CENTER HANDLERS (Separate Module)
# ============================================================================


class CommandCenterHandlers:
    """Handler methods extracted for code organization"""

    def __init__(self, command_center):
        self.cc = command_center

    async def handle_single_scan(self) -> None:
        """Handle single target scan"""
        self.cc.terminal.clear()
        self.cc.banner.display("scan")

        self.cc.menu.display_info("SINGLE TARGET SCAN - Username Intelligence")

        username = await self.cc.menu.prompt(
            "ENTER TARGET USERNAME (or 'back' to return)"
        )

        if not username or username.lower() in ["back", "exit", "0"]:
            return

        if not self.cc.scanner:
            self.cc.menu.display_error("Scanner not available.")
            await self.cc.menu.prompt("PRESS ENTER TO CONTINUE")
            return

        self.cc.terminal.write_info(f"\nScanning: {username}")

        try:
            async with self.cc.scanner as scanner_instance:
                result = await scanner_instance.scan_username(username)
                await self._display_scan_results(result)

                for _, data in result.platforms.items():
                    await self.cc.db.save_result(
                        target=username,
                        platform=data.platform,
                        status=data.status,
                        url=data.url,
                        scan_type="USERNAME_SCAN",
                    )

            self.cc.increment_session_scans()
            self.cc.menu.display_success("Scan completed and saved")
        except (OSError, asyncio.TimeoutError, ValueError) as err:
            error_handler.handle_scan_error(
                f"Scan error: {err}",
                target=username,
                context={"function": "handle_single_scan"},
            )
            self.cc.menu.display_error(f"Scan failed: {err}")

        await self.cc.menu.prompt("PRESS ENTER TO CONTINUE")

    async def _display_scan_results(self, result) -> None:
        """Display scan results"""
        self.cc.terminal.clear()
        self.cc.banner.display("scan")

        headers = ["Platform", "Status", "URL"]
        rows = []

        for _, data in result.platforms.items():
            icon = "✓" if data.found else "✗"
            url_display = data.url[:40] + "..." if len(data.url) > 40 else data.url
            styled_status = self._get_styled_status(data.status)
            rows.append([data.platform, Text.assemble(icon + " ", styled_status), url_display])

        self.cc.menu.display_table(headers, rows, f"SCAN RESULTS - {result.username}")

        summary = [
            f"Target: {result.username}",
            f"Profiles Found: {result.profiles_found}/{result.total_platforms}",
            f"Timestamp: {result.timestamp}",
        ]

        self.cc.menu.display_box("SUMMARY", summary)

    def _get_styled_status(self, status: str) -> Any: # Returns rich.Text or str
        """Returns rich.Text with color based on status."""
        status_lower = status.lower()
        if status_lower == "found":
            return Text(status, style="green")
        elif status_lower == "not_found":
            return Text(status, style="yellow")
        elif status_lower == "blocked":
            return Text(status, style="orange3") # User implied "not intent to block" for red.
        elif status_lower == "error":
            return Text(status, style="red")
        else:
            return Text(status, style="white")

    async def handle_batch_operations(self) -> None:
        """Handle batch scanning"""
        self.cc.terminal.clear()
        self.cc.banner.display("batch")

        self.cc.menu.display_info("BATCH OPERATIONS - Multiple Target Intelligence")

        targets_input = await self.cc.menu.prompt(
            "ENTER TARGETS (comma-separated) or 'back'"
        )

        if not targets_input or targets_input.lower() in ["back", "exit", "0"]:
            return

        targets = [t.strip() for t in targets_input.split(",") if t.strip()]

        if not targets:
            self.cc.menu.display_warning("No valid targets entered")
            await self.cc.menu.prompt("PRESS ENTER TO CONTINUE")
            return

        if not self.cc.scanner:
            self.cc.menu.display_error("Scanner not available.")
            await self.cc.menu.prompt("PRESS ENTER TO CONTINUE")
            return

        self.cc.menu.display_info(f"Processing {len(targets)} targets...")

        try:
            with self.cc.terminal.progress_bar(
                len(targets), "Batch Scanning..."
            ) as progress:
                task = progress.add_task("scan", total=len(targets))
                async with self.cc.scanner as scanner_instance:
                    for target in targets:
                        result = await scanner_instance.scan_username(target)

                        for _, data in result.platforms.items():
                            await self.cc.db.save_result(
                                target=target,
                                platform=data.platform,
                                status=data.status,
                                url=data.url,
                                scan_type="BATCH_SCAN",
                            )

                        self.cc.increment_session_scans()
                        progress.update(task, advance=1)

            self.cc.menu.display_success(
                f"Batch scan completed: {len(targets)} targets processed"
            )
        except (OSError, asyncio.TimeoutError, ValueError) as err:
            error_handler.handle_scan_error(
                f"Batch scan error: {err}",
                context={"targets": targets, "function": "handle_batch_operations"},
            )
            self.cc.menu.display_error(f"Batch scan failed: {err}")

        await self.cc.menu.prompt("PRESS ENTER TO CONTINUE")

    async def handle_dashboard(self) -> None:
        """Display intelligence dashboard"""
        self.cc.terminal.clear()
        self.cc.banner.display("dashboard")

        self.cc.menu.display_info("INTELLIGENCE DASHBOARD")

        uptime_str = self.cc.get_uptime_str()
        stats = await self.cc.db.get_statistics()

        scanner_info = {}
        if self.cc.scanner:
            scanner_info = self.cc.scanner.get_platform_info()

        request_stats = scanner_info.get("request_stats", {})

        headers = ["Metric", "Value", "Status"]
        rows = [
            ["System Uptime", uptime_str, "🟢"],
            ["Scans This Session (CLI)", str(self.cc.get_session_scans()), "🟢"],
            ["Total Database Scans", str(stats.get("total_scans", 0)), "📊"],
            ["Profiles Found (DB)", str(stats.get("found_profiles", 0)), "✓"],
            ["Unique Targets (DB)", str(stats.get("unique_targets", 0)), "🎯"],
            [
                "Total Scanner Requests",
                str(request_stats.get("total_requests", 0)),
                "⚡",
            ],
            ["Redis Cache Size", str(request_stats.get("redis_cache_size", 0)), "📦"],
        ]

        self.cc.menu.display_table(headers, rows, "SYSTEM STATISTICS")

        if stats.get("platforms"):
            platform_rows = []
            for platform, count in stats["platforms"].items():
                platform_rows.append([platform, str(count)])

            self.cc.menu.display_table(
                ["Platform", "Scans"], platform_rows, "PLATFORM BREAKDOWN"
            )

        await self.cc.menu.prompt("PRESS ENTER TO CONTINUE")

    async def handle_scan_history(self) -> None:
        """Display scan history"""
        self.cc.terminal.clear()
        self.cc.banner.display("history")

        self.cc.menu.display_info("SCAN HISTORY")

        history = await self.cc.db.get_scan_history(50)

        if not history:
            self.cc.menu.display_warning("No scan history available")
            await self.cc.menu.prompt("PRESS ENTER TO CONTINUE")
            return

        headers = ["#", "Target", "Platform", "Status", "Date"]
        rows = []

        for i, record in enumerate(history[:20], 1):
            timestamp = datetime.fromisoformat(record["timestamp"]).strftime(
                "%Y-%m-%d %H:%M"
            )
            rows.append(
                [
                    str(i),
                    record["target"][:15],
                    record["platform"][:12],
                    self._get_styled_status(record["status"]),
                    timestamp,
                ]
            )

        self.cc.menu.display_table(
            headers, rows, f"RECENT SCANS (Total: {len(history)})"
        )

        search = await self.cc.menu.prompt("SEARCH BY TARGET (or 'back')")

        if search and search.lower() not in ["back", "0"]:
            results = await self.cc.db.search_results(search)

            if results:
                search_rows = []
                for i, record in enumerate(results[:20], 1):
                    timestamp = datetime.fromisoformat(record["timestamp"]).strftime(
                        "%Y-%m-%d %H:%M"
                    )
                    search_rows.append(
                        [
                            str(i),
                            record["target"],
                            record["platform"],
                            self._get_styled_status(record["status"]),
                            timestamp,
                        ]
                    )

                self.cc.menu.display_table(
                    headers, search_rows, f"SEARCH RESULTS - {search}"
                )

        await self.cc.menu.prompt("PRESS ENTER TO CONTINUE")

    async def handle_export(self) -> None:
        """Handle data export"""
        self.cc.terminal.clear()
        self.cc.banner.display("main")

        self.cc.menu.display_info("DATA EXPORT")

        export_options = {
            "1": "Export all scan history",
            "2": "Export statistics report",
            "3": "Export database backup",
            "0": "Return to main menu",
        }

        for key, option in export_options.items():
            print(f"  [{key}] {option}")

        choice = await self.cc.menu.prompt("SELECT EXPORT TYPE")

        if choice == "1":
            await self._export_history()
        elif choice == "2":
            await self._export_statistics()
        elif choice == "3":
            await self._export_backup()

        if choice in ["1", "2", "3"]:
            await self.cc.menu.prompt("PRESS ENTER TO CONTINUE")

    async def _export_history(self) -> None:
        """Export scan history to JSON"""
        try:
            history = await self.cc.db.get_scan_history(999)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            export_file = BASE_DIR / "exports" / f"scan_history_{timestamp}.json"
            export_file.parent.mkdir(exist_ok=True)

            with open(export_file, "w", encoding="utf-8") as f:
                json.dump(history, f, indent=2)

            self.cc.menu.display_success(f"History exported to {export_file.name}")
            error_handler.log_info(f"History exported to {export_file}")
        except (OSError, json.JSONDecodeError, IOError) as err:
            error_handler.handle_exception(err, context={"function": "_export_history"})
            self.cc.menu.display_error(f"Export failed: {err}")

    async def _export_statistics(self) -> None:
        """Export statistics report"""
        try:
            stats = await self.cc.db.get_statistics()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_file = BASE_DIR / "reports" / f"report_{timestamp}.json"
            report_file.parent.mkdir(exist_ok=True)

            report = {
                "generated": datetime.now().isoformat(),
                "statistics": stats,
                "session_scans": self.cc.get_session_scans(),
            }

            with open(report_file, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2)

            self.cc.menu.display_success(f"Report exported to {report_file.name}")
            error_handler.log_info(f"Report exported to {report_file}")
        except (OSError, json.JSONDecodeError, IOError) as err:
            error_handler.handle_exception(
                err, context={"function": "_export_statistics"}
            )
            self.cc.menu.display_error(f"Report generation failed: {err}")

    async def _export_backup(self) -> None:
        """Create database backup"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = BASE_DIR / "backups" / f"backup_{timestamp}.db"
            backup_file.parent.mkdir(exist_ok=True)

            shutil.copy(self.cc.db.db_path, backup_file)

            self.cc.menu.display_success(f"Database backed up to {backup_file.name}")
            error_handler.log_info(f"Database backed up to {backup_file}")
        except (OSError, shutil.Error, IOError) as err:
            error_handler.handle_database_error(
                f"Backup error: {err}", operation="export_backup"
            )
            self.cc.menu.display_error(f"Backup failed: {err}")

    async def handle_configuration(self) -> None:
        """Handle configuration options"""
        self.cc.terminal.clear()
        self.cc.banner.display("main")

        self.cc.menu.display_info("CONFIGURATION")

        config_menu = {
            "1": "Color Scheme",
            "2": "Theme",
            "3": "Animation Settings",
            "0": "Return to main menu",
        }

        for key, option in config_menu.items():
            print(f"  [{key}] {option}")

        choice = await self.cc.menu.prompt("SELECT OPTION")

        if choice == "1":
            await self._select_color_scheme()
        elif choice == "2":
            await self._select_theme()
        elif choice == "3":
            animation_status = (
                "Enabled" if self.cc.banner.animations_enabled else "Disabled"
            )
            self.cc.menu.display_info(f"Animation: {animation_status}")
            self.cc.banner.set_animation(not self.cc.banner.animations_enabled)

        await self.cc.menu.prompt("PRESS ENTER TO CONTINUE")

    async def _select_color_scheme(self) -> None:
        """Select color scheme"""
        schemes = {
            "1": (
                "Green Plasma",
                BannerColorScheme.GREEN_PLASMA,
                MenuColorScheme.GREEN_PLASMA,
            ),
            "2": (
                "Amber Mono",
                BannerColorScheme.AMBER_MONO,
                MenuColorScheme.AMBER_MONO,
            ),
            "3": ("Cool Blue", BannerColorScheme.COOL_BLUE, MenuColorScheme.COOL_BLUE),
            "4": (
                "Monochrome",
                BannerColorScheme.MONOCHROME,
                MenuColorScheme.MONOCHROME,
            ),
        }

        for key, (name, _, _) in schemes.items():
            print(f"  [{key}] {name}")

        choice = await self.cc.menu.prompt("SELECT SCHEME")

        if choice in schemes:
            name, banner_scheme, menu_scheme = schemes[choice]
            self.cc.banner.change_scheme(banner_scheme)
            self.cc.menu.change_scheme(menu_scheme)
            self.cc.menu.display_success(f"Switched to {name}")

    async def _select_theme(self) -> None:
        """Select banner theme"""
        themes = {
            "1": "Modern",
            "2": "Vintage",
        }

        for key, name in themes.items():
            print(f"  [{key}] {name}")

        choice = await self.cc.menu.prompt("SELECT THEME")

        if choice in themes:
            name = themes[choice]
            self.cc.menu.display_success(
                f"Switched to {name} theme (visual impact depends on "
                "current banner display type)"
            )

    async def handle_system_validation(self) -> None:
        """System validation and health check"""
        self.cc.terminal.clear()
        self.cc.banner.display("main")

        self.cc.menu.display_info("SYSTEM VALIDATION")

        checks = {
            "UI Modules": True,
            "Database": True,
            "Scanner": SCANNER_AVAILABLE,
            "Documentation": DOCS_AVAILABLE,
            "Logging": True,
        }

        status_rows = []
        for check, available in checks.items():
            status = "✅ OK" if available else "⚠️  Limited"
            status_rows.append([check, status])

        self.cc.menu.display_table(
            ["Component", "Status"], status_rows, "SYSTEM HEALTH"
        )

        await self.cc.menu.prompt("PRESS ENTER TO CONTINUE")

    async def handle_documentation(self) -> None:
        """Display documentation"""
        self.cc.terminal.clear()
        self.cc.banner.display("main")

        self.cc.menu.display_info("DOCUMENTATION")

        docs = [
            "GETTING STARTED:",
            "  1. Use Single Target Scan for individual usernames",
            "  2. Use Batch Operations for multiple targets",
            "  3. View results in Scan History",
            "",
            "FEATURES:",
            "  • Cross-platform username search",
            "  • Batch processing",
            "  • Complete scan history",
            "  • Export functionality",
            "  • Statistics dashboard",
            "",
            "KEYBOARD SHORTCUTS:",
            "  • Ctrl+C: Exit current operation",
            "  • 0: Return to main menu",
            "  • back/exit: Cancel operation",
        ]

        self.cc.menu.display_box("HELP & DOCUMENTATION", docs)

        await self.cc.menu.prompt("PRESS ENTER TO CONTINUE")


# ============================================================================
# COMMAND CENTER
# ============================================================================


class HandyOsintCommandCenter:
    """Enterprise command center"""

    def __init__(self):
        """Initialize command center"""
        default_banner_scheme_str = app_config.get('ui.default_banner_scheme', 'HEAT_WAVE')
        default_menu_scheme_str = app_config.get('ui.default_menu_scheme', 'GREEN_PLASMA')
        
        default_banner_scheme = getattr(BannerColorScheme, default_banner_scheme_str.upper(), BannerColorScheme.HEAT_WAVE)
        default_menu_scheme = getattr(MenuColorScheme, default_menu_scheme_str.upper(), MenuColorScheme.GREEN_PLASMA)

        self.banner = Banner(default_banner_scheme)
        self.menu = Menu("COMMAND CENTER", default_menu_scheme)
        self.terminal = Terminal(TerminalColorScheme.GREEN_PLASMA)
        self.db = DatabaseManager()
        self.scanner = SocialScanApp() if SCANNER_AVAILABLE else None
        self.running = False
        self.start_time = datetime.now()
        self._session_scans = 0

        self._handlers = CommandCenterHandlers(self)
        self._setup_menu()
        self._setup_signal_handlers()

        logger.info("Command center initialized")

    def get_session_scans(self) -> int:
        """Get current session scans count"""
        return self._session_scans

    def increment_session_scans(self) -> None:
        """Increment session scans"""
        self._session_scans += 1

    def get_uptime_str(self) -> str:
        """Calculate and return uptime string"""
        uptime_seconds = int((datetime.now() - self.start_time).total_seconds())
        uptime_minutes = uptime_seconds // 60
        uptime_hours = uptime_minutes // 60
        return f"{uptime_hours}h {uptime_minutes % 60}m"

    def _setup_signal_handlers(self) -> None:
        """Setup signal handlers for graceful shutdown"""

        def signal_handler(sig, frame):
            del sig, frame
            print(
                f"\n\033[93m[{datetime.now().strftime('%H:%M:%S')}] "
                f"Shutting down...\033[0m"
            )
            self.running = False

        signal.signal(signal.SIGINT, signal_handler)

    def _setup_menu(self) -> None:
        """Setup main menu items"""
        self.menu.add_item(
            "1", "🔍 Single Target Scan", "Deep scan single username across platforms"
        )
        self.menu.add_item(
            "2", "📁 Batch Operations", "Process multiple targets simultaneously"
        )
        self.menu.add_item(
            "3", "📊 Intelligence Dashboard", "View analytics and statistics"
        )
        self.menu.add_item("4", "📋 Scan History", "Review past scanning operations")
        self.menu.add_item("5", "💾 Export Data", "Export findings and reports")
        self.menu.add_item("6", "⚙️  Configuration", "System settings and parameters")
        self.menu.add_item(
            "7", "🛠️  System Validation", "Diagnostic checks and health status"
        )
        self.menu.add_item("8", "📘 Documentation", "Command center manual and guides")
        self.menu.add_item("0", "⏹️  Exit System", "Terminate command center")

    async def initialize(self) -> bool:
        """Initialize and boot command center"""
        try:
            self.terminal.clear()
            self.terminal.boot_sequence()
            await asyncio.sleep(0.5)

            self.terminal.clear()
            self.banner.display("main", animate=True)
            await asyncio.sleep(1)

            scanner_status = "✅ Available" if SCANNER_AVAILABLE else "❌ Not Available"
            docs_status = "✅ Available" if DOCS_AVAILABLE else "⚠️ Limited"

            status_info = [
                f"Scanner: {scanner_status}",
                "Database: ✅ Connected",
                f"Documentation: {docs_status}",
                f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            ]

            self.menu.display_box("SYSTEM STATUS", status_info)

            self.running = True
            self.start_time = datetime.now()

            logger.info("Command center initialized successfully")
            return True
        except (OSError, RuntimeError, asyncio.TimeoutError) as err:
            error_handler.handle_exception(
                err, context={"function": "initialize"}, severity=ErrorSeverity.CRITICAL
            )
            self.menu.display_error(f"Initialization failed: {err}")
            return False

    async def run(self) -> None:
        """Main command center loop"""
        if not await self.initialize():
            return

        while self.running:
            self.terminal.clear()
            self.banner.display("main")
            self.menu.display()

            choice = await self.menu.prompt("SELECT OPTION")

            try:
                if choice == "1":
                    await self._handlers.handle_single_scan()
                elif choice == "2":
                    await self._handlers.handle_batch_operations()
                elif choice == "3":
                    await self._handlers.handle_dashboard()
                elif choice == "4":
                    await self._handlers.handle_scan_history()
                elif choice == "5":
                    await self._handlers.handle_export()
                elif choice == "6":
                    await self._handlers.handle_configuration()
                elif choice == "7":
                    await self._handlers.handle_system_validation()
                elif choice == "8":
                    await self._handlers.handle_documentation()
                elif choice == "0":
                    self.running = False
                else:
                    self.menu.display_warning("Invalid selection")
                    await asyncio.sleep(1)
            except (ValueError, KeyboardInterrupt, asyncio.CancelledError) as err:
                error_handler.handle_exception(
                    err, context={"function": "run"}, severity=ErrorSeverity.ERROR
                )
                self.menu.display_error(f"Error: {err}")
                await asyncio.sleep(2)

        # Shutdown sequence
        self.terminal.clear()
        self.terminal.shutdown_sequence()
        logger.info("Session ended. Total scans: %d", self.get_session_scans())


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================


async def main() -> None:
    """Application entry point"""
    command_center = HandyOsintCommandCenter()
    await command_center.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n\033[93m[SYSTEM] Interrupted by user\033[0m")
        sys.exit(0)
    except (OSError, RuntimeError, asyncio.TimeoutError) as err:
        print(f"\n\033[91m[FATAL ERROR] {err}\033[0m")
        error_handler.handle_exception(
            err, context={"function": "__main__"}, severity=ErrorSeverity.FATAL
        )

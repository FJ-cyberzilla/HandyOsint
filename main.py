#!/usr/bin/env python3
"""
HANDYOSINT - Enterprise Production Command Center v3.0
Complete OSINT Intelligence Platform with 16-bit Vintage Aesthetics
"""

import asyncio
import sys
import os
import json
import signal
import sqlite3
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

# ============================================================================
# PATH CONFIGURATION
# ============================================================================

BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR / 'ui'))
sys.path.insert(0, str(BASE_DIR / 'core'))

# ============================================================================
# IMPORTS
# ============================================================================

try:
    from ui.banner import Banner, BannerColorScheme, BannerTheme
    from ui.menu import Menu, MenuColorScheme
    from ui.terminal import Terminal, TerminalColorScheme
except ImportError as e:
    print(f"\033[91m[FATAL ERROR] Failed to import UI modules: {e}\033[0m")
    sys.exit(1)

# Optional core modules
try:
    from core.error_handler import ErrorHandler
    from core.documentation import IntegratedDocumentation
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

LOG_DIR = BASE_DIR / 'logs'
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / f'handyosint_{datetime.now().strftime("%Y%m%d")}.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('HandyOsint')

# ============================================================================
# DATABASE MANAGER
# ============================================================================

class DatabaseManager:
    """SQLite database operations"""
    
    def __init__(self):
        self.db_path = BASE_DIR / 'data' / 'social_scan.db'
        self.db_path.parent.mkdir(exist_ok=True)
        self._init_database()
    
    def _init_database(self) -> None:
        """Initialize database schema"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Scan results table
            cursor.execute('''
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
            ''')
            
            # Batch jobs table
            cursor.execute('''
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
            ''')
            
            # Create indexes
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_target ON scan_results(target)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON scan_results(timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_platform ON scan_results(platform)')
            
            conn.commit()
            conn.close()
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Database initialization error: {e}")
    
    def save_result(self, target: str, platform: str, status: str, 
                   url: str = "", details: Dict = None, scan_type: str = "") -> bool:
        """Save scan result"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO scan_results 
                (timestamp, target, platform, status, url, details, scan_type)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                datetime.now().isoformat(),
                target,
                platform,
                status,
                url,
                json.dumps(details or {}),
                scan_type
            ))
            
            conn.commit()
            conn.close()
            logger.info(f"Saved result: {target} on {platform}")
            return True
        except Exception as e:
            logger.error(f"Failed to save result: {e}")
            return False
    
    def get_scan_history(self, limit: int = 50) -> List[Dict]:
        """Retrieve scan history"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, timestamp, target, platform, status, url, scan_type
                FROM scan_results
                ORDER BY created_at DESC
                LIMIT ?
            ''', (limit,))
            
            results = []
            for row in cursor.fetchall():
                results.append({
                    'id': row[0],
                    'timestamp': row[1],
                    'target': row[2],
                    'platform': row[3],
                    'status': row[4],
                    'url': row[5],
                    'scan_type': row[6]
                })
            
            conn.close()
            return results
        except Exception as e:
            logger.error(f"Failed to retrieve history: {e}")
            return []
    
    def search_results(self, target: str) -> List[Dict]:
        """Search results by target"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, timestamp, target, platform, status, url, scan_type
                FROM scan_results
                WHERE target LIKE ? OR url LIKE ?
                ORDER BY created_at DESC
            ''', (f"%{target}%", f"%{target}%"))
            
            results = []
            for row in cursor.fetchall():
                results.append({
                    'id': row[0],
                    'timestamp': row[1],
                    'target': row[2],
                    'platform': row[3],
                    'status': row[4],
                    'url': row[5],
                    'scan_type': row[6]
                })
            
            conn.close()
            return results
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM scan_results")
            total_scans = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM scan_results WHERE status = 'FOUND'")
            found_profiles = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(DISTINCT target) FROM scan_results")
            unique_targets = cursor.fetchone()[0]
            
            cursor.execute('''
                SELECT platform, COUNT(*) as count 
                FROM scan_results 
                GROUP BY platform
            ''')
            platforms = dict(cursor.fetchall())
            
            conn.close()
            
            return {
                'total_scans': total_scans,
                'found_profiles': found_profiles,
                'unique_targets': unique_targets,
                'platforms': platforms
            }
        except Exception as e:
            logger.error(f"Statistics retrieval failed: {e}")
            return {}


# ============================================================================
# COMMAND CENTER
# ============================================================================

class HandyOsintCommandCenter:
    """Enterprise command center"""
    
    def __init__(self):
        """Initialize command center"""
        self.banner = Banner(BannerColorScheme.GREEN_PLASMA)
        self.menu = Menu("COMMAND CENTER", MenuColorScheme.GREEN_PLASMA)
        self.terminal = Terminal(TerminalColorScheme.GREEN_PLASMA)
        
        self.db = DatabaseManager()
        self.scanner = SocialScanApp() if SCANNER_AVAILABLE else None
        
        self.running = False
        self.start_time = None
        self.session_scans = 0
        
        self._setup_menu()
        self._setup_signal_handlers()
        
        logger.info("Command center initialized")
    
    def _setup_signal_handlers(self) -> None:
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(sig, frame):
            print(f"\n\033[93m[{datetime.now().strftime('%H:%M:%S')}] Shutting down...\033[0m")
            self.running = False
        
        signal.signal(signal.SIGINT, signal_handler)
    
    def _setup_menu(self) -> None:
        """Setup main menu items"""
        self.menu.add_item(
            "1", "🔍 Single Target Scan", 
            "Deep scan single username across platforms"
        )
        self.menu.add_item(
            "2", "📁 Batch Operations",
            "Process multiple targets simultaneously"
        )
        self.menu.add_item(
            "3", "📊 Intelligence Dashboard",
            "View analytics and statistics"
        )
        self.menu.add_item(
            "4", "📋 Scan History",
            "Review past scanning operations"
        )
        self.menu.add_item(
            "5", "💾 Export Data",
            "Export findings and reports"
        )
        self.menu.add_item(
            "6", "⚙️  Configuration",
            "System settings and parameters"
        )
        self.menu.add_item(
            "7", "🛠️  System Validation",
            "Diagnostic checks and health status"
        )
        self.menu.add_item(
            "8", "📘 Documentation",
            "Command center manual and guides"
        )
        self.menu.add_item(
            "0", "⏹️  Exit System",
            "Terminate command center"
        )
    
    async def initialize(self) -> bool:
        """Initialize and boot command center"""
        try:
            self.terminal.clear()
            self.terminal.boot_sequence()
            await asyncio.sleep(0.5)
            
            self.terminal.clear()
            self.banner.display("main", animate=True)
            await asyncio.sleep(1)
            
            # System status
            status_info = [
                f"Scanner: {'✅ Available' if SCANNER_AVAILABLE else '❌ Not Available'}",
                f"Database: ✅ Connected",
                f"Documentation: {'✅ Available' if DOCS_AVAILABLE else '⚠️ Limited'}",
                f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            ]
            
            self.menu.display_box("SYSTEM STATUS", status_info)
            
            self.running = True
            self.start_time = datetime.now()
            
            logger.info("Command center initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Initialization error: {e}")
            self.menu.display_error(f"Initialization failed: {e}")
            return False
    
    async def handle_single_scan(self) -> None:
        """Handle single target scan"""
        self.terminal.clear()
        self.banner.display("scan")
        
        self.menu.display_info("SINGLE TARGET SCAN - Username Intelligence")
        
        username = await self.menu.prompt("ENTER TARGET USERNAME (or 'back' to return)")
        
        if not username or username.lower() in ['back', 'exit', '0']:
            return
        
        if not self.scanner:
            self.menu.display_error("Scanner not available.")
            await self.menu.prompt("PRESS ENTER TO CONTINUE")
            return

        # Scan
        self.terminal.write_info(f"\nScanning: {username}")
        
        try:
            async with self.scanner as scanner_instance:
                result = await scanner_instance.scan_username(username)
                await self._display_scan_results(result)
            
                # Save to database
                for platform_id, data in result.platforms.items():
                    self.db.save_result(
                        target=username,
                        platform=data.platform,
                        status=data.status,
                        url=data.url,
                        scan_type='USERNAME_SCAN'
                    )
            
            self.session_scans += 1
            self.menu.display_success("Scan completed and saved")
        except Exception as e:
            logger.error(f"Scan error: {e}")
            self.menu.display_error(f"Scan failed: {e}")
        
        await self.menu.prompt("PRESS ENTER TO CONTINUE")
    
    async def _display_scan_results(self, result) -> None:
        """Display scan results"""
        self.terminal.clear()
        self.banner.display("scan")
        
        headers = ["Platform", "Status", "URL"]
        rows = []
        
        for platform_id, data in result.platforms.items():
            icon = "✓" if data.found else "✗"
            rows.append([
                data.platform,
                f"{icon} {data.status}",
                data.url[:40] + "..." if len(data.url) > 40 else data.url
            ])
        
        self.menu.display_table(headers, rows, f"SCAN RESULTS - {result.username}")
        
        summary = [
            f"Target: {result.username}",
            f"Profiles Found: {result.profiles_found}/{result.total_platforms}",
            f"Timestamp: {result.timestamp}",
        ]
        
        self.menu.display_box("SUMMARY", summary)
    
    async def handle_batch_operations(self) -> None:
        """Handle batch scanning"""
        self.terminal.clear()
        self.banner.display("batch")
        
        self.menu.display_info("BATCH OPERATIONS - Multiple Target Intelligence")
        
        # Get targets
        targets_input = await self.menu.prompt("ENTER TARGETS (comma-separated) or 'back'")
        
        if not targets_input or targets_input.lower() in ['back', 'exit', '0']:
            return
        
        targets = [t.strip() for t in targets_input.split(',') if t.strip()]
        
        if not targets:
            self.menu.display_warning("No valid targets entered")
            await self.menu.prompt("PRESS ENTER TO CONTINUE")
            return
        
        if not self.scanner:
            self.menu.display_error("Scanner not available.")
            await self.menu.prompt("PRESS ENTER TO CONTINUE")
            return
        
        self.menu.display_info(f"Processing {len(targets)} targets...")
        
        try:
            with self.terminal.progress_bar(len(targets), "Batch Scanning...") as progress:
                task = progress.add_task("scan", total=len(targets))
                async with self.scanner as scanner_instance:
                    for target in targets:
                        result = await scanner_instance.scan_username(target)
                        
                        for platform_id, data in result.platforms.items():
                            self.db.save_result(
                                target=target,
                                platform=data.platform,
                                status=data.status,
                                url=data.url,
                                scan_type='BATCH_SCAN'
                            )
                        
                        self.session_scans += 1
                        progress.update(task, advance=1)
            
            self.menu.display_success(f"Batch scan completed: {len(targets)} targets processed")
        except Exception as e:
            logger.error(f"Batch scan error: {e}")
            self.menu.display_error(f"Batch scan failed: {e}")
        
        await self.menu.prompt("PRESS ENTER TO CONTINUE")
    
    async def handle_dashboard(self) -> None:
        """Display intelligence dashboard"""
        self.terminal.clear()
        self.banner.display("dashboard")
        
        self.menu.display_info("INTELLIGENCE DASHBOARD")
        
        # Calculate uptime
        uptime_seconds = int((datetime.now() - self.start_time).total_seconds())
        uptime_minutes = uptime_seconds // 60
        uptime_hours = uptime_minutes // 60
        uptime_str = f"{uptime_hours}h {uptime_minutes % 60}m"
        
        # Get statistics
        stats = self.db.get_statistics()
        
        # Display stats table
        headers = ["Metric", "Value", "Status"]
        rows = [
            ["System Uptime", uptime_str, "🟢"],
            ["Scans This Session", str(self.session_scans), "🟢"],
            ["Total Database Scans", str(stats.get('total_scans', 0)), "📊"],
            ["Profiles Found (DB)", str(stats.get('found_profiles', 0)), "✓"],
            ["Unique Targets (DB)", str(stats.get('unique_targets', 0)), "🎯"],
        ]
        
        self.menu.display_table(headers, rows, "SYSTEM STATISTICS")
        
        # Platform breakdown
        if stats.get('platforms'):
            platform_rows = []
            for platform, count in stats['platforms'].items():
                platform_rows.append([platform, str(count)])
            
            self.menu.display_table(["Platform", "Scans"], platform_rows, "PLATFORM BREAKDOWN")
        
        await self.menu.prompt("PRESS ENTER TO CONTINUE")
    
    async def handle_scan_history(self) -> None:
        """Display scan history"""
        self.terminal.clear()
        self.banner.display("history")
        
        self.menu.display_info("SCAN HISTORY")
        
        history = self.db.get_scan_history(50)
        
        if not history:
            self.menu.display_warning("No scan history available")
            await self.menu.prompt("PRESS ENTER TO CONTINUE")
            return
        
        headers = ["#", "Target", "Platform", "Status", "Date"]
        rows = []
        
        for i, record in enumerate(history[:20], 1):
            timestamp = datetime.fromisoformat(record['timestamp']).strftime('%Y-%m-%d %H:%M')
            rows.append([
                str(i),
                record['target'][:15],
                record['platform'][:12],
                record['status'],
                timestamp
            ])
        
        self.menu.display_table(headers, rows, f"RECENT SCANS (Total: {len(history)})")
        
        # Search option
        search = await self.menu.prompt("SEARCH BY TARGET (or 'back')")
        
        if search and search.lower() not in ['back', '0']:
            results = self.db.search_results(search)
            
            if results:
                search_rows = []
                for i, record in enumerate(results[:20], 1):
                    timestamp = datetime.fromisoformat(record['timestamp']).strftime('%Y-%m-%d %H:%M')
                    search_rows.append([
                        str(i),
                        record['target'],
                        record['platform'],
                        record['status'],
                        timestamp
                    ])
                
                self.menu.display_table(headers, search_rows, f"SEARCH RESULTS - {search}")
        
        await self.menu.prompt("PRESS ENTER TO CONTINUE")
    
    async def handle_export(self) -> None:
        """Handle data export"""
        self.terminal.clear()
        self.banner.display("main")
        
        self.menu.display_info("DATA EXPORT")
        
        export_options = {
            "1": "Export all scan history",
            "2": "Export statistics report",
            "3": "Export database backup",
            "0": "Return to main menu"
        }
        
        for key, option in export_options.items():
            print(f"  [{key}] {option}")
        
        choice = await self.menu.prompt("SELECT EXPORT TYPE")
        
        if choice == "1":
            await self._export_history()
        elif choice == "2":
            await self._export_statistics()
        elif choice == "3":
            await self._export_backup()
        
        if choice in ["1", "2", "3"]:
            await self.menu.prompt("PRESS ENTER TO CONTINUE")
    
    async def _export_history(self) -> None:
        """Export scan history to JSON"""
        try:
            history = self.db.get_scan_history(999)
            export_file = BASE_DIR / 'exports' / f'scan_history_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
            export_file.parent.mkdir(exist_ok=True)
            
            with open(export_file, 'w') as f:
                json.dump(history, f, indent=2)
            
            self.menu.display_success(f"History exported to {export_file.name}")
            logger.info(f"History exported to {export_file}")
        except Exception as e:
            logger.error(f"Export error: {e}")
            self.menu.display_error(f"Export failed: {e}")
    
    async def _export_statistics(self) -> None:
        """Export statistics report"""
        try:
            stats = self.db.get_statistics()
            report_file = BASE_DIR / 'reports' / f'report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
            report_file.parent.mkdir(exist_ok=True)
            
            report = {
                'generated': datetime.now().isoformat(),
                'statistics': stats,
                'session_scans': self.session_scans
            }
            
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2)
            
            self.menu.display_success(f"Report exported to {report_file.name}")
            logger.info(f"Report exported to {report_file}")
        except Exception as e:
            logger.error(f"Report generation error: {e}")
            self.menu.display_error(f"Report generation failed: {e}")
    
    async def _export_backup(self) -> None:
        """Create database backup"""
        try:
            import shutil
            backup_file = BASE_DIR / 'backups' / f'backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'
            backup_file.parent.mkdir(exist_ok=True)
            
            shutil.copy(self.db.db_path, backup_file)
            
            self.menu.display_success(f"Database backed up to {backup_file.name}")
            logger.info(f"Database backed up to {backup_file}")
        except Exception as e:
            logger.error(f"Backup error: {e}")
            self.menu.display_error(f"Backup failed: {e}")
    
    async def handle_configuration(self) -> None:
        """Handle configuration options"""
        self.terminal.clear()
        self.banner.display("main")
        
        self.menu.display_info("CONFIGURATION")
        
        config_menu = {
            "1": "Color Scheme",
            "2": "Theme",
            "3": "Animation Settings",
            "4": "Scanner Timeout",
            "0": "Return to main menu"
        }
        
        for key, option in config_menu.items():
            print(f"  [{key}] {option}")
        
        choice = await self.menu.prompt("SELECT OPTION")
        
        if choice == "1":
            await self._select_color_scheme()
        elif choice == "2":
            await self._select_theme()
        elif choice == "3":
            self.menu.display_info("Animation: " + ("Enabled" if self.banner.animations_enabled else "Disabled"))
            self.banner.set_animation(not self.banner.animations_enabled)
        
        await self.menu.prompt("PRESS ENTER TO CONTINUE")
    
    async def _select_color_scheme(self) -> None:
        """Select color scheme"""
        schemes = {
            "1": ("Green Plasma", BannerColorScheme.GREEN_PLASMA, MenuColorScheme.GREEN_PLASMA),
            "2": ("Amber Mono", BannerColorScheme.AMBER_MONO, MenuColorScheme.AMBER_MONO),
            "3": ("Cool Blue", BannerColorScheme.COOL_BLUE, MenuColorScheme.COOL_BLUE),
            "4": ("Monochrome", BannerColorScheme.MONOCHROME, MenuColorScheme.MONOCHROME),
        }
        
        for key, (name, _, _) in schemes.items():
            print(f"  [{key}] {name}")
        
        choice = await self.menu.prompt("SELECT SCHEME")
        
        if choice in schemes:
            name, banner_scheme, menu_scheme = schemes[choice]
            self.banner.change_scheme(banner_scheme)
            self.menu.change_scheme(menu_scheme)
            self.menu.display_success(f"Switched to {name}")
            
    async def _select_theme(self) -> None:
        """Select banner theme"""
        themes = {
            "1": ("Modern", BannerTheme.MODERN),
            "2": ("Vintage", BannerTheme.VINTAGE),
        }
        
        for key, (name, _) in themes.items():
            print(f"  [{key}] {name}")
        
        choice = await self.menu.prompt("SELECT THEME")
        
        if choice in themes:
            name, theme = themes[choice]
            self.banner.change_theme(theme)
            self.menu.display_success(f"Switched to {name} theme")
    
    async def handle_system_validation(self) -> None:
        """System validation and health check"""
        self.terminal.clear()
        self.banner.display("main")
        
        self.menu.display_info("SYSTEM VALIDATION")
        
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
        
        self.menu.display_table(["Component", "Status"], status_rows, "SYSTEM HEALTH")
        
        await self.menu.prompt("PRESS ENTER TO CONTINUE")
    
    async def handle_documentation(self) -> None:
        """Display documentation"""
        self.terminal.clear()
        self.banner.display("main")
        
        self.menu.display_info("DOCUMENTATION")
        
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
        
        self.menu.display_box("HELP & DOCUMENTATION", docs)
        
        await self.menu.prompt("PRESS ENTER TO CONTINUE")
    
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
                    await self.handle_single_scan()
                elif choice == "2":
                    await self.handle_batch_operations()
                elif choice == "3":
                    await self.handle_dashboard()
                elif choice == "4":
                    await self.handle_scan_history()
                elif choice == "5":
                    await self.handle_export()
                elif choice == "6":
                    await self.handle_configuration()
                elif choice == "7":
                    await self.handle_system_validation()
                elif choice == "8":
                    await self.handle_documentation()
                elif choice == "0":
                    self.running = False
                else:
                    self.menu.display_warning("Invalid selection")
                    await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"Command execution error: {e}")
                self.menu.display_error(f"Error: {e}")
                await asyncio.sleep(2)
        
        # Shutdown sequence
        self.terminal.clear()
        self.terminal.shutdown_sequence()
        logger.info(f"Session ended. Total scans: {self.session_scans}")


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
    except Exception as e:
        print(f"\n\033[91m[FATAL ERROR] {e}\033[0m")
        logger.critical(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)

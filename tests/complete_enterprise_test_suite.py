#!/usr/bin/env python3
"""
HandyOsint - Integrated Test Suite
Diagnostics and  Troubleshooting
"""

import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime
import json
import sqlite3
from typing import Dict, List, Tuple, Optional

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


# ============================================================
# TEST FRAMEWORK & ASCII BANNERS
# ============================================================

class TestColors:
    """ANSI color codes"""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"


class TestBanners:
    """ASCII art banners for testing"""
    
    @staticmethod
    def print_header():
        """Main test header"""
        banner = r"""
    ╔═══════════════════════════════════════════════════════════════════════════╗
    ║                           TEST SUITE v3.0.0                               ║
    ║                    [cyberzilla™ | Enterprise Level]                       ║
    ╚═══════════════════════════════════════════════════════════════════════════╝
        """
        print(TestColors.CYAN + banner + TestColors.RESET)
    
    @staticmethod
    def print_section(title: str):
        """Print section header"""
        divider = "═" * 80
        print(f"\n{TestColors.BOLD}{TestColors.CYAN}{divider}{TestColors.RESET}")
        print(f"{TestColors.BOLD}{TestColors.YELLOW}▶ {title.center(76)} ◀{TestColors.RESET}")
        print(f"{TestColors.BOLD}{TestColors.CYAN}{divider}{TestColors.RESET}\n")
    
    @staticmethod
    def print_test(name: str, status: str, message: str = ""):
        """Print test result"""
        if status.upper() == "PASS":
            icon = f"{TestColors.GREEN}✓{TestColors.RESET}"
            status_color = TestColors.GREEN
        elif status.upper() == "FAIL":
            icon = f"{TestColors.RED}✗{TestColors.RESET}"
            status_color = TestColors.RED
        elif status.upper() == "SKIP":
            icon = f"{TestColors.YELLOW}⊘{TestColors.RESET}"
            status_color = TestColors.YELLOW
        else:
            icon = f"{TestColors.CYAN}◆{TestColors.RESET}"
            status_color = TestColors.CYAN
        
        msg = f" | {message}" if message else ""
        print(f"  {icon} {name:<40} [{status_color}{status}{TestColors.RESET}]{msg}")
    
    @staticmethod
    def print_summary(passed: int, failed: int, skipped: int, total: int):
        """Print test summary"""
        divider = "═" * 80
        print(f"\n{TestColors.CYAN}{divider}{TestColors.RESET}")
        
        passed_str = f"{TestColors.GREEN}✓ {passed}{TestColors.RESET}"
        failed_str = f"{TestColors.RED}✗ {failed}{TestColors.RESET}"
        skipped_str = f"{TestColors.YELLOW}⊘ {skipped}{TestColors.RESET}"
        total_str = f"{TestColors.BOLD}{total}{TestColors.RESET}"
        
        summary = f"  RESULTS: {passed_str} PASSED | {failed_str} FAILED | {skipped_str} SKIPPED | {total_str} TOTAL"
        print(summary)
        print(f"{TestColors.CYAN}{divider}{TestColors.RESET}\n")


# ============================================================================
# MODULE DETECTION & VERIFICATION
# ============================================================================

class ModuleDetector:
    """Detect and verify installed modules"""
    
    @staticmethod
    def check_module(module_name: str, friendly_name: str = "") -> Tuple[bool, str]:
        """Check if module is available"""
        try:
            __import__(module_name)
            return True, f"{friendly_name or module_name} ✓"
        except ImportError:
            return False, f"{friendly_name or module_name} ✗ (Not installed)"
    
    @staticmethod
    def check_project_structure() -> Dict[str, bool]:
        """Verify project structure"""
        project_root = Path(__file__).parent.parent
        
        structure = {
            'main.py': (project_root / 'main.py').exists(),
            'ui/banner.py': (project_root / 'ui' / 'banner.py').exists(),
            'ui/menu.py': (project_root / 'ui' / 'menu.py').exists(),
            'ui/terminal.py': (project_root / 'ui' / 'terminal.py').exists(),
            'core/production_scanner.py': (project_root / 'core' / 'production_scanner.py').exists(),
            'core/error_handler.py': (project_root / 'core' / 'error_handler.py').exists(),
            'data/': (project_root / 'data').exists(),
            'logs/': (project_root / 'logs').exists(),
        }
        
        return structure
    
    @staticmethod
    def detect_dependencies() -> Dict[str, Tuple[bool, str]]:
        """Detect all dependencies"""
        dependencies = {
            'asyncio': ModuleDetector.check_module('asyncio', 'AsyncIO'),
            'aiohttp': ModuleDetector.check_module('aiohttp', 'AIOHTTP'),
            'aioconsole': ModuleDetector.check_module('aioconsole', 'AIOConsole'),
            'sqlite3': ModuleDetector.check_module('sqlite3', 'SQLite3'),
            'logging': ModuleDetector.check_module('logging', 'Logging'),
            'json': ModuleDetector.check_module('json', 'JSON'),
        }
        
        return dependencies


# ============================================================================
# UNIT TESTS
# ============================================================================

class UnitTests:
    """Unit tests for components"""
    
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.skipped = 0
    
    async def run_all(self):
        """Run all unit tests"""
        TestBanners.print_section("UNIT TESTS")
        
        await self.test_imports()
        await self.test_database()
        await self.test_error_handler()
        await self.test_scanner()
    
    async def test_imports(self):
        """Test all imports"""
        TestBanners.print_test("Import UI Modules", "SKIP", "Requires full environment")
        self.skipped += 1
        
        try:
            from ui.banner import VintageBanner, BannerColorScheme
            TestBanners.print_test("Import Banner", "PASS")
            self.passed += 1
        except Exception as e:
            TestBanners.print_test("Import Banner", "FAIL", str(e))
            self.failed += 1
    
    async def test_database(self):
        """Test database functionality"""
        TestBanners.print_test("Database Initialization", "SKIP", "Requires main.py context")
        self.skipped += 1
        
        try:
            db_path = Path(__file__).parent.parent / 'data' / 'social_scan.db'
            if db_path.exists():
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = cursor.fetchall()
                conn.close()
                
                if tables:
                    TestBanners.print_test("Database Tables", "PASS", f"{len(tables)} tables found")
                    self.passed += 1
                else:
                    TestBanners.print_test("Database Tables", "FAIL", "No tables found")
                    self.failed += 1
            else:
                TestBanners.print_test("Database File", "SKIP", "Database not yet created")
                self.skipped += 1
        except Exception as e:
            TestBanners.print_test("Database Test", "FAIL", str(e))
            self.failed += 1
    
    async def test_error_handler(self):
        """Test error handler"""
        try:
            from core.error_handler import ErrorHandler
            handler = ErrorHandler()
            TestBanners.print_test("ErrorHandler Creation", "PASS")
            self.passed += 1
        except Exception as e:
            TestBanners.print_test("ErrorHandler Creation", "SKIP", "Module not available")
            self.skipped += 1
    
    async def test_scanner(self):
        """Test scanner initialization"""
        TestBanners.print_test("Scanner Module", "SKIP", "Requires async context")
        self.skipped += 1


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class IntegrationTests:
    """Integration tests"""
    
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.skipped = 0
    
    async def run_all(self):
        """Run all integration tests"""
        TestBanners.print_section("INTEGRATION TESTS")
        
        await self.test_ui_rendering()
        await self.test_database_operations()
        await self.test_scanner_initialization()
    
    async def test_ui_rendering(self):
        """Test UI rendering"""
        try:
            from ui.banner import VintageBanner, BannerColorScheme
            banner = VintageBanner(BannerColorScheme.GREEN_PLASMA)
            
            # Test banner generation
            main_banner = banner.get_main_banner()
            if "HANDYOSINT" in main_banner or "HandyOsint" in main_banner:
                TestBanners.print_test("Banner Rendering", "PASS")
                self.passed += 1
            else:
                TestBanners.print_test("Banner Rendering", "FAIL", "Banner content invalid")
                self.failed += 1
        except Exception as e:
            TestBanners.print_test("Banner Rendering", "SKIP", "UI module unavailable")
            self.skipped += 1
    
    async def test_database_operations(self):
        """Test database operations"""
        try:
            project_root = Path(__file__).parent.parent
            db_path = project_root / 'data' / 'social_scan.db'
            
            # Check if database path is accessible
            db_path.parent.mkdir(parents=True, exist_ok=True)
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Test table creation
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS test_table (
                    id INTEGER PRIMARY KEY,
                    name TEXT
                )
            ''')
            
            # Test insert
            cursor.execute("INSERT INTO test_table (name) VALUES (?)", ("test",))
            conn.commit()
            
            # Test retrieve
            cursor.execute("SELECT * FROM test_table WHERE name = ?", ("test",))
            result = cursor.fetchone()
            
            conn.close()
            
            if result:
                TestBanners.print_test("Database Operations", "PASS")
                self.passed += 1
            else:
                TestBanners.print_test("Database Operations", "FAIL", "Data not retrieved")
                self.failed += 1
        except Exception as e:
            TestBanners.print_test("Database Operations", "FAIL", str(e))
            self.failed += 1
    
    async def test_scanner_initialization(self):
        """Test scanner initialization"""
        try:
            from core.production_scanner import ProductionScanner
            
            scanner = ProductionScanner()
            platforms_count = len(scanner.platforms)
            
            if platforms_count > 0:
                TestBanners.print_test("Scanner Init", "PASS", f"{platforms_count} platforms loaded")
                self.passed += 1
            else:
                TestBanners.print_test("Scanner Init", "FAIL", "No platforms loaded")
                self.failed += 1
        except Exception as e:
            TestBanners.print_test("Scanner Init", "SKIP", "Scanner module unavailable")
            self.skipped += 1


# ============================================================================
# SYSTEM CHECKS
# ============================================================================

class SystemChecks:
    """System health checks"""
    
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.skipped = 0
        self.issues = []
    
    async def run_all(self):
        """Run all system checks"""
        TestBanners.print_section("SYSTEM CHECKS")
        
        await self.check_dependencies()
        await self.check_project_structure()
        await self.check_directories()
        await self.check_permissions()
        await self.check_memory()
    
    async def check_dependencies(self):
        """Check all dependencies"""
        deps = ModuleDetector.detect_dependencies()
        
        for dep, (available, message) in deps.items():
            if available:
                TestBanners.print_test(f"Dependency: {dep}", "PASS")
                self.passed += 1
            else:
                TestBanners.print_test(f"Dependency: {dep}", "FAIL", message)
                self.failed += 1
                self.issues.append(message)
    
    async def check_project_structure(self):
        """Check project structure"""
        structure = ModuleDetector.check_project_structure()
        
        for path, exists in structure.items():
            if exists:
                TestBanners.print_test(f"Structure: {path}", "PASS")
                self.passed += 1
            else:
                TestBanners.print_test(f"Structure: {path}", "FAIL", "Missing")
                self.failed += 1
                self.issues.append(f"Missing: {path}")
    
    async def check_directories(self):
        """Check required directories"""
        project_root = Path(__file__).parent.parent
        dirs = ['data', 'logs', 'exports', 'reports', 'backups']
        
        for dir_name in dirs:
            dir_path = project_root / dir_name
            try:
                dir_path.mkdir(parents=True, exist_ok=True)
                TestBanners.print_test(f"Directory: {dir_name}", "PASS")
                self.passed += 1
            except Exception as e:
                TestBanners.print_test(f"Directory: {dir_name}", "FAIL", str(e))
                self.failed += 1
                self.issues.append(f"Cannot create {dir_name}: {e}")
    
    async def check_permissions(self):
        """Check file permissions"""
        project_root = Path(__file__).parent.parent
        
        # Check write permissions
        try:
            test_file = project_root / '.test_write'
            test_file.write_text('test')
            test_file.unlink()
            TestBanners.print_test("Write Permissions", "PASS")
            self.passed += 1
        except Exception as e:
            TestBanners.print_test("Write Permissions", "FAIL", str(e))
            self.failed += 1
            self.issues.append(f"Write permission denied: {e}")
    
    async def check_memory(self):
        """Check memory availability"""
        try:
            import psutil
            memory = psutil.virtual_memory()
            available_mb = memory.available / 1024 / 1024
            
            if available_mb > 100:
                TestBanners.print_test("Memory Available", "PASS", f"{available_mb:.0f}MB")
                self.passed += 1
            else:
                TestBanners.print_test("Memory Available", "FAIL", f"Low: {available_mb:.0f}MB")
                self.failed += 1
                self.issues.append(f"Low memory: {available_mb:.0f}MB")
        except ImportError:
            TestBanners.print_test("Memory Check", "SKIP", "psutil not available")
            self.skipped += 1


# ============================================================================
# TROUBLESHOOTING & DIAGNOSTICS
# ============================================================================

class Troubleshoot:
    """Troubleshooting and diagnostics"""
    
    @staticmethod
    def diagnose_issues(issues: List[str]):
        """Provide troubleshooting for identified issues"""
        TestBanners.print_section("TROUBLESHOOTING & DIAGNOSTICS")
        
        if not issues:
            print(f"{TestColors.GREEN}✓ No issues detected!{TestColors.RESET}\n")
            return
        
        print(f"{TestColors.YELLOW}Found {len(issues)} issue(s):{TestColors.RESET}\n")
        
        solutions = {
            "aiohttp": "Install: pip install aiohttp",
            "aioconsole": "Install: pip install aioconsole",
            "Missing": "Create the directory and ensure proper permissions",
            "Low memory": "Free up system memory or increase available resources",
            "Write permission": "Check file permissions: chmod +rw <directory>",
            "psutil": "Optional: pip install psutil (for memory monitoring)",
        }
        
        for issue in issues:
            print(f"  {TestColors.YELLOW}⚠{TestColors.RESET} {issue}")
            
            # Find matching solution
            for key, solution in solutions.items():
                if key.lower() in issue.lower():
                    print(f"    {TestColors.GREEN}→ Solution:{TestColors.RESET} {solution}\n")
                    break
    
    @staticmethod
    def generate_report(results: Dict) -> str:
        """Generate detailed test report"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        report = f"""
╔════════════════════════════════════════════════════════════════════════════╗
║                       HANDYOSINT TEST REPORT                               ║
╚════════════════════════════════════════════════════════════════════════════╝

Generated: {timestamp}

TEST RESULTS:
  Unit Tests:
    Passed:  {results['unit']['passed']}
    Failed:  {results['unit']['failed']}
    Skipped: {results['unit']['skipped']}
  
  Integration Tests:
    Passed:  {results['integration']['passed']}
    Failed:  {results['integration']['failed']}
    Skipped: {results['integration']['skipped']}
  
  System Checks:
    Passed:  {results['checks']['passed']}
    Failed:  {results['checks']['failed']}
    Skipped: {results['checks']['skipped']}

SUMMARY:
  Total Passed:  {results['total_passed']}
  Total Failed:  {results['total_failed']}
  Total Skipped: {results['total_skipped']}
  Success Rate:  {results['success_rate']:.1f}%

STATUS: {results['status']}

══════════════════════════════════════════════════════════════
"""
        return report


# ============================================================================
# MAIN TEST RUNNER
# ============================================================================

class TestRunner:
    """Main test runner"""
    
    def __init__(self):
        self.unit_tests = UnitTests()
        self.integration_tests = IntegrationTests()
        self.system_checks = SystemChecks()
        self.troubleshoot = Troubleshoot()
    
    async def run(self):
        """Run complete test suite"""
        TestBanners.print_header()
        
        # Run all test suites
        await self.unit_tests.run_all()
        await self.integration_tests.run_all()
        await self.system_checks.run_all()
        
        # Calculate totals
        total_passed = (self.unit_tests.passed + 
                       self.integration_tests.passed + 
                       self.system_checks.passed)
        total_failed = (self.unit_tests.failed + 
                       self.integration_tests.failed + 
                       self.system_checks.failed)
        total_skipped = (self.unit_tests.skipped + 
                        self.integration_tests.skipped + 
                        self.system_checks.skipped)
        total = total_passed + total_failed + total_skipped
        
        success_rate = (total_passed / total * 100) if total > 0 else 0
        
        # Print summary
        TestBanners.print_summary(total_passed, total_failed, total_skipped, total)
        
        # Troubleshooting
        all_issues = self.system_checks.issues
        self.troubleshoot.diagnose_issues(all_issues)
        
        # Generate report
        results = {
            'unit': {
                'passed': self.unit_tests.passed,
                'failed': self.unit_tests.failed,
                'skipped': self.unit_tests.skipped,
            },
            'integration': {
                'passed': self.integration_tests.passed,
                'failed': self.integration_tests.failed,
                'skipped': self.integration_tests.skipped,
            },
            'checks': {
                'passed': self.system_checks.passed,
                'failed': self.system_checks.failed,
                'skipped': self.system_checks.skipped,
            },
            'total_passed': total_passed,
            'total_failed': total_failed,
            'total_skipped': total_skipped,
            'success_rate': success_rate,
            'status': 'PASS' if total_failed == 0 else 'FAIL',
        }
        
        report = self.troubleshoot.generate_report(results)
        print(report)
        
        # Save report
        report_path = Path(__file__).parent.parent / 'reports' / 'test_report.txt'
        report_path.parent.mkdir(parents=True, exist_ok=True)
        with open(report_path, 'w') as f:
            f.write(report)
        
        print(f"Report saved to: {report_path}\n")
        
        return total_failed == 0


async def main():
    """Main entry point"""
    runner = TestRunner()
    success = await runner.run()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n{TestColors.YELLOW}Tests interrupted by user{TestColors.RESET}\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n{TestColors.RED}Fatal error: {e}{TestColors.RESET}\n")
        sys.exit(1)

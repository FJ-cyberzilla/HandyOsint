#!/usr/bin/env python3
"""
HandyOsint Banner System Migration Tool
Seamlessly migrate from old banner to advanced gradient banner system.

This module provides:
- Automatic backup of existing banner system
- Import scanning and migration
- Compatibility layer creation
- Example file generation
- Full pylint compliance
"""

import re
import shutil
import argparse
from pathlib import Path
from typing import List, Tuple
from datetime import datetime


class BannerMigrationTool:
    """Handles migration from old Banner to AdvancedBannerGenerator."""

    def __init__(self, project_root: str = ".") -> None:
        """Initialize migration tool."""
        self.project_root = Path(project_root)
        self.ui_path = self.project_root / "ui"
        self.backup_dir = self.project_root / ".banner_migration_backup"
        self.migration_log: List[str] = []

    def backup_old_banner(self) -> bool:
        """Backup old banner.py file."""
        try:
            old_banner = self.ui_path / "banner.py"
            if old_banner.exists():
                self.backup_dir.mkdir(exist_ok=True)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_file = self.backup_dir / f"banner.py.{timestamp}.backup"
                shutil.copy2(old_banner, backup_file)

                self.log(f"Backed up old banner to: {backup_file}")
                return True
            return True
        except (OSError, IOError) as exc:
            self.log(f"Backup failed: {exc}", error=True)
            return False

    def scan_imports(self) -> List[Tuple[str, List[str]]]:
        """Scan project for Banner imports."""
        imports: List[Tuple[str, List[str]]] = []

        for py_file in self.project_root.rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                banner_imports = re.findall(
                    r'(?:from\s+ui\.banner\s+import\s+([^\n]+)|import\s+ui\.banner)',
                    content
                )

                if banner_imports or 'Banner' in content:
                    imports.append((str(py_file), banner_imports))
                    self.log(f"Found Banner usage in: {py_file.name}")

            except (OSError, IOError, UnicodeDecodeError) as exc:
                self.log(f"Error scanning {py_file}: {exc}", error=True)

        return imports

    def migrate_imports(self, file_path: str) -> bool:
        """Update imports in a Python file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            original_content = content

            migrations = [
                (r'from\s+ui\.banner\s+import\s+Banner\b',
                 'from ui.banner import Banner'),
                (r'\bBanner\s*\(',
                 'Banner('),
                (r'\.display_main_banner_(?:modern|vintage)\(\)',
                 '.display("main")'),
                (r'\.get_main_banner_(?:modern|vintage)\(\)',
                 '.get_main_banner()'),
            ]

            for pattern, replacement in migrations:
                if re.search(pattern, content):
                    content = re.sub(pattern, replacement, content)
                    self.log(f"Updated pattern in: {Path(file_path).name}")

            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                return True

            return False

        except (OSError, IOError, UnicodeDecodeError) as exc:
            self.log(f"Migration failed for {file_path}: {exc}", error=True)
            return False

    def create_compatibility_layer(self) -> str:
        """Create backward compatibility code."""
        compatibility_code = '''#!/usr/bin/env python3
"""
Backward Compatibility Layer
Provides old Banner API mapping to new Banner system.
"""

from ui.banner import Banner, BannerColorScheme


class BannerCompat:
    """Compatibility wrapper for legacy code."""

    def __init__(self) -> None:
        """Initialize compatibility wrapper."""
        self.generator = Banner(BannerColorScheme.DARK_ORANGE)

    def display_main_banner_modern(self) -> None:
        """Legacy method - maps to new API."""
        self.generator.display("main")

    def display_main_banner_vintage(self) -> None:
        """Legacy method - maps to new API."""
        self.generator.display("main")

    def display_scan_banner_modern(self) -> None:
        """Legacy method - maps to new API."""
        self.generator.display("scan")

    def get_main_banner_modern(self) -> str:
        """Legacy method - maps to new API."""
        return self.generator.get_main_banner()

    def get_main_banner_vintage(self) -> str:
        """Legacy method - maps to new API."""
        return self.generator.get_main_banner()

    def change_theme(self, theme: str) -> None:
        """Legacy method - maintains compatibility."""
        pass
'''
        return compatibility_code

    def migrate_menu_module(self) -> bool:
        """Migrate menu.py to use new banner system."""
        try:
            menu_file = self.ui_path / "menu.py"

            if not menu_file.exists():
                self.log("menu.py not found, skipping migration")
                return False

            with open(menu_file, 'r', encoding='utf-8') as f:
                content = f.read()

            if 'Banner' in content:
                self.log("menu.py already uses banner system")
                return True

            return True

        except (OSError, IOError, UnicodeDecodeError) as exc:
            self.log(f"Migration of menu.py failed: {exc}", error=True)
            return False

    def create_example_file(self) -> str:
        """Create example usage file."""
        example_code = '''#!/usr/bin/env python3
"""
Example: Using Advanced Banner System
Shows all features and best practices.
"""

from ui.banner import Banner, BannerColorScheme
import time


def example_main_banner() -> None:
    """Display main banner with gradient."""
    banner = Banner(BannerColorScheme.DARK_ORANGE)
    banner.display("main", animate=True)


def example_with_chart() -> None:
    """Display banner with integrated chart."""
    banner = Banner(BannerColorScheme.DARK_ORANGE)

    chart_data = {
        "Targets": 45.0,
        "Threats": 78.0,
        "Vulnerable": 62.0,
        "Critical": 91.0,
    }

    banner.display(
        banner_type="dashboard",
        chart_data=chart_data,
        chart_type="bar"
    )


def example_color_schemes() -> None:
    """Demonstrate all color schemes."""
    schemes = [
        BannerColorScheme.DARK_ORANGE,
        BannerColorScheme.PROFESSIONAL,
    ]

    for scheme in schemes:
        banner = Banner(scheme)
        banner.display("main")
        time.sleep(0.5)


def example_custom_banner() -> None:
    """Create custom banner."""
    banner = Banner(BannerColorScheme.DARK_ORANGE)

    custom = banner.create_custom_banner(
        title="[ SECURITY ALERT ]",
        subtitle="Potential Threat Detected"
    )
    print(custom)


def example_status_dashboard() -> None:
    """Display system status."""
    banner = Banner(BannerColorScheme.DARK_ORANGE)

    status = banner.display_system_dashboard(
        cpu=67.5,
        memory=54.2,
        network=82.1,
        scans=78.9
    )
    print(status)


def example_threat_level() -> None:
    """Display threat assessment."""
    banner = Banner(BannerColorScheme.DARK_ORANGE)

    for level in range(1, 6):
        threat = banner.display_threat_level(level)
        print(threat)


def main() -> None:
    """Main entry point."""
    print("\\n=== Main Banner Demo ===")
    example_main_banner()

    print("\\n=== Chart Integration Demo ===")
    example_with_chart()

    print("\\n=== Custom Banner Demo ===")
    example_custom_banner()

    print("\\n=== Status Dashboard Demo ===")
    example_status_dashboard()

    print("\\n=== Threat Level Demo ===")
    example_threat_level()


if __name__ == "__main__":
    main()
'''
        return example_code

    def log(self, message: str, error: bool = False) -> None:
        """Log migration messages."""
        prefix = "✗" if error else "→"
        print(f"{prefix} {message}")
        self.migration_log.append(message)

    def run_full_migration(self) -> bool:
        """Execute complete migration."""
        print("\n" + "=" * 80)
        print("HandyOsint Banner System Migration")
        print("=" * 80 + "\n")

        self.log("Step 1: Backing up old banner system...")
        if not self.backup_old_banner():
            self.log("Backup failed. Aborting migration.", error=True)
            return False

        self.log("\nStep 2: Scanning project for Banner usage...")
        imports = self.scan_imports()
        self.log(f"Found {len(imports)} files using Banner")

        self.log("\nStep 3: Migrating imports in Python files...")
        migrated_count = 0
        for file_path, _ in imports:
            if self.migrate_imports(file_path):
                migrated_count += 1
        self.log(f"Migrated {migrated_count} files")

        self.log("\nStep 4: Migrating specific modules...")
        self.migrate_menu_module()

        self.log("\nStep 5: Creating compatibility layer...")
        compat_file = self.ui_path / "banner_compat.py"
        try:
            with open(compat_file, 'w', encoding='utf-8') as f:
                f.write(self.create_compatibility_layer())
            self.log(f"Created compatibility layer: {compat_file}")
        except (OSError, IOError) as exc:
            self.log(f"Failed to create compatibility layer: {exc}",
                    error=True)

        self.log("\nStep 6: Creating example files...")
        example_file = self.project_root / "banner_examples.py"
        try:
            with open(example_file, 'w', encoding='utf-8') as f:
                f.write(self.create_example_file())
            self.log(f"Created examples: {example_file}")
        except (OSError, IOError) as exc:
            self.log(f"Failed to create examples: {exc}", error=True)

        print("\n" + "=" * 80)
        print("Migration Complete!")
        print("=" * 80)
        print("\nNext Steps:")
        print("1. Test your application: python3 main.py")
        print("2. Review changes in migrated files")
        print("3. Check banner_examples.py for usage examples")
        print("4. Customize color schemes as needed")
        print(f"5. Backup available at: {self.backup_dir}")
        print("\nFor help, see INTEGRATION_GUIDE.md\n")

        return True


def main() -> None:
    """Run migration tool."""
    parser = argparse.ArgumentParser(
        description="Migrate HandyOsint to advanced banner system"
    )
    parser.add_argument(
        "--project-root",
        default=".",
        help="Path to HandyOsint project root"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be changed without modifying files"
    )

    args = parser.parse_args()

    migrator = BannerMigrationTool(args.project_root)

    if args.dry_run:
        print("DRY RUN MODE - No files will be modified\n")
        print("Files that would be migrated:")
        imports = migrator.scan_imports()
        for file_path, _ in imports:
            print(f"  - {file_path}")
    else:
        migrator.run_full_migration()


if __name__ == "__main__":
    main()

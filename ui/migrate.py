#!/usr/bin/env python3
"""
HandyOsint Banner System Migration Tool
Seamlessly migrate from old banner to advanced gradient banner system
"""

import os
import re
import shutil
from pathlib import Path
from typing import List, Tuple
from datetime import datetime


class BannerMigrationTool:
    """Handles migration from old Banner to AdvancedBannerGenerator"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.ui_path = self.project_root / "ui"
        self.backup_dir = self.project_root / ".banner_migration_backup"
        self.migration_log = []
    
    def backup_old_banner(self) -> bool:
        """Backup old banner.py"""
        try:
            old_banner = self.ui_path / "banner.py"
            if old_banner.exists():
                self.backup_dir.mkdir(exist_ok=True)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_file = self.backup_dir / f"banner.py.{timestamp}.backup"
                shutil.copy2(old_banner, backup_file)
                
                self.log(f"✓ Backed up old banner to: {backup_file}")
                return True
        except Exception as e:
            self.log(f"✗ Backup failed: {e}", error=True)
            return False
    
    def scan_imports(self) -> List[Tuple[str, List[str]]]:
        """Scan project for Banner imports"""
        imports = []
        
        for py_file in self.project_root.rglob("*.py"):
            try:
                with open(py_file, 'r') as f:
                    content = f.read()
                
                # Find Banner class imports
                banner_imports = re.findall(
                    r'(?:from\s+ui\.banner\s+import\s+([^\n]+)|import\s+ui\.banner)',
                    content
                )
                
                if banner_imports or 'Banner' in content:
                    imports.append((str(py_file), banner_imports))
                    self.log(f"Found Banner usage in: {py_file.name}")
            
            except Exception as e:
                self.log(f"Error scanning {py_file}: {e}", error=True)
        
        return imports
    
    def migrate_imports(self, file_path: str) -> bool:
        """Update imports in a Python file"""
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            original_content = content
            
            # Update old Banner imports to new ones
            migrations = [
                # Old: from ui.banner import Banner
                # New: from ui.banner import AdvancedBannerGenerator
                (r'from\s+ui\.banner\s+import\s+Banner\b',
                 'from ui.banner import AdvancedBannerGenerator, ColorSchemePreset'),
                
                # Old: Banner()
                # New: AdvancedBannerGenerator()
                (r'\bBanner\s*\(',
                 'AdvancedBannerGenerator('),
                
                # Old: banner.display_main_banner_modern()
                # New: banner.display("main")
                (r'\.display_main_banner_(?:modern|vintage)\(\)',
                 '.display("main")'),
                
                # Old: banner.get_main_banner_modern()
                # New: banner.get_main_banner()
                (r'\.get_main_banner_(?:modern|vintage)\(\)',
                 '.get_main_banner()'),
            ]
            
            for pattern, replacement in migrations:
                if re.search(pattern, content):
                    content = re.sub(pattern, replacement, content)
                    self.log(f"Updated import pattern in: {Path(file_path).name}")
            
            if content != original_content:
                with open(file_path, 'w') as f:
                    f.write(content)
                return True
            
            return False
        
        except Exception as e:
            self.log(f"Migration failed for {file_path}: {e}", error=True)
            return False
    
    def create_compatibility_layer(self) -> str:
        """Create backward compatibility code"""
        compatibility_code = '''"""
Backward Compatibility Layer
Provides old Banner API mapping to new AdvancedBannerGenerator
"""

from ui.banner import AdvancedBannerGenerator, ColorSchemePreset

# Legacy API support
Banner = AdvancedBannerGenerator

class BannerCompat:
    """Compatibility wrapper for old code"""
    
    def __init__(self):
        self.generator = AdvancedBannerGenerator(ColorSchemePreset.HEAT_WAVE)
    
    def display_main_banner_modern(self):
        """Legacy method - maps to new API"""
        return self.generator.display("main")
    
    def display_main_banner_vintage(self):
        """Legacy method - maps to new API"""
        return self.generator.display("main")
    
    def display_scan_banner_modern(self):
        """Legacy method - maps to new API"""
        return self.generator.display("scan")
    
    def get_main_banner_modern(self):
        """Legacy method - maps to new API"""
        return self.generator.get_main_banner()
    
    def get_main_banner_vintage(self):
        """Legacy method - maps to new API"""
        return self.generator.get_main_banner()
    
    def change_theme(self, theme):
        """Legacy method - maintains compatibility"""
        pass

# For full backward compatibility, you can use:
# banner = BannerCompat()
# banner.display_main_banner_modern()
'''
        return compatibility_code
    
    def migrate_menu_module(self) -> bool:
        """Migrate menu.py to use new banner system"""
        try:
            menu_file = self.ui_path / "menu.py"
            
            if not menu_file.exists():
                self.log("✓ Migrated menu.py to new banner system")
            return True
        
        except Exception as e:
            self.log(f"Migration of menu.py failed: {e}", error=True)
            return False
    
    def create_example_file(self) -> str:
        """Create example usage file"""
        example_code = '''#!/usr/bin/env python3
"""
Example: Using Advanced Banner System
Shows all features and best practices
"""

from ui.banner import AdvancedBannerGenerator, ColorSchemePreset
import time

def example_main_banner():
    """Display main banner with gradient"""
    banner = AdvancedBannerGenerator(ColorSchemePreset.HEAT_WAVE)
    banner.display("main", animate=True)

def example_with_chart():
    """Display banner with integrated chart"""
    banner = AdvancedBannerGenerator(ColorSchemePreset.COOL_BREEZE)
    
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

def example_color_schemes():
    """Demonstrate all color schemes"""
    schemes = [
        ColorSchemePreset.HEAT_WAVE,
        ColorSchemePreset.COOL_BREEZE,
        ColorSchemePreset.NEON_GLOW,
        ColorSchemePreset.NATURE,
    ]
    
    for scheme in schemes:
        banner = AdvancedBannerGenerator(scheme)
        banner.display("main")
        time.sleep(0.5)

def example_custom_banner():
    """Create custom banner"""
    banner = AdvancedBannerGenerator(ColorSchemePreset.NEON_GLOW)
    
    custom = banner.create_custom_banner(
        title="[ SECURITY ALERT ]",
        subtitle="Potential Threat Detected",
        scheme=ColorSchemePreset.NEON_GLOW
    )
    print(custom)

def example_status_dashboard():
    """Display system status"""
    banner = AdvancedBannerGenerator(ColorSchemePreset.HEAT_WAVE)
    
    status = banner.get_system_status_dashboard(
        cpu=67.5,
        memory=54.2,
        network=82.1,
        scans=78.9
    )
    print(status)

def example_threat_level():
    """Display threat assessment"""
    banner = AdvancedBannerGenerator(ColorSchemePreset.HEAT_WAVE)
    
    for level in range(1, 6):
        threat = banner.get_threat_level_display(level)
        print(threat)

def example_line_chart():
    """Display trend line chart"""
    banner = AdvancedBannerGenerator(ColorSchemePreset.COOL_BREEZE)
    
    trend_data = [10, 25, 45, 60, 75, 85, 92, 88, 95, 98]
    print(banner.chart.render_line_chart(
        trend_data,
        height=8,
        width=50,
        title="Detection Trend"
    ))

if __name__ == "__main__":
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
    
    print("\\n=== Line Chart Demo ===")
    example_line_chart()
'''
        return example_code
    
    def log(self, message: str, error: bool = False) -> None:
        """Log migration messages"""
        prefix = "✗" if error else "→"
        print(f"{prefix} {message}")
        self.migration_log.append(message)
    
    def run_full_migration(self) -> bool:
        """Execute complete migration"""
        print("\n" + "=" * 80)
        print("HandyOsint Banner System Migration")
        print("=" * 80 + "\n")
        
        # Step 1: Backup
        self.log("Step 1: Backing up old banner system...")
        if not self.backup_old_banner():
            self.log("Backup failed. Aborting migration.", error=True)
            return False
        
        # Step 2: Scan
        self.log("\nStep 2: Scanning project for Banner usage...")
        imports = self.scan_imports()
        self.log(f"Found {len(imports)} files using Banner")
        
        # Step 3: Migrate imports
        self.log("\nStep 3: Migrating imports in Python files...")
        migrated_count = 0
        for file_path, _ in imports:
            if self.migrate_imports(file_path):
                migrated_count += 1
        self.log(f"Migrated {migrated_count} files")
        
        # Step 4: Migrate specific modules
        self.log("\nStep 4: Migrating specific modules...")
        self.migrate_menu_module()
        
        # Step 5: Create compatibility layer
        self.log("\nStep 5: Creating compatibility layer...")
        compat_file = self.ui_path / "banner_compat.py"
        try:
            with open(compat_file, 'w') as f:
                f.write(self.create_compatibility_layer())
            self.log(f"✓ Created compatibility layer: {compat_file}")
        except Exception as e:
            self.log(f"Failed to create compatibility layer: {e}", error=True)
        
        # Step 6: Create examples
        self.log("\nStep 6: Creating example files...")
        example_file = self.project_root / "banner_examples.py"
        try:
            with open(example_file, 'w') as f:
                f.write(self.create_example_file())
            self.log(f"✓ Created examples: {example_file}")
        except Exception as e:
            self.log(f"Failed to create examples: {e}", error=True)
        
        # Summary
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


def main():
    """Run migration tool"""
    import argparse
    
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
menu.py not found, skipping migration")
                return False
            
            with open(menu_file, 'r') as f:
                content = f.read()
            
            # Check if already uses new system
            if 'AdvancedBannerGenerator' in content:
                self.log("menu.py already uses new banner system")
                return True
            
            # Update imports
            if 'from ui.banner import' in content:
                content = re.sub(
                    r'from ui\.banner import\s+\w+',
                    'from ui.banner import AdvancedBannerGenerator, ColorSchemePreset',
                    content
                )
            
            # Update class initialization
            if 'self.banner = Banner' in content:
                content = content.replace(
                    'self.banner = Banner',
                    'self.banner = AdvancedBannerGenerator(ColorSchemePreset.HEAT_WAVE)'
                )
            
            with open(menu_file, 'w') as f:
                f.write(content)
            
            self.log(")

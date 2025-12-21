"""
Integrated README.md viewer for command center
"""

import os
from pathlib import Path


class IntegratedDocumentation:
    """Interactive documentation from README.md"""

    def __init__(self, readme_path="README.md"):
        self.readme_path = Path(readme_path)
        self.sections = self._parse_readme()

    def _parse_readme(self) -> dict:
        """Parse README.md into interactive sections"""
        if not self.readme_path.exists():
            return self._get_default_sections()

        try:
            with open(self.readme_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Parse sections (simplified - you can enhance this)
            sections = {
                "about": self._extract_section(content, "About", "## "),
                "features": self._extract_section(content, "Features", "## "),
                "usage": self._extract_section(content, "Usage", "## "),
                "installation": self._extract_section(content, "Installation", "## "),
                "license": self._extract_section(content, "License", "## "),
            }
            return sections
        except Exception:
            return self._get_default_sections()

    def _extract_section(self, content, section_name, delimiter):
        """Extract specific section from markdown"""
        # Simplified extraction - can be enhanced with proper markdown parsing
        lines = content.split("\n")
        in_section = False
        section_lines = []

        for line in lines:
            if line.startswith(f"{delimiter}{section_name}"):
                in_section = True
                continue
            elif in_section and line.startswith(delimiter):
                break
            elif in_section:
                section_lines.append(line)

        return "\n".join(section_lines) if section_lines else "Section not found"

    def _get_default_sections(self):
        """Default documentation if README not found"""
        return {
            "about": """
            HANDYOSINT COMMAND CENTER
            ==========================

            Version: 2.4 (16-Bit Vintage Edition)
            A comprehensive OSINT intelligence platform for security
            professionals and researchers.

            This tool provides unified access to multiple intelligence
            gathering modules with enterprise-grade reliability.
            """,
            "features": """
            • Multi-platform target scanning
            • Batch processing capabilities
            • Real-time intelligence dashboard
            • Comprehensive logging system
            • Modular plugin architecture
            • Vintage 16-bit interface
            """,
            "license": """
            EDUCATIONAL/RESEARCH USE ONLY

            Always comply with:
            • Platform Terms of Service
            • Applicable laws and regulations
            • Ethical hacking guidelines

            Use only on systems you own or have explicit permission to test.
            """,
        }

    def display_section(self, section_name):
        """Display a specific documentation section"""
        section = self.sections.get(section_name.lower())
        if section:
            print("\n" + "═" * 60)
            print(f"        {section_name.upper()}")
            print("═" * 60)
            print(section)
            print("═" * 60)
        else:
            print(f"\n[ERROR] Section '{section_name}' not found")

        return section is not None

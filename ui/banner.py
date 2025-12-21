#!/usr/bin/env python3
"""
HandyOsint Banner Generator
Advanced ASCII art system with gradient colors, nancyj-fancy fonts, and sleek charts
Enterprise-grade visual display system
"""

import time
import sys
from typing import Dict, List, Optional, Tuple
from enum import Enum
from collections import deque


class GradientColor(Enum):
    """Advanced gradient color definitions with RGB to ANSI mapping"""

    # Gradient: Red -> Yellow -> Green (Heatmap)
    HEAT_RED = "208"  # Bright Orange-Red
    HEAT_ORANGE = "214"  # Orange
    HEAT_YELLOW = "226"  # Yellow
    HEAT_LIME = "118"  # Lime Green
    HEAT_GREEN = "46"  # Bright Green

    # Gradient: Blue -> Cyan -> White (Cool)
    COOL_NAVY = "17"  # Dark Blue
    COOL_BLUE = "33"  # Blue
    COOL_CYAN = "51"  # Bright Cyan
    COOL_WHITE = "231"  # White

    # Gradient: Purple -> Magenta -> Pink (Neon)
    NEON_PURPLE = "55"  # Purple
    NEON_MAGENTA = "127"  # Magenta
    NEON_PINK = "205"  # Pink
    NEON_WHITE = "231"  # White

    # Gradient: Green -> Cyan -> Blue (Nature)
    NATURE_GREEN = "28"  # Dark Green
    NATURE_LIME = "82"  # Lime
    NATURE_CYAN = "51"  # Cyan
    NATURE_BLUE = "33"  # Blue


class BannerColorScheme(Enum):
    """Professional color scheme presets"""

    HEAT_WAVE = [
        GradientColor.HEAT_RED,
        GradientColor.HEAT_ORANGE,
        GradientColor.HEAT_YELLOW,
        GradientColor.HEAT_LIME,
        GradientColor.HEAT_GREEN,
    ]
    COOL_BREEZE = [
        GradientColor.COOL_NAVY,
        GradientColor.COOL_BLUE,
        GradientColor.COOL_CYAN,
        GradientColor.COOL_WHITE,
    ]
    NEON_GLOW = [
        GradientColor.NEON_PURPLE,
        GradientColor.NEON_MAGENTA,
        GradientColor.NEON_PINK,
        GradientColor.NEON_WHITE,
    ]
    NATURE = [
        GradientColor.NATURE_GREEN,
        GradientColor.NATURE_LIME,
        GradientColor.NATURE_CYAN,
        GradientColor.NATURE_BLUE,
    ]


class NancyJFancyFont:
    """Nancyj-fancy style ASCII art fonts"""

    HANDY_OSINT = r"""
██╗  ██╗ █████╗ ███╗   ██╗ ██████╗ ██╗     ███████╗ ██████╗ ██╗  ██╗
██║  ██║██╔══██╗████╗  ██║██╔════╝ ██║     ██╔════╝██╔═══██╗██║  ██║
███████║███████║██╔██╗ ██║██║  ███╗██║     █████╗  ██║   ██║███████║
██╔══██║██╔══██║██║╚██╗██║██║   ██║██║     ██╔══╝  ██║   ██║██╔══██║
██║  ██║██║  ██║██║ ╚████║╚██████╔╝███████╗███████╗╚██████╔╝██║  ██║
╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝ ╚═════╝ ╚══════╝╚══════╝ ╚═════╝ ╚═╝  ╚═╝
    """

    SCAN_PRO = r"""
 ___  ___  _   _  _ _
/ __|/ __|| | | || 	'_|
\__ \\__ \| |_| || |
|___/|___/ \__,_||_|
"""

    DASHBOARD = r"""
 ____              _     _                     _
|  _ \  __ _  ___ | |__ | |__   ___   __ _  __| |
| | | |/ _` |/ __|| 	'_ \t| '_ \ / _ \ / _` |/ _` |
| |_| | (_| |\__ \| |_) | |_) | (_) | (_| | (_| |
|____/ \__,_||___/|_.__/|_.__/ \___/ \__,_|\__,_|
"""

    RESULTS = r"""
 ____  ___  ____  _   _  _  ___  ____  ___
|  _ \/ _ \/ ___|| | | || ||_ _||_  _/ __|
| |_) | | |\___ \| | | || | | |   | || (__
|____/|_| |_____|\_____/|_| |_|   |_| \___|
"""

    ANALYZE = r"""
  ___ ___   _   _  _ _  ___ ___ ___
 / _ \\_ _| /_\ | \\| | |/ __| _ \\_ _|
| (_) || | / _ \| .` | | (__| v /| |
 \___/|___/_/ \_\|_|_|\___|_|\_\___|
"""
    STATUS_OK = r"""
✓ STATUS OK
"""

    ALERT = r"""
⚠ ALERT
"""


class GradientTextRenderer:
    """Renders text with smooth gradient colors"""

    def __init__(self, scheme: BannerColorScheme = BannerColorScheme.HEAT_WAVE):
        self.scheme = scheme.value
        self.reset = "\033[0m"

    def apply_gradient(
        self, text: str, scheme: Optional[BannerColorScheme] = None
    ) -> str:
        """Apply gradient colors to text"""
        colors = (
            (scheme or self.scheme).value
            if isinstance(scheme, BannerColorScheme)
            else scheme or self.scheme
        )

        result = ""
        text_len = len(text)

        for idx, char in enumerate(text):
            if char.strip():
                # Calculate color index based on position
                color_idx = int((idx / text_len) * (len(colors) - 1))
                color_code = colors[color_idx].value
                result += f"\033[38;5;{color_code}m{char}"
            else:
                result += char

        result += self.reset
        return result

    def apply_rainbow(self, text: str, cycle: bool = False) -> str:
        """Apply rainbow gradient to text"""
        rainbow = [
            196,
            208,
            226,
            82,
            51,
            33,
            127,
        ]  # Red, Orange, Yellow, Lime, Cyan, Blue, Magenta

        result = ""
        for idx, char in enumerate(text):
            if char.strip():
                color_code = rainbow[idx % len(rainbow)]
                result += f"\033[38;5;{color_code}m{char}"
            else:
                result += char

        result += self.reset
        return result


class SleekChart:
    """Professional sleek chart rendering system"""

    def __init__(self, scheme: BannerColorScheme = BannerColorScheme.HEAT_WAVE):
        self.scheme = scheme.value
        self.gradient = GradientTextRenderer(scheme)

    def render_bar_chart(
        self,
        data: Dict[str, float],
        width: int = 40,
        title: str = "",
        show_values: bool = True,
    ) -> str:
        """Render a sleek horizontal bar chart"""
        result = ""

        if title:
            result += f"\n{self.gradient.apply_gradient(title)}\n"

        max_value = max(data.values()) if data else 1
        max_label_len = max(len(str(k)) for k in data.keys()) if data else 0

        for label, value in data.items():
            normalized = (value / max_value) if max_value > 0 else 0
            bar_length = int(normalized * width)

            # Determine color based on value
            color_idx = int(normalized * (len(self.scheme) - 1))
            color = self.scheme[color_idx].value

            bar = "▓" * bar_length + "░" * (width - bar_length)
            value_str = f"{value:.1f}" if show_values else ""

            # Corrected line: escape the literal curly brace
            # The original was: result += f"{label:<{max_label_len}}} |\033[38;5;{color}m{bar}\033[0m| {value_str}\n"
            # The issue was with `max_label_len}}`. It needs to be `{{max_label_len}}` if the outer `}` is literal,
            # or handled differently if `max_label_len` is part of format spec.
            # This version explicitly formats the label width first to avoid nested brace issues.
            label_formatted = f"{label:<{max_label_len}}"
            result += (
                f"{label_formatted} |\033[38;5;{color}m{bar}\033[0m| {value_str}\n"
            )

        return result

    def render_line_chart(
        self, data: List[float], height: int = 10, width: int = 40, title: str = ""
    ) -> str:
        """Render a sleek ASCII line chart"""
        if not data or height < 2:
            return "No data"

        result = ""
        if title:
            result += f"{self.gradient.apply_gradient(title)}\n"

        # Normalize data
        min_val = min(data)
        max_val = max(data)
        range_val = max_val - min_val if max_val != min_val else 1

        # Build chart grid
        grid = [[" " for _ in range(min(len(data), width))] for _ in range(height)]

        # Plot points
        for idx, value in enumerate(data[:width]):
            row = height - 1 - int(((value - min_val) / range_val) * (height - 1))
            if 0 <= row < height and idx < width:
                grid[row][idx] = "●"

        # Draw grid
        colors = self.scheme
        for row_idx, row in enumerate(grid):
            color = colors[int((row_idx / height) * (len(colors) - 1))].value
            line = "".join(row)
            result += f"\033[38;5;{color}m{line}\033[0m\n"

        return result

    def render_progress_bar(
        self,
        value: float,
        max_value: float = 100,
        width: int = 30,
        label: str = "Progress",
    ) -> str:
        """Render sleek progress bar with gradient"""
        percent = (value / max_value) * 100 if max_value > 0 else 0
        filled = int((percent / 100) * width)

        # Color based on progress
        if percent < 33:
            color = "196"  # Red
        elif percent < 66:
            color = "226"  # Yellow
        else:
            color = "46"  # Green

        bar = "█" * filled + "░" * (width - filled)
        return f"{label}: |\033[38;5;{color}m{bar}\033[0m| {percent:.1f}%\n"


class Banner:
    """Enterprise-grade banner system with gradient colors and charts"""

    def __init__(self, scheme: BannerColorScheme = BannerColorScheme.HEAT_WAVE):
        self.scheme = scheme
        self.gradient = GradientTextRenderer(scheme)
        self.chart = SleekChart(scheme)
        self.animations_enabled = True
        self.font = NancyJFancyFont()

    # ========================================================================
    # MAIN BANNERS WITH NANCYJ-FANCY FONT
    # ========================================================================

    def get_main_banner(self) -> str:
        """Main banner with gradient nancyj-fancy font"""
        ascii_art = self.font.HANDY_OSINT
        gradient_art = self.gradient.apply_gradient(ascii_art)

        border = "═" * 80
        border_gradient = self.gradient.apply_gradient(border)

        return f"""
{border_gradient}
{gradient_art}
{border_gradient}
{self.gradient.apply_gradient('  🔍 Advanced OSINT Intelligence Framework | Enterprise Edition v3.0')}
{self.gradient.apply_rainbow('  Open Source Security Intelligence • Real-Time Analysis • Deep Investigation')}
{border_gradient}
"""

    def get_scan_banner(self) -> str:
        """Scan progress banner"""
        ascii_art = self.font.SCAN_PRO
        gradient_art = self.gradient.apply_gradient(ascii_art)

        return f"""
{self.gradient.apply_rainbow('╔' + '═' * 78 + '╗')}
{self.gradient.apply_gradient(f'║{gradient_art:<77}║')}
{self.gradient.apply_rainbow('╚' + '═' * 78 + '╝')}
"""

    def get_dashboard_banner(self) -> str:
        """Dashboard banner with chart preview"""
        ascii_art = self.font.DASHBOARD
        gradient_art = self.gradient.apply_gradient(ascii_art)

        return f"""
{self.gradient.apply_rainbow('╔' + '═' * 78 + '╗')}
{gradient_art}
{self.gradient.apply_rainbow('╚' + '═' * 78 + '╝')}
"""

    def get_results_banner(self) -> str:
        """Results display banner"""
        ascii_art = self.font.RESULTS
        gradient_art = self.gradient.apply_gradient(ascii_art)

        return f"""
{self.gradient.apply_rainbow('┌' + '─' * 78 + '┐')}
{gradient_art}
{self.gradient.apply_rainbow('└' + '─' * 78 + '┘')}
"""

    def get_analyze_banner(self) -> str:
        """Analysis mode banner"""
        ascii_art = self.font.ANALYZE
        gradient_art = self.gradient.apply_rainbow(ascii_art)

        return f"""
{self.gradient.apply_gradient('▁' * 80)}
{gradient_art}
{self.gradient.apply_gradient('▔' * 80)}
"""

    # ========================================================================
    # CHART INTEGRATION METHODS
    # ========================================================================

    def display_with_chart(
        self,
        banner_type: str = "main",
        chart_data: Optional[Dict[str, float]] = None,
        chart_type: str = "bar",
    ) -> str:
        """Display banner with integrated chart"""
        banners = {
            "main": self.get_main_banner,
            "scan": self.get_scan_banner,
            "dashboard": self.get_dashboard_banner,
            "results": self.get_results_banner,
            "analyze": self.get_analyze_banner,
        }

        banner = banners.get(banner_type, banners["main"])
        result = banner()

        # Add chart if data provided
        if chart_data:
            if chart_type == "bar":
                result += self.chart.render_bar_chart(
                    chart_data,
                    width=50,
                    title=self.gradient.apply_gradient("📊 Intelligence Metrics"),
                )
            elif chart_type == "line":
                line_data = list(chart_data.values())
                result += self.chart.render_line_chart(
                    line_data,
                    height=8,
                    width=60,
                    title=self.gradient.apply_gradient("📈 Trend Analysis"),
                )
            elif chart_type == "progress":
                for label, value in chart_data.items():
                    result += self.chart.render_progress_bar(value, 100, 30, label)

        return result

    # ========================================================================
    # DISPLAY METHODS
    # ========================================================================

    def display(
        self,
        banner_type: str = "main",
        animate: bool = False,
        chart_data: Optional[Dict[str, float]] = None,
        chart_type: str = "bar",
    ) -> None:
        """Display banner with optional animation and charts"""
        output = self.display_with_chart(banner_type, chart_data, chart_type)

        if animate and self.animations_enabled:
            self._animate_output(output)
        else:
            print(output)

    def _animate_output(self, text: str, char_delay: float = 0.003) -> None:
        """Animate output character by character"""
        try:
            for char in text:
                sys.stdout.write(char)
                sys.stdout.flush()
                time.sleep(char_delay)
        except KeyboardInterrupt:
            print(text)

    def display_status_ok(self) -> None:
        """Display status OK indicator"""
        status = self.gradient.apply_gradient(self.font.STATUS_OK)
        print(status)

    def display_alert(self) -> None:
        """Display alert indicator"""
        alert = self.gradient.apply_gradient(self.font.ALERT)
        print(alert)

    # ========================================================================
    # CONFIGURATION METHODS
    # ========================================================================

    def set_animation(self, enabled: bool) -> None:
        """Enable/disable animations"""
        self.animations_enabled = enabled

    def change_scheme(self, scheme: BannerColorScheme) -> None:
        """Change color scheme"""
        self.scheme = scheme
        self.gradient = GradientTextRenderer(scheme)
        self.chart = SleekChart(scheme)

    # ========================================================================
    # ADVANCED FEATURES
    # ========================================================================

    def get_system_status_dashboard(
        self,
        cpu: float = 45.0,
        memory: float = 62.0,
        network: float = 78.0,
        scans: float = 91.0,
    ) -> str:
        """Display system status with gradient charts"""
        dashboard = self.get_dashboard_banner()

        status_data = {"CPU": cpu, "Memory": memory, "Network": network, "Scans": scans}

        dashboard += "\n" + self.gradient.apply_gradient("┌─ System Status ─┐\n")
        dashboard += self.chart.render_bar_chart(
            status_data, width=30, show_values=True
        )
        dashboard += self.gradient.apply_gradient("\n└─────────────────┘\n")

        return dashboard

    def get_threat_level_display(self, level: int = 5) -> str:
        """Display threat level with gradient indicator"""
        threat_map = {
            1: ("LOW", "46"),  # Green
            2: ("LOW", "46"),
            3: ("MEDIUM", "226"),  # Yellow
            4: ("HIGH", "208"),  # Orange
            5: ("CRITICAL", "196"),  # Red
        }

        threat_text, color = threat_map.get(level, ("UNKNOWN", "37"))

        gauge = "▓" * level + "░" * (5 - level)

        return f"\n{self.gradient.apply_gradient('Threat Level:')} |\033[38;5;{color}m{gauge}\033[0m| {threat_text}\n"

    def create_custom_banner(
        self, title: str, subtitle: str = "", scheme: Optional[BannerColorScheme] = None
    ) -> str:
        """Create custom banner with user-provided text"""
        if scheme:
            self.change_scheme(scheme)

        border = "═" * 80
        border_gradient = self.gradient.apply_gradient(border)
        title_gradient = self.gradient.apply_rainbow(title.center(80))

        result = f"\n{border_gradient}\n{title_gradient}\n"

        if subtitle:
            subtitle_gradient = self.gradient.apply_gradient(subtitle.center(80))
            result += f"{subtitle_gradient}\n"

        result += f"{border_gradient}\n"

        return result


__all__ = [
    "Banner",
    "BannerColorScheme",
    "GradientColor",
    "NancyJFancyFont",
    "GradientTextRenderer",
    "SleekChart",
]

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================


def demo_all_schemes() -> None:
    """Display demo of all color schemes"""
    schemes = [
        BannerColorScheme.HEAT_WAVE,
        BannerColorScheme.COOL_BREEZE,
        BannerColorScheme.NEON_GLOW,
        BannerColorScheme.NATURE,
    ]

    for scheme in schemes:
        banner = Banner(scheme)
        print(banner.get_main_banner())
        time.sleep(1)


def demo_charts() -> None:
    """Display demo charts"""
    banner = Banner(BannerColorScheme.HEAT_WAVE)

    print("\n" + "═" * 80)
    print(banner.gradient.apply_gradient("BAR CHART DEMO"))
    print("═" * 80)
    chart_data = {
        "Malware": 75.0,
        "Phishing": 45.0,
        "SQL Injection": 92.0,
        "XSS": 38.0,
        "CSRF": 61.0,
    }
    print(banner.chart.render_bar_chart(chart_data, width=40, title="Security Threats"))

    print("\n" + "═" * 80)
    print(banner.gradient.apply_gradient("LINE CHART DEMO"))
    print("═" * 80)
    line_data = [10, 25, 45, 60, 75, 85, 92, 88, 95, 98]
    print(
        banner.chart.render_line_chart(
            line_data, height=8, width=40, title="Detection Rate"
        )
    )

    print("\n" + "═" * 80)
    print(banner.gradient.apply_gradient("PROGRESS BARS DEMO"))
    print("═" * 80)
    progress_data = {
        "Scan Complete": 87.0,
        "Analysis": 64.0,
        "Reporting": 41.0,
    }
    for label, value in progress_data.items():
        print(banner.chart.render_progress_bar(value, 100, 30, label), end="")


# ============================================================================
# MAIN DEMONSTRATION
# ============================================================================

if __name__ == "__main__":
    # Create banner generator
    banner_gen = Banner(BannerColorScheme.HEAT_WAVE)

    # Display main banner
    print("\n" + banner_gen.get_main_banner())

    # Display status dashboard
    print(
        banner_gen.get_system_status_dashboard(cpu=67, memory=54, network=82, scans=78)
    )

    # Display threat level
    print(banner_gen.get_threat_level_display(level=4))

    # Display custom banner
    print(
        banner_gen.create_custom_banner(
            title="[ THREAT DETECTED ]",
            subtitle="Initiating Counter-Measures...",
            scheme=BannerColorScheme.NEON_GLOW,
        )
    )

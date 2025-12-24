# pylint: disable=R0914
#!/usr/bin/env python3
"""
HandyOsint Banner Generator - Professional Enterprise Edition
Advanced ASCII art system with gradient colors, responsive design, and smooth animations.

This module provides an enterprise-grade visual display system with:
- Responsive terminal width detection
- Dark orange to light orange gradient color schemes
- Professional smooth animations
- Sleek charts and visualizations
- Full pylint compliance
"""

import os
import sys
import time
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Tuple


@dataclass
class TerminalConfig:  # pylint: disable=R0903
    """Terminal configuration and capabilities."""

    width: int
    height: int
    supports_colors: bool

    @staticmethod
    def detect() -> "TerminalConfig":
        """Detect terminal capabilities and constraints."""
        try:
            term_size = os.get_terminal_size()
            width = term_size.columns
            height = term_size.lines
        except (AttributeError, ValueError):
            width = 80
            height = 24

        width = max(40, min(width, 200))
        height = max(10, min(height, 50))

        supports_colors = sys.stdout.isatty()

        return TerminalConfig(
            width=width, height=height, supports_colors=supports_colors
        )


class GradientColor(Enum):
    """Professional gradient color definitions with ANSI codes."""

    # Dark Orange to Light Orange Gradient
    ORANGE_DARK = "52"  # Dark brown
    ORANGE_DARK1 = "94"  # Dark orange
    ORANGE_DARK2 = "130"  # Darker burnt orange
    ORANGE_MEDIUM = "166"  # Medium orange
    ORANGE_MEDIUM1 = "172"  # Lighter medium orange
    ORANGE_LIGHT = "178"  # Light orange
    ORANGE_LIGHT1 = "215"  # Lighter orange
    ORANGE_LIGHTER = "216"  # Very light orange
    ORANGE_PALE = "223"  # Pale orange

    # Neutral grays for text
    GRAY_DARK = "235"
    GRAY_MEDIUM = "245"
    GRAY_LIGHT = "255"

    # Accent colors
    WHITE = "231"
    BLACK = "16"


class BannerColorScheme(Enum):
    """Professional color scheme presets."""

    DARK_ORANGE = [
        GradientColor.ORANGE_DARK,
        GradientColor.ORANGE_DARK1,
        GradientColor.ORANGE_DARK2,
        GradientColor.ORANGE_MEDIUM,
        GradientColor.ORANGE_MEDIUM1,
        GradientColor.ORANGE_LIGHT,
        GradientColor.ORANGE_LIGHT1,
        GradientColor.ORANGE_LIGHTER,
    ]

    PROFESSIONAL = [
        GradientColor.ORANGE_DARK1,
        GradientColor.ORANGE_MEDIUM,
        GradientColor.ORANGE_LIGHT,
    ]


class ProfessionalFonts:  # pylint: disable=R0903
    """Professional ASCII art fonts for enterprise display."""

    HANDY_OSINT = r"""
    ██╗  ██╗ █████╗ ███╗   ██╗ ██████╗ ██╗   ██╗
    ██║  ██║██╔══██╗████╗  ██║██╔════╝ ██║   ██║
    ███████║███████║██╔██╗ ██║██║  ███╗██║   ██║
    ██╔══██║██╔══██║██║╚██╗██║██║   ██║╚██╗ ██╔╝
    ██║  ██║██║  ██║██║ ╚████║╚██████╔╝ ╚████╔╝
    ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝ ╚═════╝   ╚═══╝
    """

    OSINT = r"""
    ╔═══════════════════════════════════════╗
    ║        OPEN SOURCE INTELLIGENCE       ║
    ║         PROFESSIONAL PLATFORM          ║
    ╚═══════════════════════════════════════╝
    """

    SCAN = r"""
    ▓▒░ S C A N   I N   P R O G R E S S ░▒▓
    """

    ANALYSIS = r"""
    ┌─ A N A L Y S I S   M O D E ─┐
    """

    RESULTS = r"""
    ╔═ R E S U L T S   D I S P L A Y ═╗
    """

    @staticmethod
    def get_font(font_name: str) -> str:
        """Retrieve font by name with validation."""
        fonts = {
            "osint": ProfessionalFonts.HANDY_OSINT,
            "scan": ProfessionalFonts.SCAN,
            "analysis": ProfessionalFonts.ANALYSIS,
            "results": ProfessionalFonts.RESULTS,
        }
        return fonts.get(font_name, ProfessionalFonts.HANDY_OSINT)


class GradientRenderer:
    """Renders text with smooth gradient colors."""

    ANSI_RESET = "\033[0m"
    ANSI_BOLD = "\033[1m"
    ANSI_DIM = "\033[2m"

    def __init__(self, scheme: BannerColorScheme = BannerColorScheme.DARK_ORANGE):
        """Initialize gradient renderer with color scheme."""
        self.scheme = scheme.value
        self.supports_colors = True

    def apply_gradient(self, text: str, bold: bool = False) -> str:
        """Apply smooth gradient to text."""
        if not self.supports_colors or not text:
            return text

        colors = self.scheme
        result = ""
        text_len = len(text)

        for idx, char in enumerate(text):
            if char not in (" ", "\n", "\t"):
                color_idx = int((idx / max(text_len, 1)) * (len(colors) - 1))
                color_code = colors[color_idx].value

                if bold:
                    result += f"\033[1;38;5;{color_code}m{char}"
                else:
                    result += f"\033[38;5;{color_code}m{char}"
            else:
                result += char

        result += self.ANSI_RESET
        return result

    def solid_color(self, text: str, color: GradientColor, bold: bool = False) -> str:
        """Apply solid color to text."""
        if not self.supports_colors:
            return text

        style = f"\033[1;38;5;{color.value}m" if bold else f"\033[38;5;{color.value}m"
        return f"{style}{text}{self.ANSI_RESET}"


class SleekChart:
    """Professional sleek chart rendering system."""

    def __init__(
        self,
        terminal: TerminalConfig,
        scheme: BannerColorScheme = BannerColorScheme.DARK_ORANGE,
    ):
        """Initialize chart renderer."""
        self.terminal = terminal
        self.scheme = scheme.value
        self.gradient = GradientRenderer(scheme)

    def render_bar_chart(
        self,
        data: Dict[str, float],
        width: Optional[int] = None,
        title: str = "",
        show_values: bool = True,
    ) -> str:
        """Render professional horizontal bar chart."""
        if width is None:
            width = max(20, self.terminal.width - 40)

        result = ""

        if title:
            result += f"\n{self.gradient.apply_gradient(title, bold=True)}\n"

        if not data:
            return result

        max_value = max(data.values())
        max_label_len = max(len(str(k)) for k in data.keys())

        for label, value in data.items():
            normalized = (value / max_value) if max_value > 0 else 0
            bar_length = int(normalized * width)

            color_idx = int(normalized * (len(self.scheme) - 1))
            color_code = self.scheme[color_idx].value

            filled_portion = "█" * bar_length
            empty_portion = "░" * (width - bar_length)
            bar_display = filled_portion + empty_portion
            value_str = f"{value:.1f}" if show_values else ""

            label_formatted = f"{label:<{max_label_len}}"
            result += (
                f"{label_formatted} |\033[38;5;{color_code}m"
                f"{bar_display}\033[0m| {value_str}\n"
            )

        return result

    def render_progress_bar(
        self,
        value: float,
        max_value: float = 100,
        width: Optional[int] = None,
        label: str = "Progress",
    ) -> str:
        """Render professional progress bar."""
        if width is None:
            width = max(15, self.terminal.width - 30)

        percent = (value / max_value) * 100 if max_value > 0 else 0
        filled = int((percent / 100) * width)

        # Color progression based on completion percentage
        if percent < 33:
            color = GradientColor.ORANGE_DARK.value
        elif percent < 66:
            color = GradientColor.ORANGE_MEDIUM.value
        else:
            color = GradientColor.ORANGE_LIGHT.value

        filled_bar = "█" * filled
        empty_bar = "░" * (width - filled)
        bar_display = filled_bar + empty_bar
        return f"{label}: |\033[38;5;{color}m{bar_display}\033[0m| " f"{percent:.1f}%\n"

    def _build_chart_grid(self, data: List[float], height: int, width: int) -> list:
        """Build chart grid for line visualization."""
        min_val = min(data)
        max_val = max(data)
        range_val = max_val - min_val if max_val != min_val else 1

        grid = [[" " for _ in range(min(len(data), width))] for _ in range(height)]

        for idx, value in enumerate(data[:width]):
            norm_height = ((value - min_val) / range_val) * (height - 1)
            row_pos = height - 1 - int(norm_height)
            if 0 <= row_pos < height and idx < width:
                grid[row_pos][idx] = "●"

        return grid

    def render_line_chart(
        self,
        data: List[float],
        height: int = 8,
        width: Optional[int] = None,
        title: str = "",
    ) -> str:
        """Render professional ASCII line chart."""
        if width is None:
            width = max(20, self.terminal.width - 20)

        if not data or height < 2:
            return "No data available\n"

        result = ""
        if title:
            result += f"{self.gradient.apply_gradient(title, bold=True)}\n"

        grid = self._build_chart_grid(data, height, width)
        colors = self.scheme

        for row_idx, row in enumerate(grid):
            color_ratio = row_idx / height if height > 0 else 0
            color_idx = int(color_ratio * (len(colors) - 1))
            color = colors[color_idx].value
            line = "".join(row)
            result += f"\033[38;5;{color}m{line}\033[0m\n"

        return result


class AnimationEngine:
    """Professional smooth animation system."""

    # Animation types (professional, no color)
    ANIM_NONE = "none"
    ANIM_TYPEWRITER = "typewriter"
    ANIM_FADE = "fade"
    ANIM_SLIDE = "slide"

    def __init__(self, enabled: bool = True, animation_type: str = ANIM_TYPEWRITER):
        """Initialize animation engine."""
        self.enabled = enabled
        self.animation_type = animation_type

    def typewriter_effect(self, text: str, delay: float = 0.02) -> None:
        """Professional typewriter animation."""
        if not self.enabled:
            print(text)
            return

        try:
            for char in text:
                sys.stdout.write(char)
                sys.stdout.flush()
                time.sleep(delay)
            print()
        except KeyboardInterrupt:
            print(text)

    def fade_effect(self, text: str, steps: int = 10) -> None:
        """Smooth fade animation effect."""
        if not self.enabled:
            print(text)
            return

        delay = 0.05
        actual_steps = max(steps, 1)
        for _ in range(actual_steps):
            sys.stdout.write("\r" + text)
            sys.stdout.flush()
            time.sleep(delay)

        print()


class Banner:
    """Enterprise-grade banner system with responsive design."""

    def __init__(self, scheme: BannerColorScheme = BannerColorScheme.DARK_ORANGE):
        """Initialize banner system."""
        self.terminal = TerminalConfig.detect()
        self.scheme = scheme
        self.gradient = GradientRenderer(scheme)
        self.chart = SleekChart(self.terminal, scheme)
        self.animation = AnimationEngine(enabled=True, animation_type="typewriter")
        self.fonts = ProfessionalFonts()

    def _get_responsive_width(self, ratio: float = 0.9) -> int:
        """Get responsive width based on terminal size."""
        return max(40, int(self.terminal.width * ratio))

    def _create_border(
        self,
        width: Optional[int] = None,
        char: str = "═",
        corners: Tuple[str, str] = ("╔", "╗"),
    ) -> str:
        """Create responsive border."""
        if width is None:
            width = self._get_responsive_width()

        return f"{corners[0]}{char * (width - 2)}{corners[1]}"

    def _prepare_banner_elements(
        self, width: int
    ) -> Tuple[str, str, str, str, str]:  # pylint: disable=R0914
        """Prepare reusable banner elements."""
        border = self._create_border(width)
        border_gradient = self.gradient.apply_gradient(border, bold=True)

        ascii_art = self.fonts.HANDY_OSINT
        gradient_art = self.gradient.apply_gradient(ascii_art, bold=False)

        subtitle = "Enterprise Intelligence Framework | Professional Edition v4.0"
        subtitle_centered = subtitle.center(width)
        subtitle_gradient = self.gradient.apply_gradient(subtitle_centered, bold=True)

        divider = "─" * (width - 2)
        divider_gradient = self.gradient.solid_color(divider, GradientColor.GRAY_MEDIUM)

        return (
            border_gradient,
            gradient_art,
            divider_gradient,
            subtitle_gradient,
            divider_gradient,
        )

    def get_main_banner(self) -> str:
        """Generate main banner with gradient colors."""
        width = self._get_responsive_width()
        border_g, ascii_g, divider_g, subtitle_g, divider_g2 = (
            self._prepare_banner_elements(width)
        )

        return f"""
{border_g}
{ascii_g}
{border_g}
{divider_g}
{subtitle_g}
{divider_g2}
"""

    def get_scan_banner(self) -> str:
        """Generate scan progress banner."""
        width = self._get_responsive_width()
        border = self._create_border(width)
        border_gradient = self.gradient.apply_gradient(border, bold=True)

        scan_text = self.fonts.SCAN
        scan_gradient = self.gradient.apply_gradient(scan_text, bold=True)
        scan_centered = scan_gradient.center(width)

        return f"""
{border_gradient}
{scan_centered}
{border_gradient}
"""

    def get_analysis_banner(self) -> str:
        """Generate analysis mode banner."""
        width = self._get_responsive_width()
        border = "▁" * width
        border_gradient = self.gradient.apply_gradient(border, bold=False)

        analysis_text = self.fonts.ANALYSIS
        analysis_gradient = self.gradient.apply_gradient(analysis_text, bold=True)

        return f"""
{border_gradient}
{analysis_gradient}
{border_gradient}
"""

    def get_results_banner(self) -> str:
        """Generate results display banner."""
        width = self._get_responsive_width()
        border = self._create_border(width, char="═", corners=("╔", "╗"))
        border_gradient = self.gradient.apply_gradient(border, bold=True)

        results_text = self.fonts.RESULTS
        results_gradient = self.gradient.apply_gradient(results_text, bold=True)

        return f"""
{border_gradient}
{results_gradient}
{border_gradient}
"""

    def display_system_dashboard(
        self,
        cpu: float = 45.0,
        memory: float = 62.0,
        network: float = 78.0,
        scans: float = 91.0,
    ) -> str:
        """Display system status dashboard with metrics."""
        dashboard = self.get_analysis_banner()

        status_data = {
            "CPU Usage": cpu,
            "Memory": memory,
            "Network": network,
            "Scans": scans,
        }

        title_text = "╔═ System Status ═╗"
        title_gradient = self.gradient.apply_gradient(title_text, bold=True)
        dashboard += f"\n{title_gradient}\n"

        chart_output = self.chart.render_bar_chart(
            status_data, width=self._get_responsive_width(0.6), show_values=True
        )
        dashboard += chart_output

        footer_text = "╚════════════════╝"
        footer_gradient = self.gradient.apply_gradient(footer_text, bold=True)
        dashboard += f"{footer_gradient}\n"

        return dashboard

    def display_threat_level(self, level: int = 3) -> str:
        """Display threat level indicator."""
        threat_levels = {
            1: ("LOW", GradientColor.ORANGE_DARK),
            2: ("MEDIUM", GradientColor.ORANGE_MEDIUM),
            3: ("HIGH", GradientColor.ORANGE_LIGHT),
            4: ("CRITICAL", GradientColor.ORANGE_LIGHTER),
            5: ("MAXIMUM", GradientColor.WHITE),
        }

        threat_text, color = threat_levels.get(
            level, ("UNKNOWN", GradientColor.GRAY_MEDIUM)
        )
        level = max(1, min(level, 5))

        gauge = "▓" * level + "░" * (5 - level)

        threat_label = self.gradient.solid_color("Threat Level:", color, bold=True)
        gauge_colored = self.gradient.solid_color(gauge, color, bold=True)

        return f"\n{threat_label} [{gauge_colored}] {threat_text}\n"

    def create_custom_banner(self, title: str, subtitle: str = "") -> str:
        """Create custom responsive banner."""
        width = self._get_responsive_width()

        border = self._create_border(width)
        border_gradient = self.gradient.apply_gradient(border, bold=True)

        title_centered = title.center(width)
        title_gradient = self.gradient.apply_gradient(title_centered, bold=True)

        result = f"\n{border_gradient}\n{title_gradient}\n"

        if subtitle:
            subtitle_centered = subtitle.center(width)
            subtitle_gradient = self.gradient.apply_gradient(
                subtitle_centered, bold=False
            )
            result += f"{subtitle_gradient}\n"

        result += f"{border_gradient}\n"

        return result

    def display(self, banner_type: str = "main", animate: bool = True) -> None:
        """Display banner with optional animation."""
        banners = {
            "main": self.get_main_banner(),
            "scan": self.get_scan_banner(),
            "analysis": self.get_analysis_banner(),
            "results": self.get_results_banner(),
            "dashboard": self.display_system_dashboard(),
        }

        output = banners.get(banner_type, banners["main"])

        if animate:
            self.animation.typewriter_effect(output, delay=0.005)
        else:
            print(output)

    def set_animation(self, enabled: bool, animation_type: str = "typewriter") -> None:
        """Configure animation settings."""
        self.animation.enabled = enabled
        self.animation.animation_type = animation_type

    def change_scheme(self, scheme: BannerColorScheme) -> None:
        """Change color scheme dynamically."""
        self.scheme = scheme
        self.gradient = GradientRenderer(scheme)
        self.chart = SleekChart(self.terminal, scheme)


def main():
    """Main demonstration function."""
    banner = Banner(BannerColorScheme.DARK_ORANGE)

    # Display main banner
    print("\n")
    banner.display("main", animate=False)

    # System dashboard
    print("\n")
    print(banner.display_system_dashboard(cpu=67, memory=54, network=82, scans=78))

    # Threat level
    print(banner.display_threat_level(level=3))

    # Custom banner
    print("\n")
    custom = banner.create_custom_banner(
        title="[ SECURITY ANALYSIS ]", subtitle="Professional Intelligence Platform"
    )
    print(custom)

    # Progress demonstration
    print("\nOperation Progress:\n")
    for i in range(0, 101, 20):
        print(banner.chart.render_progress_bar(i, 100, label="Processing"), end="")
        time.sleep(0.5)


if __name__ == "__main__":
    main()

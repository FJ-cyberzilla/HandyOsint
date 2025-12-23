#!/usr/bin/env python3
"""
HandyOsint Terminal Management System
Modern terminal utilities and effects with full pylint compliance.

This module provides:
- Terminal color schemes and styling
- Boot and shutdown sequences
- Progress bar visualization
- Status indicators and messaging
- Cross-platform terminal support
"""

import time
import platform
from typing import Optional, List
from enum import Enum

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
from rich.text import Text


class TerminalColorScheme(Enum):
    """ANSI terminal color schemes."""

    GREEN_PLASMA = "green"
    AMBER_MONO = "yellow"
    COOL_BLUE = "blue"
    MONOCHROME = "white"


class Terminal:
    """Modern terminal control and effects."""

    def __init__(
        self,
        scheme: TerminalColorScheme = TerminalColorScheme.GREEN_PLASMA
    ) -> None:
        """Initialize terminal with color scheme."""
        self.scheme = scheme.value
        self.console = Console()
        self.platform = platform.system()

    def clear(self) -> None:
        """Clear terminal screen."""
        self.console.clear()

    def write(self, text: str, style: str = "white",
              newline: bool = True) -> None:
        """Write styled text to terminal."""
        self.console.print(text, style=style, end="\n" if newline else "")

    def boot_sequence(self, steps: Optional[List[str]] = None) -> None:
        """Display boot sequence with status updates."""
        if steps is None:
            steps = [
                "INITIALIZING HANDYOSINT COMMAND CENTER...",
                "LOADING CORE MODULES...",
                "ESTABLISHING SECURE DATA CHANNELS...",
                "SYSTEM READY. AWAITING COMMANDS...",
            ]

        with self.console.status(
            "[bold green]Booting system..."
        ) as status:
            for step in steps:
                time.sleep(0.02)
                status.update(f"[bold green]{step}")

        self.console.print("[bold green]Boot sequence complete.[/bold green]")

    def shutdown_sequence(self, steps: Optional[List[str]] = None) -> None:
        """Display shutdown sequence with status updates."""
        if steps is None:
            steps = [
                "TERMINATING USER SESSIONS...",
                "ARCHIVING OPERATION LOGS...",
                "CLOSING SECURE CONNECTIONS...",
                "SYSTEM HALTED.",
            ]

        with self.console.status(
            "[bold yellow]Shutting down..."
        ) as status:
            for step in steps:
                time.sleep(0.1)
                status.update(f"[bold yellow]{step}")

        self.console.print("[bold yellow]Shutdown complete.[/bold yellow]")

    def progress_bar(self) -> Progress:
        """Return a rich progress bar context manager."""
        return Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=self.console,
        )

    def write_info(self, text: str) -> None:
        """Write info message with icon."""
        self.console.print(Text(f"[ℹ] {text}", style="cyan"))

    def write_success(self, text: str) -> None:
        """Write success message with icon."""
        self.console.print(Text(f"[✓] {text}", style="green"))

    def write_error(self, text: str) -> None:
        """Write error message with icon."""
        self.console.print(Text(f"[✗] {text}", style="red"))

    def write_warning(self, text: str) -> None:
        """Write warning message with icon."""
        self.console.print(Text(f"[⚠] {text}", style="yellow"))

    def change_scheme(self, scheme: TerminalColorScheme) -> None:
        """Change terminal color scheme dynamically."""
        self.scheme = scheme.value

    def get_platform(self) -> str:
        """Get current platform name."""
        return self.platform

    def is_windows(self) -> bool:
        """Check if running on Windows."""
        return self.platform == "Windows"

    def is_linux(self) -> bool:
        """Check if running on Linux."""
        return self.platform == "Linux"

    def is_macos(self) -> bool:
        """Check if running on macOS."""
        return self.platform == "Darwin"


def demo_terminal() -> None:
    """Demonstrate terminal functionality."""
    terminal = Terminal(TerminalColorScheme.GREEN_PLASMA)

    terminal.clear()
    terminal.write_info("Terminal system initialized")
    terminal.write_success("Connection established")
    terminal.write_warning("Demo mode active")
    terminal.write_error("This is a test error")

    print("\nPlatform Detection:")
    print(f"  Platform: {terminal.get_platform()}")
    print(f"  Windows: {terminal.is_windows()}")
    print(f"  Linux: {terminal.is_linux()}")
    print(f"  macOS: {terminal.is_macos()}")

    print("\nBoot Sequence:")
    terminal.boot_sequence()

    print("\nShutdown Sequence:")
    terminal.shutdown_sequence()


if __name__ == "__main__":
    demo_terminal()

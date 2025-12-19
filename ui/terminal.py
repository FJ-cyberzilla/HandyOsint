#!/usr/bin/env python3
"""
HandyOsint Terminal Management
Modern terminal utilities and effects
"""

import os
import sys
import time
import platform
from typing import Tuple, Optional, List
from enum import Enum

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
from rich.text import Text


class TerminalColorScheme(Enum):
    """ANSI terminal color schemes"""
    GREEN_PLASMA = "green"
    AMBER_MONO = "yellow"
    COOL_BLUE = "blue"
    MONOCHROME = "white"


class Terminal:
    """Modern terminal control and effects"""

    def __init__(self, scheme: TerminalColorScheme = TerminalColorScheme.GREEN_PLASMA):
        """Initialize terminal with color scheme"""
        self.scheme = scheme.value
        self.console = Console()
        self.platform = platform.system()

    def clear(self) -> None:
        """Clear terminal screen"""
        self.console.clear()

    def write(self, text: str, style: str = "white", newline: bool = True):
        """Write styled text"""
        self.console.print(text, style=style, end="\n" if newline else "")

    def boot_sequence(self, steps: Optional[List[str]] = None) -> None:
        """Display boot sequence"""
        if steps is None:
            steps = [
                "INITIALIZING HANDYOSINT COMMAND CENTER...",
                "LOADING CORE MODULES...",
                "ESTABLISHING SECURE DATA CHANNELS...",
                "SYSTEM READY. AWAITING COMMANDS...",
            ]
        
        with self.console.status("[bold green]Booting system...") as status:
            for step in steps:
                time.sleep(0.5)
                status.update(f"[bold green]{step}")
        self.console.print("[bold green]Boot sequence complete.[/bold green]")

    def shutdown_sequence(self, steps: Optional[List[str]] = None) -> None:
        """Display shutdown sequence"""
        if steps is None:
            steps = [
                "TERMINATING USER SESSIONS...",
                "ARCHIVING OPERATION LOGS...",
                "CLOSING SECURE CONNECTIONS...",
                "SYSTEM HALTED.",
            ]
        
        with self.console.status("[bold yellow]Shutting down...") as status:
            for step in steps:
                time.sleep(0.5)
                status.update(f"[bold yellow]{step}")
        self.console.print("[bold yellow]Shutdown complete.[/bold yellow]")

    def progress_bar(self, total: int, description: str = "Processing..."):
        """Returns a rich progress bar context manager"""
        return Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=self.console,
        )
        
    def write_info(self, text: str):
        self.console.print(Text(f"[ℹ] {text}", style="cyan"))
        
    def write_success(self, text: str):
        self.console.print(Text(f"[✓] {text}", style="green"))

    def write_error(self, text: str):
        self.console.print(Text(f"[✗] {text}", style="red"))

    def write_warning(self, text: str):
        self.console.print(Text(f"[⚠] {text}", style="yellow"))


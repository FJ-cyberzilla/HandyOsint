#!/usr/bin/env python3
"""
HandyOsint Menu System
Modern, rich-based interactive menu system
"""

import asyncio
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass
from enum import Enum

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn

try:
    import aioconsole
except ImportError:
    aioconsole = None


@dataclass
class MenuItem:
    """Menu item data structure"""

    key: str
    label: str
    description: str
    icon: str
    action: Optional[Callable] = None


class MenuColorScheme(Enum):
    """Menu color schemes"""

    GREEN_PLASMA = "green"
    AMBER_MONO = "yellow"
    COOL_BLUE = "blue"
    MONOCHROME = "white"


class Menu:
    """Modern menu system using rich"""

    def __init__(
        self,
        title: str = "COMMAND CENTER",
        color_scheme: MenuColorScheme = MenuColorScheme.GREEN_PLASMA,
    ):
        """Initialize menu system"""
        self.title = title
        self.color_scheme = color_scheme.value
        self.items: Dict[str, MenuItem] = {}
        self.console = Console()

    def add_item(
        self,
        key: str,
        label: str,
        description: str = "",
        icon: str = "►",
        action: Optional[Callable] = None,
    ) -> None:
        """Add menu item"""
        self.items[key] = MenuItem(key, label, description, icon, action)

    def display(self) -> None:
        """Display the menu"""
        menu_table = Table.grid(expand=True)
        menu_table.add_column()

        for key, item in self.items.items():
            menu_table.add_row(
                Text(f"[{item.key}] {item.icon} {item.label}", style=self.color_scheme),
                Text(f"  {item.description}", style="dim"),
            )

        self.console.print(
            Panel(
                menu_table,
                title=self.title,
                border_style=self.color_scheme,
                title_align="center",
            )
        )

    async def prompt(self, message: str = "SELECT OPTION") -> str:
        """Get user input"""
        try:
            prompt_text_str = str(Text(f"\n{message} > ", style=self.color_scheme))
            with self.console.status("[bold green]Waiting for input...") as status:
                if aioconsole:
                    user_input = await aioconsole.ainput(prompt_text_str)
                else:
                    user_input = self.console.input(prompt_text_str)
            return user_input.strip().upper()
        except (EOFError, KeyboardInterrupt):
            return "0"

    def display_table(self, headers: List[str], rows: List[List[str]], title: str = ""):
        """Display a table"""
        table = Table(title=title, border_style=self.color_scheme)
        for header in headers:
            table.add_column(header, style=self.color_scheme)
        for row in rows:
            table.add_row(*row)
        self.console.print(table)

    def display_box(self, title: str, content: List[str]):
        """Display content in a box"""
        content_text = "\n".join(content)
        self.console.print(
            Panel(content_text, title=title, border_style=self.color_scheme)
        )

    def display_info(self, message: str):
        self.console.print(Text(f"[ℹ] {message}", style="cyan"))

    def display_success(self, message: str):
        self.console.print(Text(f"[✓] {message}", style="green"))

    def display_error(self, message: str):
        self.console.print(Text(f"[✗] {message}", style="red"))

    def display_warning(self, message: str):
        self.console.print(Text(f"[⚠] {message}", style="yellow"))

    def change_scheme(self, scheme: MenuColorScheme):
        """Change color scheme"""
        self.color_scheme = scheme.value

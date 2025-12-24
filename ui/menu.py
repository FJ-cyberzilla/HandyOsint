#!/usr/bin/env python3
"""
HandyOsint Menu System - Professional Enterprise Edition
Modern, rich-based interactive menu system with full pylint compliance.

This module provides:
- Enterprise-grade menu management
- Professional color schemes with dark orange gradient
- Responsive terminal design
- Rich table and panel displays
- Comprehensive status indicators
- Full async/await support
"""

import asyncio
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Dict, List, Optional

from rich.console import Console
from rich.panel import Panel
from rich.style import Style
from rich.table import Table
from rich.text import Text


@dataclass
class MenuItem:
    """Menu item data structure with validation."""

    key: str
    label: str
    description: str
    icon: str
    action: Optional[Callable] = None

    def __post_init__(self) -> None:
        """Validate menu item properties."""
        if not self.key or not self.label:
            raise ValueError("Menu item key and label cannot be empty")


class MenuColorScheme(Enum):
    """Professional menu color schemes."""

    DARK_ORANGE = "orange1"
    GREEN_PLASMA = "green"
    AMBER_MONO = "yellow"
    COOL_BLUE = "blue"
    MONOCHROME = "white"


class MenuStatus(Enum):
    """Menu operation status indicators."""

    INFO = ("ℹ", "cyan")
    SUCCESS = ("✓", "green")
    ERROR = ("✗", "red")
    WARNING = ("⚠", "yellow")
    PROCESSING = ("◆", "orange1")


class MenuBuilder:
    """Builder for menu item configuration."""

    def __init__(self, key: str, label: str) -> None:
        """Initialize menu builder."""
        self.key = key
        self.label = label
        self.description = ""
        self.icon = "►"
        self.action: Optional[Callable] = None

    def with_description(self, description: str) -> "MenuBuilder":
        """Set item description."""
        self.description = description
        return self

    def with_icon(self, icon: str) -> "MenuBuilder":
        """Set item icon."""
        self.icon = icon
        return self

    def with_action(self, action: Callable) -> "MenuBuilder":
        """Set item action."""
        self.action = action
        return self

    def build(self) -> MenuItem:
        """Build menu item."""
        return MenuItem(
            key=self.key.upper(),
            label=self.label,
            description=self.description,
            icon=self.icon,
            action=self.action,
        )


class MenuRenderer:
    """Handles all menu rendering operations."""

    def __init__(self, console: Console, color_scheme: str) -> None:
        """Initialize menu renderer."""
        self.console = console
        self.color_scheme = color_scheme
        self._style_cache: Dict[str, Style] = {}

    def _get_style(self, color: str) -> Style:
        """Get or create cached style."""
        if color not in self._style_cache:
            self._style_cache[color] = Style(color=color)
        return self._style_cache[color]

    def render_menu_items(self, items: Dict[str, MenuItem]) -> Table:
        """Render menu items as formatted table grid."""
        menu_grid = Table.grid(expand=True, padding=(0, 2))
        menu_grid.add_column(style=self.color_scheme)

        for item in items.values():
            key_text = Text(f"[{item.key}]", style=self.color_scheme, no_wrap=True)
            icon_text = Text(f"{item.icon}", style=self.color_scheme)
            label_text = Text(f"{item.label}", style=self.color_scheme)
            desc_text = Text(f"{item.description}", style="dim")

            row_content = Text()
            row_content.append_text(key_text)
            row_content.append(" ")
            row_content.append_text(icon_text)
            row_content.append(" ")
            row_content.append_text(label_text)
            row_content.append("\n")
            row_content.append_text(desc_text)

            menu_grid.add_row(row_content)

        return menu_grid

    def render_info_panel(self, title: str, content: str) -> Panel:
        """Render information panel."""
        panel = Panel(
            content,
            title=title,
            border_style=self.color_scheme,
            title_align="center",
            padding=(1, 2),
        )
        return panel

    def render_data_table(
        self, headers: List[str], rows: List[List[str]], title: str = ""
    ) -> Table:
        """Render data table with responsive columns."""
        table = Table(
            title=title,
            border_style=self.color_scheme,
            show_header=True,
            header_style=self._get_style(self.color_scheme),
        )

        for header in headers:
            table.add_column(header, style=self.color_scheme)

        for row in rows:
            table.add_row(*row)

        return table

    def render_status_message(self, status: MenuStatus, message: str) -> Text:
        """Render status message with icon."""
        icon, color = status.value
        text = Text()
        text.append(f"[{icon}] ", style=color)
        text.append(message, style=color)
        return text


class MenuInputHandler:
    """Handles user input and validation."""

    def __init__(self, console: Console, color_scheme: str) -> None:
        """Initialize input handler."""
        self.console = console
        self.color_scheme = color_scheme
        self.valid_inputs: set = set()

    def set_valid_inputs(self, inputs: List[str]) -> None:
        """Set valid input options."""
        self.valid_inputs = {inp.upper() for inp in inputs}

    def prompt_selection(self, message: str = "SELECT OPTION") -> str:
        """Get validated user selection."""
        try:
            prompt_style = Style(color=self.color_scheme)
            prompt_text = Text(f"\n{message} > ", style=prompt_style)
            user_input = self.console.input(prompt_text)
            return user_input.strip().upper()
        except (EOFError, KeyboardInterrupt):
            return "0"

    def prompt_text(self, prompt_msg: str, allow_empty: bool = False) -> str:
        """Get text input with optional validation."""
        try:
            prompt_style = Style(color=self.color_scheme)
            prompt_text = Text(f"{prompt_msg} > ", style=prompt_style)
            user_input = self.console.input(prompt_text)
            result = user_input.strip()

            if not result and not allow_empty:
                raise ValueError("Input cannot be empty")

            return result
        except (EOFError, KeyboardInterrupt):
            return ""

    def validate_input(self, user_input: str) -> bool:
        """Validate input against allowed options."""
        return user_input in self.valid_inputs


class Menu:
    """Enterprise-grade professional menu system."""

    def __init__(
        self,
        title: str = "COMMAND CENTER",
        color_scheme: MenuColorScheme = MenuColorScheme.DARK_ORANGE,
    ) -> None:
        """Initialize menu system with professional configuration."""
        self.title = title
        self.color_scheme = color_scheme.value
        self.items: Dict[str, MenuItem] = {}
        self.console = Console()
        self.renderer = MenuRenderer(self.console, self.color_scheme)
        self.input_handler = MenuInputHandler(self.console, self.color_scheme)
        self._history: List[str] = []

    def add_item(  # pylint: disable=R0913,R0917
        self,
        key: str,
        label: str,
        description: str = "",
        icon: str = "►",
        action: Optional[Callable] = None,
    ) -> None:
        """Add menu item with validation."""
        if key in self.items:
            raise ValueError(f"Menu item with key '{key}' already exists")

        try:
            builder = MenuBuilder(key, label)
            builder.with_description(description)
            builder.with_icon(icon)
            if action:
                builder.with_action(action)
            item = builder.build()
            self.items[item.key] = item
        except ValueError as exc:
            self.display_error(f"Failed to add menu item: {str(exc)}")

    def remove_item(self, key: str) -> bool:
        """Remove menu item by key."""
        key_upper = key.upper()
        if key_upper in self.items:
            del self.items[key_upper]
            return True
        return False

    def get_item(self, key: str) -> Optional[MenuItem]:
        """Retrieve menu item by key."""
        return self.items.get(key.upper())

    def display(self) -> None:
        """Display the menu interface."""
        menu_content = self.renderer.render_menu_items(self.items)
        panel = Panel(
            menu_content,
            title=self.title,
            border_style=self.color_scheme,
            title_align="center",
            padding=(1, 2),
        )
        self.console.print(panel)
        self.input_handler.set_valid_inputs(self.items.keys())

    def display_table(
        self, headers: List[str], rows: List[List[str]], title: str = ""
    ) -> None:
        """Display data table."""
        table = self.renderer.render_data_table(headers, rows, title)
        self.console.print(table)
        self._add_to_history(f"Table displayed: {title}")

    def display_panel(self, title: str, content: str) -> None:
        """Display content panel."""
        panel = self.renderer.render_info_panel(title, content)
        self.console.print(panel)
        self._add_to_history(f"Panel displayed: {title}")

    def display_info(self, message: str) -> None:
        """Display info message."""
        status_text = self.renderer.render_status_message(MenuStatus.INFO, message)
        self.console.print(status_text)
        self._add_to_history(f"Info: {message}")

    def display_success(self, message: str) -> None:
        """Display success message."""
        status_text = self.renderer.render_status_message(MenuStatus.SUCCESS, message)
        self.console.print(status_text)
        self._add_to_history(f"Success: {message}")

    def display_error(self, message: str) -> None:
        """Display error message."""
        status_text = self.renderer.render_status_message(MenuStatus.ERROR, message)
        self.console.print(status_text)
        self._add_to_history(f"Error: {message}")

    def display_warning(self, message: str) -> None:
        """Display warning message."""
        status_text = self.renderer.render_status_message(MenuStatus.WARNING, message)
        self.console.print(status_text)
        self._add_to_history(f"Warning: {message}")

    def display_processing(self, message: str) -> None:
        """Display processing indicator."""
        status_text = self.renderer.render_status_message(
            MenuStatus.PROCESSING, message
        )
        self.console.print(status_text)
        self._add_to_history(f"Processing: {message}")

    def prompt_selection(self, message: str = "SELECT OPTION") -> str:
        """Get user menu selection."""
        selection = self.input_handler.prompt_selection(message)
        self._add_to_history(f"Selection: {selection}")
        return selection

    def prompt_input(self, prompt_msg: str, allow_empty: bool = False) -> str:
        """Get user text input."""
        user_input = self.input_handler.prompt_text(prompt_msg, allow_empty)
        self._add_to_history(f"Input: {prompt_msg}")
        return user_input

    def prompt_confirm(self, prompt_msg: str = "Continue?") -> bool:
        """Get user confirmation."""
        response = self.input_handler.prompt_text(
            f"{prompt_msg} (Y/N)", allow_empty=False
        )
        result = response.upper() in ("Y", "YES")
        self._add_to_history(f"Confirm: {prompt_msg} -> {result}")
        return result

    def change_scheme(self, scheme: MenuColorScheme) -> None:
        """Change color scheme dynamically."""
        self.color_scheme = scheme.value
        self.renderer = MenuRenderer(self.console, self.color_scheme)
        self.input_handler = MenuInputHandler(self.console, self.color_scheme)
        self._add_to_history(f"Color scheme changed to: {scheme.name}")

    def execute_action(self, key: str) -> bool:
        """Execute menu item action."""
        item = self.get_item(key)
        if not item:
            self.display_error(f"Menu item '{key}' not found")
            return False

        if not item.action:
            self.display_warning(f"Menu item '{item.label}' has no action")
            return False

        try:
            if asyncio.iscoroutinefunction(item.action):
                asyncio.run(item.action())
            else:
                item.action()
            self._add_to_history(f"Action executed: {item.label}")
            return True
        except (asyncio.CancelledError, KeyboardInterrupt) as exc:
            self.display_error(f"Action interrupted: {str(exc)}")
            self._add_to_history(f"Action interrupted: {item.label}")
            return False

    def clear_screen(self) -> None:
        """Clear console screen."""
        self.console.clear()

    def get_history(self) -> List[str]:
        """Get operation history."""
        return self._history.copy()

    def _add_to_history(self, entry: str) -> None:
        """Add entry to operation history."""
        self._history.append(entry)
        max_history = 50
        if len(self._history) > max_history:
            self._history.pop(0)

    def display_history(self, limit: int = 10) -> None:
        """Display recent operation history."""
        recent = self._history[-limit:]
        history_text = "\n".join(recent) if recent else "No history available"
        self.display_panel("Operation History", history_text)


async def demo_menu() -> None:
    """Demonstrate menu system functionality."""
    menu = Menu(
        title="OSINT INTELLIGENCE PLATFORM", color_scheme=MenuColorScheme.DARK_ORANGE
    )

    menu.add_item("1", "Network Scanner", "Scan and analyze network targets", icon="🔍")
    menu.add_item(
        "2", "Domain Lookup", "Perform comprehensive domain analysis", icon="🌐"
    )
    menu.add_item(
        "3", "Data Extraction", "Extract and process intelligence data", icon="📊"
    )
    menu.add_item("4", "Report Generator", "Generate professional reports", icon="📄")
    menu.add_item("0", "Exit", "Close application", icon="⏻")

    menu.clear_screen()
    menu.display()

    menu.display_success("System initialized successfully")
    menu.display_info("Ready to process intelligence operations")

    sample_data = [
        ["192.168.1.1", "Gateway", "Active"],
        ["192.168.1.100", "Workstation", "Active"],
        ["192.168.1.101", "Server", "Inactive"],
    ]
    menu.display_table(
        ["IP Address", "Device Type", "Status"], sample_data, title="Network Devices"
    )

    menu.display_processing("Performing reconnaissance scan...")
    menu.display_warning("Elevated privilege level required")
    menu.display_error("Connection timeout on target host")

    menu.display_history(limit=5)


def main() -> None:
    """Main entry point."""
    asyncio.run(demo_menu())


if __name__ == "__main__":
    main()

"""
HandyOsint - Vintage 16-bit UI Module
A modular user interface system with retro aesthetics
"""

from .banner import Banner
from .banner import BannerColorScheme
from .menu import Menu, MenuColorScheme
from .terminal import Terminal, TerminalColorScheme

__all__ = [
    "Banner",
    "BannerColorScheme",
    "Menu",
    "MenuColorScheme",
    "Terminal",
    "TerminalColorScheme",
]

__version__ = "2.4.0"
__author__ = "Cyberzilla Security"
__description__ = "Vintage 16-bit UI components for HandyOsint Command Center"

# Initialize default color scheme
COLOR_SCHEMES = {
    "16bit_green": {
        "primary": "\033[92m",  # Bright Green
        "secondary": "\033[32m",  # Green
        "highlight": "\033[93m",  # Amber/Yellow
        "error": "\033[91m",  # Red
        "info": "\033[96m",  # Cyan
        "reset": "\033[0m",
        "bold": "\033[1m",
        "dim": "\033[2m",
    },
    "amber_mono": {
        "primary": "\033[93m",  # Amber
        "secondary": "\033[33m",  # Brown
        "highlight": "\033[92m",  # Green
        "error": "\033[91m",  # Red
        "info": "\033[96m",  # Cyan
        "reset": "\033[0m",
        "bold": "\033[1m",
        "dim": "\033[2m",
    },
}


def get_color_scheme(name="16bit_green"):
    """Get a predefined color scheme"""
    return COLOR_SCHEMES.get(name, COLOR_SCHEMES["16bit_green"])


def print_colored(text, color_code="92", end="\n"):
    """Quick colored print utility"""
    print(f"\033[{color_code}m{text}\033[0m", end=end)


def demo_ui():
    """Demo the UI components"""
    print("=" * 60)
    print("HANDYOSINT UI MODULE DEMO")
    print("=" * 60)

    # Test colors
    schemes = ["16bit_green", "amber_mono"]
    for scheme in schemes:
        colors = get_color_scheme(scheme)
        print(f"\n{colors['bold']}{scheme.upper()} SCHEME:{colors['reset']}")
        print(f"{colors['primary']}Primary Text{colors['reset']}")
        print(f"{colors['secondary']}Secondary Text{colors['reset']}")
        print(f"{colors['highlight']}Highlight Text{colors['reset']}")
        print(f"{colors['error']}Error Text{colors['reset']}")
        print(f"{colors['info']}Info Text{colors['reset']}")

    print("\n" + "=" * 60)
    print("UI Module Ready!")
    print("=" * 60)


if __name__ == "__main__":
    demo_ui()

"""
Termux-compatible system monitoring
Fallback for psutil restrictions on Android/Termux
"""

import os
import sys
from typing import Any, Dict

import psutil  # Moved to top


class TermuxMonitor:
    """Lightweight system monitoring for Termux"""

    @staticmethod
    def cpu_usage() -> float:
        """Get CPU usage percentage (simplified for Termux)"""
        try:
            return psutil.cpu_percent(interval=0.1)
        except psutil.Error:  # Catch psutil specific errors
            # Fallback to reading /proc/stat if accessible
            try:
                with open("/proc/stat", "r", encoding="utf-8") as f:  # Added encoding
                    lines = f.readlines()
                for line in lines:
                    if line.startswith("cpu "):
                        parts = line.split()
                        # Simple calculation
                        total = sum(int(p) for p in parts[1:])
                        idle = int(parts[4])
                        return 100.0 * (1.0 - idle / total) if total > 0 else 0.0
            except (FileNotFoundError, IndexError, ValueError):  # Specific fallbacks
                pass
            return 50.0  # Default fallback

    @staticmethod
    def memory_usage() -> Dict[str, Any]:
        """Get memory usage information"""
        try:
            mem = psutil.virtual_memory()
            return {
                "percent": mem.percent,
                "total": mem.total,
                "available": mem.available,
                "used": mem.used,
            }
        except psutil.Error:  # Catch psutil specific errors
            # Fallback for Termux
            try:
                with open(
                    "/proc/meminfo", "r", encoding="utf-8"
                ) as f:  # Added encoding
                    lines = f.readlines()
                meminfo = {}
                for line in lines:
                    if ":" in line:
                        key, value = line.split(":", 1)
                        meminfo[key.strip()] = value.strip()

                total = int(meminfo.get("MemTotal", "0 kB").split()[0]) * 1024
                available = int(meminfo.get("MemAvailable", "0 kB").split()[0]) * 1024

                if total > 0:
                    percent = 100.0 * (total - available) / total
                else:
                    percent = 0.0

                return {
                    "percent": percent,
                    "total": total,
                    "available": available,
                    "used": total - available,
                }
            except (FileNotFoundError, IndexError, ValueError):  # Specific fallbacks
                return {"percent": 0.0, "total": 0, "available": 0, "used": 0}

    @staticmethod
    def disk_usage(path: str = ".") -> Dict[str, Any]:
        """Get disk usage information"""
        try:
            disk = psutil.disk_usage(path)
            return {
                "percent": disk.percent,
                "total": disk.total,
                "used": disk.used,
                "free": disk.free,
            }
        except psutil.Error:  # Catch psutil specific errors
            # Fallback using os.statvfs
            try:
                stat = os.statvfs(path)
                total = stat.f_blocks * stat.f_frsize
                free = stat.f_bfree * stat.f_frsize
                used = total - free

                if total > 0:
                    percent = 100.0 * used / total
                else:
                    percent = 0.0

                return {"percent": percent, "total": total, "used": used, "free": free}
            except (FileNotFoundError, OSError):  # Specific fallbacks
                return {"percent": 0.0, "total": 0, "used": 0, "free": 0}

    @staticmethod
    def get_system_info() -> Dict[str, Any]:
        """Get comprehensive system information"""
        return {
            "cpu_percent": TermuxMonitor.cpu_usage(),
            "memory": TermuxMonitor.memory_usage(),
            "disk": TermuxMonitor.disk_usage("."),
            "platform": sys.platform,
            "python_version": sys.version,
            "termux": "termux" in os.environ.get("PREFIX", ""),
        }


# Test function
if __name__ == "__main__":
    monitor = TermuxMonitor()
    info = monitor.get_system_info()
    print(f"CPU: {info['cpu_percent']:.1f}%")
    print(f"Memory: {info['memory']['percent']:.1f}%")
    print(f"Disk: {info['disk']['percent']:.1f}%")
    print(f"Platform: {info['platform']}")
    print(f"Termux: {info['termux']}")

"""
Data models for HandyOsint.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
import hashlib


class RiskLevel(Enum):
    """Risk assessment levels."""
    LOW = ("🟢 LOW", "green", 1)
    MEDIUM = ("🟡 MEDIUM", "yellow", 2)
    HIGH = ("🔴 HIGH", "red", 3)
    CRITICAL = ("⚫ CRITICAL", "bold red", 4)

    def __init__(self, label: str, color: str, score: int) -> None:
        self.label = label
        self.color = color
        self.score = score


class ProfileStatus(Enum):
    """Profile discovery status."""
    FOUND = "✓ FOUND"
    NOT_FOUND = "✗ NOT FOUND"
    BLOCKED = "⊘ BLOCKED"
    ERROR = "⚠ ERROR"
    PENDING = "⟳ PENDING"
    TIMEOUT = "⏱ TIMEOUT"


class AuditAction(Enum):
    """Audit trail actions."""
    SCAN_START = "SCAN_START"
    SCAN_COMPLETE = "SCAN_COMPLETE"
    PROFILE_FOUND = "PROFILE_FOUND"
    PROFILE_NOT_FOUND = "PROFILE_NOT_FOUND"
    RISK_ASSESSED = "RISK_ASSESSED"
    REPORT_GENERATED = "REPORT_GENERATED"
    EXPORT_PERFORMED = "EXPORT_PERFORMED"


@dataclass
class PlatformResult:  # pylint: disable=too-many-instance-attributes
    """Result for a single platform scan."""

    platform_id: str
    platform_name: str
    found: bool
    url: str
    status: str = "pending"
    status_code: int = 0
    response_time: float = 0.0
    error: Optional[str] = None
    timestamp: str = ""
    content_length: int = 0
    content_preview: str = ""
    headers: Dict[str, str] = field(default_factory=dict)
    risk_indicators: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Initialize with defaults."""
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "platform_id": self.platform_id,
            "platform_name": self.platform_name,
            "found": self.found,
            "url": self.url,
            "status": self.status,
            "status_code": self.status_code,
            "response_time": round(self.response_time, 2),
            "error": self.error,
            "timestamp": self.timestamp,
            "content_length": self.content_length,
            "content_preview": self.content_preview,
        }


@dataclass
class CorrelationData:
    """Correlation analysis results."""

    username: str
    common_patterns: List[str] = field(default_factory=list)
    likely_connections: Dict[str, List[str]] = field(default_factory=dict)
    behavioral_fingerprint: Dict[str, Any] = field(default_factory=dict)
    anomalies: List[str] = field(default_factory=list)
    confidence_score: float = 0.0


@dataclass
class ScanAnalysis:  # pylint: disable=too-many-instance-attributes
    """Complete scan analysis."""

    username: str
    scan_id: str
    timestamp: str
    total_platforms: int = 0
    profiles_found: int = 0
    scan_duration: float = 0.0
    risk_level: str = ""
    overall_risk_score: float = 0.0
    platforms: Dict[str, PlatformResult] = field(default_factory=dict)
    correlation_data: Optional[CorrelationData] = None
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Initialize defaults."""
        if not self.scan_id:
            self.scan_id = hashlib.sha256(
                f"{self.username}{self.timestamp}".encode()
            ).hexdigest()[:12]


@dataclass
class AuditLogEntry:
    """Audit trail entry."""

    timestamp: str
    action: str
    username: str
    scan_id: str
    details: Dict[str, Any] = field(default_factory=dict)
    status: str = "success"
    error_message: Optional[str] = None

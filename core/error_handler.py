#!/usr/bin/env python3
"""
HandyOsint Error Handler - Enterprise Error Management System
Comprehensive exception handling, logging, and recovery strategies
"""

import logging
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Callable, Any, Optional, Tuple, Dict, List
from enum import Enum
from functools import wraps
import json


# ============================================================================
# EXCEPTION HIERARCHY
# ============================================================================


class HandyOsintException(Exception):
    """Base exception for HandyOsint"""

    def __init__(
        self, message: str, error_code: str = "UNKNOWN", details: Optional[Dict] = None
    ):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.timestamp = datetime.now().isoformat()
        super().__init__(self.message)


class ValidationError(HandyOsintException):
    """Input validation failures"""

    def __init__(self, message: str, field: str = "", details: Optional[Dict] = None):
        super().__init__(message, "VALIDATION_ERROR", details or {})
        self.field = field


class DatabaseError(HandyOsintException):
    """Database operation failures"""

    def __init__(
        self, message: str, operation: str = "", details: Optional[Dict] = None
    ):
        super().__init__(message, "DATABASE_ERROR", details or {})
        self.operation = operation


class NetworkError(HandyOsintException):
    """Network operation failures"""

    def __init__(
        self,
        message: str,
        url: str = "",
        status_code: int = 0,
        details: Optional[Dict] = None,
    ):
        super().__init__(message, "NETWORK_ERROR", details or {})
        self.url = url
        self.status_code = status_code


class ScanError(HandyOsintException):
    """Scanning operation failures"""

    def __init__(
        self,
        message: str,
        target: str = "",
        platform: str = "",
        details: Optional[Dict] = None,
    ):
        super().__init__(message, "SCAN_ERROR", details or {})
        self.target = target
        self.platform = platform


class ConfigurationError(HandyOsintException):
    """Configuration issues"""

    def __init__(
        self, message: str, config_key: str = "", details: Optional[Dict] = None
    ):
        super().__init__(message, "CONFIG_ERROR", details or {})
        self.config_key = config_key


class TimeoutError(HandyOsintException):
    """Operation timeout"""

    def __init__(
        self, message: str, timeout_seconds: float = 0, details: Optional[Dict] = None
    ):
        super().__init__(message, "TIMEOUT_ERROR", details or {})
        self.timeout_seconds = timeout_seconds


class RateLimitError(HandyOsintException):
    """Rate limiting exceeded"""

    def __init__(
        self,
        message: str,
        platform: str = "",
        retry_after: int = 0,
        details: Optional[Dict] = None,
    ):
        super().__init__(message, "RATE_LIMIT_ERROR", details or {})
        self.platform = platform
        self.retry_after = retry_after


# ============================================================================
# ERROR SEVERITY & RECOVERY
# ============================================================================


class ErrorSeverity(Enum):
    """Error severity levels"""

    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"
    FATAL = "FATAL"


class RecoveryStrategy(Enum):
    """Error recovery strategies"""

    RETRY = "retry"
    FALLBACK = "fallback"
    IGNORE = "ignore"
    ABORT = "abort"
    USER_INPUT = "user_input"


# ============================================================================
# ERROR LOG ENTRY
# ============================================================================


class ErrorLogEntry:
    """Single error log entry"""

    def __init__(
        self,
        exception: Exception,
        severity: ErrorSeverity,
        context: Optional[Dict] = None,
        recovery: RecoveryStrategy = RecoveryStrategy.ABORT,
    ):
        self.timestamp = datetime.now().isoformat()
        self.exception_type = type(exception).__name__
        self.message = str(exception)
        self.severity = severity.value
        self.context = context or {}
        self.recovery = recovery.value
        self.traceback = traceback.format_exc()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "timestamp": self.timestamp,
            "exception_type": self.exception_type,
            "message": self.message,
            "severity": self.severity,
            "context": self.context,
            "recovery": self.recovery,
            "traceback": self.traceback,
        }

    def to_json(self) -> str:
        """Convert to JSON"""
        return json.dumps(self.to_dict(), indent=2)


# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================


class LoggerFactory:
    """Create and configure loggers"""

    _loggers: Dict[str, logging.Logger] = {}

    @staticmethod
    def get_logger(name: str, log_file: Optional[Path] = None) -> logging.Logger:
        """Get or create logger"""
        if name in LoggerFactory._loggers:
            return LoggerFactory._loggers[name]

        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)

        # Clear existing handlers
        logger.handlers.clear()

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

        # File handler
        if log_file:
            log_file.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.DEBUG)
            file_formatter = logging.Formatter(
                "[%(asctime)s] %(levelname)s - %(name)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)

        LoggerFactory._loggers[name] = logger
        return logger


# ============================================================================
# MAIN ERROR HANDLER
# ============================================================================


class ErrorHandler:
    """Enterprise error handling system"""

    def __init__(self, log_dir: Path = Path("logs")):
        """Initialize error handler"""
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Setup loggers
        self.logger = LoggerFactory.get_logger(
            "HandyOsint", self.log_dir / "handyosint.log"
        )
        self.error_logger = LoggerFactory.get_logger(
            "HandyOsintErrors", self.log_dir / "errors.log"
        )

        # Error history
        self.error_history: List[ErrorLogEntry] = []
        self.max_history = 1000

        self.logger.info("ErrorHandler initialized")

    # ========================================================================
    # ERROR HANDLING METHODS
    # ========================================================================

    def handle_exception(
        self,
        exception: Exception,
        context: Optional[Dict] = None,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        recovery: RecoveryStrategy = RecoveryStrategy.ABORT,
    ) -> ErrorLogEntry:
        """Handle exception with context"""

        entry = ErrorLogEntry(exception, severity, context, recovery)
        self.error_history.append(entry)

        # Trim history
        if len(self.error_history) > self.max_history:
            self.error_history = self.error_history[-self.max_history :]

        # Log based on severity
        if severity == ErrorSeverity.INFO:
            self.logger.info(entry.message)
        elif severity == ErrorSeverity.WARNING:
            self.logger.warning(entry.message)
        elif severity == ErrorSeverity.ERROR:
            self.error_logger.error(f"{entry.exception_type}: {entry.message}")
        elif severity == ErrorSeverity.CRITICAL:
            self.error_logger.critical(f"{entry.exception_type}: {entry.message}")
        elif severity == ErrorSeverity.FATAL:
            self.error_logger.critical(
                f"FATAL: {entry.exception_type}: {entry.message}"
            )

        return entry

    def handle_validation_error(
        self, message: str, field: str = "", context: Optional[Dict] = None
    ) -> ErrorLogEntry:
        """Handle validation error"""
        exc = ValidationError(message, field, context)
        return self.handle_exception(
            exc, context, ErrorSeverity.WARNING, RecoveryStrategy.USER_INPUT
        )

    def handle_database_error(
        self, message: str, operation: str = "", context: Optional[Dict] = None
    ) -> ErrorLogEntry:
        """Handle database error"""
        exc = DatabaseError(message, operation, context)
        return self.handle_exception(
            exc, context, ErrorSeverity.ERROR, RecoveryStrategy.RETRY
        )

    def handle_network_error(
        self,
        message: str,
        url: str = "",
        status_code: int = 0,
        context: Optional[Dict] = None,
    ) -> ErrorLogEntry:
        """Handle network error"""
        exc = NetworkError(message, url, status_code, context)
        return self.handle_exception(
            exc, context, ErrorSeverity.WARNING, RecoveryStrategy.RETRY
        )

    def handle_scan_error(
        self,
        message: str,
        target: str = "",
        platform: str = "",
        context: Optional[Dict] = None,
    ) -> ErrorLogEntry:
        """Handle scan error"""
        exc = ScanError(message, target, platform, context)
        return self.handle_exception(
            exc, context, ErrorSeverity.WARNING, RecoveryStrategy.FALLBACK
        )

    def handle_timeout_error(
        self, message: str, timeout_seconds: float = 0, context: Optional[Dict] = None
    ) -> ErrorLogEntry:
        """Handle timeout error"""
        exc = TimeoutError(message, timeout_seconds, context)
        return self.handle_exception(
            exc, context, ErrorSeverity.WARNING, RecoveryStrategy.RETRY
        )

    def handle_rate_limit(
        self,
        message: str,
        platform: str = "",
        retry_after: int = 0,
        context: Optional[Dict] = None,
    ) -> ErrorLogEntry:
        """Handle rate limiting"""
        exc = RateLimitError(message, platform, retry_after, context)
        return self.handle_exception(
            exc, context, ErrorSeverity.WARNING, RecoveryStrategy.RETRY
        )

    # ========================================================================
    # DECORATOR SUPPORT
    # ========================================================================

    def safe_call(
        self, func: Callable, *args, **kwargs
    ) -> Tuple[bool, Any, Optional[str]]:
        """Safe function call wrapper"""
        try:
            result = func(*args, **kwargs)
            self.logger.info(f"Successfully executed: {func.__name__}")
            return True, result, None
        except Exception as e:
            entry = self.handle_exception(e, {"function": func.__name__})
            return False, None, entry.message

    def try_except(self, default_return: Any = None):
        """Decorator for safe execution with fallback"""

        def decorator(func: Callable):
            @wraps(func)
            def wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    self.handle_exception(
                        e,
                        {"function": func.__name__},
                        ErrorSeverity.ERROR,
                        RecoveryStrategy.FALLBACK,
                    )
                    return default_return

            return wrapper

        return decorator

    def with_retry(self, max_retries: int = 3, delay: float = 1.0):
        """Decorator for automatic retry on exception"""

        def decorator(func: Callable):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                import asyncio

                for attempt in range(max_retries):
                    try:
                        return await func(*args, **kwargs)
                    except Exception as e:
                        if attempt < max_retries - 1:
                            self.logger.warning(
                                f"Attempt {attempt + 1} failed, retrying in {delay}s..."
                            )
                            await asyncio.sleep(delay)
                        else:
                            self.handle_exception(
                                e, {"function": func.__name__, "attempts": max_retries}
                            )
                            raise

            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                import time

                for attempt in range(max_retries):
                    try:
                        return func(*args, **kwargs)
                    except Exception as e:
                        if attempt < max_retries - 1:
                            self.logger.warning(
                                f"Attempt {attempt + 1} failed, retrying in {delay}s..."
                            )
                            time.sleep(delay)
                        else:
                            self.handle_exception(
                                e, {"function": func.__name__, "attempts": max_retries}
                            )
                            raise

            # Return async or sync wrapper based on function
            import asyncio

            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            return sync_wrapper

        return decorator

    # ========================================================================
    # LOGGING METHODS
    # ========================================================================

    def log_info(self, message: str, context: Optional[Dict] = None) -> None:
        """Log info message"""
        if context:
            message = f"{message} | {json.dumps(context)}"
        self.logger.info(message)

    def log_warning(self, message: str, context: Optional[Dict] = None) -> None:
        """Log warning message"""
        if context:
            message = f"{message} | {json.dumps(context)}"
        self.logger.warning(message)

    def log_error(self, message: str, context: Optional[Dict] = None) -> None:
        """Log error message"""
        if context:
            message = f"{message} | {json.dumps(context)}"
        self.error_logger.error(message)

    def log_critical(self, message: str, context: Optional[Dict] = None) -> None:
        """Log critical message"""
        if context:
            message = f"{message} | {json.dumps(context)}"
        self.error_logger.critical(message)

    def log_operation(
        self,
        operation: str,
        status: str,
        duration: Optional[float] = None,
        details: Optional[Dict] = None,
    ) -> None:
        """Log operation with status"""
        message = f"[{operation}] {status}"
        if duration is not None:
            message += f" ({duration:.2f}s)"
        if details:
            message += f" | {json.dumps(details)}"
        self.logger.info(message)

    # ========================================================================
    # ERROR HISTORY & REPORTING
    # ========================================================================

    def get_error_history(self, limit: int = 50) -> List[Dict]:
        """Get error history"""
        return [entry.to_dict() for entry in self.error_history[-limit:]]

    def get_error_summary(self) -> Dict[str, Any]:
        """Get summary of errors"""
        summary = {
            "total_errors": len(self.error_history),
            "by_severity": {},
            "by_type": {},
            "recent": [],
        }

        # Count by severity
        for entry in self.error_history:
            severity = entry.severity
            summary["by_severity"][severity] = (
                summary["by_severity"].get(severity, 0) + 1
            )

            exc_type = entry.exception_type
            summary["by_type"][exc_type] = summary["by_type"].get(exc_type, 0) + 1

        # Recent errors
        summary["recent"] = [entry.to_dict() for entry in self.error_history[-5:]]

        return summary

    def export_error_log(self, filename: Path) -> bool:
        """Export error log to file"""
        try:
            with open(filename, "w") as f:
                json.dump(
                    [entry.to_dict() for entry in self.error_history], f, indent=2
                )
            self.logger.info(f"Error log exported to {filename}")
            return True
        except Exception as e:
            self.handle_exception(e, {"filename": str(filename)})
            return False

    def clear_history(self) -> None:
        """Clear error history"""
        self.error_history.clear()
        self.logger.info("Error history cleared")

    # ========================================================================
    # UTILITY METHODS
    # ========================================================================

    def get_last_error(self) -> Optional[ErrorLogEntry]:
        """Get last error"""
        return self.error_history[-1] if self.error_history else None

    def has_errors(self) -> bool:
        """Check if any errors have occurred"""
        return len(self.error_history) > 0

    def get_error_count(self, severity: Optional[ErrorSeverity] = None) -> int:
        """Get count of errors by severity"""
        if severity is None:
            return len(self.error_history)

        return sum(
            1 for entry in self.error_history if entry.severity == severity.value
        )

    def format_error_message(self, exception: Exception, verbose: bool = False) -> str:
        """Format error message for display"""
        message = f"❌ {type(exception).__name__}: {str(exception)}"

        if verbose and isinstance(exception, HandyOsintException):
            message += f"\n   Error Code: {exception.error_code}"
            message += f"\n   Timestamp: {exception.timestamp}"
            if exception.details:
                message += f"\n   Details: {json.dumps(exception.details)}"

        return message


# ============================================================================
# GLOBAL ERROR HANDLER INSTANCE
# ============================================================================

_global_error_handler: Optional[ErrorHandler] = None


def get_error_handler(log_dir: Path = Path("logs")) -> ErrorHandler:
    """Get or create global error handler"""
    global _global_error_handler
    if _global_error_handler is None:
        _global_error_handler = ErrorHandler(log_dir)
    return _global_error_handler


# ============================================================================
# DEMO & TESTING
# ============================================================================

if __name__ == "__main__":
    # Setup logging for demo
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)

    # Create error handler
    error_handler = ErrorHandler()

    print("\n" + "=" * 70)
    print("ErrorHandler - Demonstration")
    print("=" * 70 + "\n")

    # Test 1: Log info
    print("✓ Test 1: Info logging")
    error_handler.log_info("System initialized", {"version": "3.0.0"})

    # Test 2: Validation error
    print("✓ Test 2: Validation error")
    error_handler.handle_validation_error(
        "Username too short", field="username", context={"provided": "ab", "minimum": 3}
    )

    # Test 3: Network error
    print("✓ Test 3: Network error")
    error_handler.handle_network_error(
        "Failed to connect", url="https://github.com/invalid", status_code=404
    )

    # Test 4: Scan error
    print("✓ Test 4: Scan error")
    error_handler.handle_scan_error(
        "Timeout during scan", target="testuser", platform="github"
    )

    # Test 5: Rate limit
    print("✓ Test 5: Rate limit error")
    error_handler.handle_rate_limit(
        "Too many requests", platform="twitter", retry_after=60
    )

    # Test 6: Error summary
    print("\n✓ Test 6: Error summary")
    summary = error_handler.get_error_summary()
    print(f"   Total errors: {summary['total_errors']}")
    print(f"   By severity: {summary['by_severity']}")
    print(f"   By type: {summary['by_type']}")

    # Test 7: Decorator
    @error_handler.try_except(default_return="Unknown")
    def risky_function():
        raise ValueError("Something went wrong!")

    print("\n✓ Test 7: Decorator test")
    result = risky_function()
    print(f"   Result: {result}")

    print("\n" + "=" * 70)
    print("All tests completed!")
    print("=" * 70 + "\n")

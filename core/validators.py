#!/usr/bin/env python3
"""
HandyOsint Validation System - Enterprise Input & Data Validation.

Comprehensive validation framework for:
- User input validation
- Configuration validation
- Database validation
- Network request validation
- Scan operation validation
- API request validation
"""

import logging
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# ========================================================================
# VALIDATION ENUMS
# ========================================================================


class ValidationLevel(Enum):
    """Validation strictness levels."""

    STRICT = "strict"
    MODERATE = "moderate"
    LENIENT = "lenient"


class ValidationType(Enum):
    """Types of validation."""

    USERNAME = "username"
    URL = "url"
    EMAIL = "email"
    DOMAIN = "domain"
    IP_ADDRESS = "ip_address"
    PORT = "port"
    FILEPATH = "filepath"
    JSON = "json"
    PLATFORM_ID = "platform_id"
    DATABASE_QUERY = "database_query"
    SCAN_TARGET = "scan_target"


# ========================================================================
# VALIDATION RESULT
# ========================================================================


@dataclass
class ValidationResult:
    """Result of validation operation."""

    is_valid: bool
    value: Any
    errors: List[str]
    warnings: List[str]
    validation_type: ValidationType

    def __bool__(self) -> bool:
        """Check if validation passed."""
        return self.is_valid

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "is_valid": self.is_valid,
            "value": self.value,
            "errors": self.errors,
            "warnings": self.warnings,
            "validation_type": self.validation_type.value,
        }


# ========================================================================
# USERNAME VALIDATOR
# ========================================================================


class UsernameValidator:  # pylint: disable=R0903
    """Validate username inputs."""

    MIN_LENGTH = 2
    MAX_LENGTH = 64
    ALLOWED_CHARS = re.compile(r"^[a-zA-Z0-9_.-]+$")
    RESERVED_NAMES = {
        "admin",
        "root",
        "system",
        "test",
        "demo",
        "default",
        "null",
        "none",
        "undefined",
        "admin123",
    }

    @staticmethod
    def validate(
        username: str, level: ValidationLevel = ValidationLevel.MODERATE
    ) -> ValidationResult:
        """Validate username."""
        errors: List[str] = []
        warnings: List[str] = []

        if not username:
            errors.append("Username cannot be empty")
            return ValidationResult(
                False, username, errors, warnings, ValidationType.USERNAME
            )

        username = username.strip()

        if len(username) < UsernameValidator.MIN_LENGTH:
            errors.append(
                f"Username too short (min {UsernameValidator.MIN_LENGTH} chars)"
            )

        if len(username) > UsernameValidator.MAX_LENGTH:
            errors.append(
                f"Username too long (max {UsernameValidator.MAX_LENGTH} chars)"
            )

        if not UsernameValidator.ALLOWED_CHARS.match(username):
            errors.append(
                "Username contains invalid characters. "
                "Use only letters, numbers, underscore, dash, dot"
            )

        if level == ValidationLevel.STRICT:
            if username.lower() in UsernameValidator.RESERVED_NAMES:
                warnings.append("Username is a reserved/common name")
            if username.startswith(("_", "-", ".")):
                warnings.append("Username starts with special character")
            if username.endswith(("_", "-", ".")):
                warnings.append("Username ends with special character")

        return ValidationResult(
            len(errors) == 0, username, errors, warnings, ValidationType.USERNAME
        )


# ========================================================================
# URL VALIDATOR
# ========================================================================


class URLValidator:  # pylint: disable=R0903
    """Validate URLs and network endpoints."""

    URL_PATTERN = re.compile(
        r"^https?://"
        r"(?:(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)*"
        r"[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)"
        r"(?::\d+)?"
        r"(?:/[^\s]*)?"
        r"$",
        re.IGNORECASE,
    )

    MAX_URL_LENGTH = 2048

    @staticmethod
    def validate(url: str) -> ValidationResult:
        """Validate URL."""
        errors: List[str] = []
        warnings: List[str] = []

        if not url:
            errors.append("URL cannot be empty")
            return ValidationResult(False, url, errors, warnings, ValidationType.URL)

        url = url.strip()

        if len(url) > URLValidator.MAX_URL_LENGTH:
            errors.append(f"URL exceeds max length of {URLValidator.MAX_URL_LENGTH}")

        if not URLValidator.URL_PATTERN.match(url):
            errors.append("Invalid URL format")

        if "http://" in url and not url.startswith("http://"):
            warnings.append("URL uses unencrypted HTTP protocol")

        return ValidationResult(
            len(errors) == 0, url, errors, warnings, ValidationType.URL
        )


# ========================================================================
# EMAIL VALIDATOR
# ========================================================================


class EmailValidator:  # pylint: disable=R0903
    """Validate email addresses."""

    EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")

    @staticmethod
    def validate(email: str) -> ValidationResult:
        """Validate email address."""
        errors: List[str] = []
        warnings: List[str] = []

        if not email:
            errors.append("Email cannot be empty")
            return ValidationResult(
                False, email, errors, warnings, ValidationType.EMAIL
            )

        email = email.strip().lower()

        if not EmailValidator.EMAIL_PATTERN.match(email):
            errors.append("Invalid email format")

        if len(email) > 254:
            errors.append("Email exceeds maximum length of 254 characters")

        if email.count("@") != 1:
            errors.append("Email must contain exactly one @ symbol")

        return ValidationResult(
            len(errors) == 0, email, errors, warnings, ValidationType.EMAIL
        )


# ========================================================================
# DOMAIN VALIDATOR
# ========================================================================


class DomainValidator:  # pylint: disable=R0903
    """Validate domain names."""

    DOMAIN_PATTERN = re.compile(
        r"^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)*"
        r"[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?"
        r"$",
        re.IGNORECASE,
    )

    MIN_TLD_LENGTH = 2

    @staticmethod
    def validate(domain: str) -> ValidationResult:
        """Validate domain name."""
        errors: List[str] = []
        warnings: List[str] = []

        if not domain:
            errors.append("Domain cannot be empty")
            return ValidationResult(
                False, domain, errors, warnings, ValidationType.DOMAIN
            )

        domain = domain.strip().lower()

        if domain.startswith(".") or domain.endswith("."):
            errors.append("Domain cannot start or end with dot")

        if ".." in domain:
            errors.append("Domain contains consecutive dots")

        if not DomainValidator.DOMAIN_PATTERN.match(domain):
            errors.append("Invalid domain format")

        parts = domain.split(".")
        if len(parts) < 2:
            errors.append("Domain must have at least one dot")

        if parts[-1] and len(parts[-1]) < DomainValidator.MIN_TLD_LENGTH:
            errors.append(f"TLD too short (min {DomainValidator.MIN_TLD_LENGTH} chars)")

        return ValidationResult(
            len(errors) == 0, domain, errors, warnings, ValidationType.DOMAIN
        )


# ========================================================================
# IP ADDRESS VALIDATOR
# ========================================================================


class IPAddressValidator:  # pylint: disable=R0903
    """Validate IP addresses."""

    IPV4_PATTERN = re.compile(
        r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}"
        r"(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"
    )

    @staticmethod
    def validate(ip_address: str) -> ValidationResult:
        """Validate IP address."""
        errors: List[str] = []
        warnings: List[str] = []

        if not ip_address:
            errors.append("IP address cannot be empty")
            return ValidationResult(
                False, ip_address, errors, warnings, ValidationType.IP_ADDRESS
            )

        ip_address = ip_address.strip()

        if not IPAddressValidator.IPV4_PATTERN.match(ip_address):
            errors.append("Invalid IPv4 address format")

        return ValidationResult(
            len(errors) == 0, ip_address, errors, warnings, ValidationType.IP_ADDRESS
        )


# ========================================================================
# PORT VALIDATOR
# ========================================================================


class PortValidator:  # pylint: disable=R0903
    """Validate network ports."""

    MIN_PORT = 1
    MAX_PORT = 65535
    PRIVILEGED_PORTS = set(range(1, 1024))

    @staticmethod
    def validate(port: Any, warn_privileged: bool = True) -> ValidationResult:
        """Validate network port."""
        errors: List[str] = []
        warnings: List[str] = []

        try:
            if isinstance(port, str):
                port = int(port)
        except (ValueError, TypeError):
            errors.append("Port must be a valid integer")
            return ValidationResult(False, port, errors, warnings, ValidationType.PORT)

        if port < PortValidator.MIN_PORT:
            errors.append(f"Port too low (min {PortValidator.MIN_PORT})")

        if port > PortValidator.MAX_PORT:
            errors.append(f"Port too high (max {PortValidator.MAX_PORT})")

        if warn_privileged and port in PortValidator.PRIVILEGED_PORTS:
            warnings.append("Port is in privileged range (1-1023)")

        return ValidationResult(
            len(errors) == 0, port, errors, warnings, ValidationType.PORT
        )


# ========================================================================
# PLATFORM ID VALIDATOR
# ========================================================================


class PlatformValidator:  # pylint: disable=R0903
    """Validate platform identifiers."""

    VALID_PLATFORMS = {
        "twitter",
        "instagram",
        "tiktok",
        "reddit",
        "linkedin",
        "snapchat",
        "telegram",
        "github",
        "gitlab",
        "stackoverflow",
        "dev_to",
        "codepen",
        "youtube",
        "twitch",
        "medium",
        "pinterest",
        "spotify",
        "patreon",
        "mastodon",
        "bluesky",
        "threads",
    }

    @staticmethod
    def validate(platform_id: str) -> ValidationResult:
        """Validate platform identifier."""
        errors: List[str] = []
        warnings: List[str] = []

        if not platform_id:
            errors.append("Platform ID cannot be empty")
            return ValidationResult(
                False, platform_id, errors, warnings, ValidationType.PLATFORM_ID
            )

        platform_id = platform_id.strip().lower()

        if platform_id not in PlatformValidator.VALID_PLATFORMS:
            errors.append(
                f"Unknown platform. Valid platforms: "
                f"{', '.join(sorted(PlatformValidator.VALID_PLATFORMS))}"
            )

        return ValidationResult(
            len(errors) == 0, platform_id, errors, warnings, ValidationType.PLATFORM_ID
        )


# ========================================================================
# DATABASE QUERY VALIDATOR
# ========================================================================


class DatabaseValidator:  # pylint: disable=R0903
    """Validate database operations."""

    DANGEROUS_KEYWORDS = {"DROP", "DELETE", "TRUNCATE", "ALTER", "EXEC", "EXECUTE"}

    @staticmethod
    def validate_query(query: str) -> ValidationResult:
        """Validate SQL query for safety."""
        errors: List[str] = []
        warnings: List[str] = []

        if not query:
            errors.append("Query cannot be empty")
            return ValidationResult(
                False, query, errors, warnings, ValidationType.DATABASE_QUERY
            )

        query_upper = query.upper().strip()

        for keyword in DatabaseValidator.DANGEROUS_KEYWORDS:
            if keyword in query_upper and not query_upper.startswith("SELECT"):
                errors.append(f"Dangerous SQL keyword detected: {keyword}")

        if "--" in query:
            warnings.append("Query contains SQL comment syntax")

        if ";" in query and not query.rstrip().endswith(";"):
            warnings.append("Query contains multiple statements")

        return ValidationResult(
            len(errors) == 0, query, errors, warnings, ValidationType.DATABASE_QUERY
        )


# ========================================================================
# SCAN TARGET VALIDATOR
# ========================================================================


class ScanTargetValidator:  # pylint: disable=R0903
    """Validate scan operation targets."""

    @staticmethod
    def validate(
        target: str, platforms: Optional[List[str]] = None
    ) -> ValidationResult:
        """Validate scan target."""
        errors: List[str] = []
        warnings: List[str] = []

        username_result = UsernameValidator.validate(target)
        if not username_result.is_valid:
            errors.extend(username_result.errors)

        if platforms:
            for platform in platforms:
                plat_result = PlatformValidator.validate(platform)
                if not plat_result.is_valid:
                    errors.extend(plat_result.errors)

        return ValidationResult(
            len(errors) == 0, target, errors, warnings, ValidationType.SCAN_TARGET
        )


# ========================================================================
# MASTER VALIDATOR
# ========================================================================


class Validator:  # pylint: disable=R0903
    """Central validation system."""

    @staticmethod
    def validate_username(
        username: str, level: ValidationLevel = ValidationLevel.MODERATE
    ) -> ValidationResult:
        """Validate username."""
        return UsernameValidator.validate(username, level)

    @staticmethod
    def validate_url(url: str) -> ValidationResult:
        """Validate URL."""
        return URLValidator.validate(url)

    @staticmethod
    def validate_email(email: str) -> ValidationResult:
        """Validate email."""
        return EmailValidator.validate(email)

    @staticmethod
    def validate_domain(domain: str) -> ValidationResult:
        """Validate domain."""
        return DomainValidator.validate(domain)

    @staticmethod
    def validate_ip(ip_address: str) -> ValidationResult:
        """Validate IP address."""
        return IPAddressValidator.validate(ip_address)

    @staticmethod
    def validate_port(port: Any, warn_privileged: bool = True) -> ValidationResult:
        """Validate port."""
        return PortValidator.validate(port, warn_privileged)

    @staticmethod
    def validate_platform(platform_id: str) -> ValidationResult:
        """Validate platform ID."""
        return PlatformValidator.validate(platform_id)

    @staticmethod
    def validate_database_query(query: str) -> ValidationResult:
        """Validate database query."""
        return DatabaseValidator.validate_query(query)

    @staticmethod
    def validate_scan_target(
        target: str, platforms: Optional[List[str]] = None
    ) -> ValidationResult:
        """Validate scan target."""
        return ScanTargetValidator.validate(target, platforms)

    @staticmethod
    def validate_multiple(
        validators: Dict[str, Callable]
    ) -> Tuple[bool, Dict[str, ValidationResult]]:
        """Run multiple validators."""
        results = {}
        all_valid = True

        for name, validator_func in validators.items():
            result = validator_func()
            results[name] = result
            if not result.is_valid:
                all_valid = False

        return all_valid, results


# ========================================================================
# DECORATOR FOR VALIDATION
# ========================================================================


def validate_inputs(**validators: Callable) -> Callable:
    """Decorator to validate function inputs."""

    def decorator(func: Callable) -> Callable:
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            all_valid, results = Validator.validate_multiple(validators)

            if not all_valid:
                errors = []
                for name, result in results.items():
                    if not result.is_valid:
                        errors.extend([f"{name}: {e}" for e in result.errors])
                error_msg = "Validation failed: " + "; ".join(errors)
                logger.error(error_msg)
                raise ValueError(error_msg)

            return func(*args, **kwargs)

        return wrapper

    return decorator


# ========================================================================
# DEMO & TESTING
# ========================================================================


def demo() -> None:
    """Demonstrate validation system."""
    print("\n" + "=" * 70)
    print("HandyOsint Validation System - Demo")
    print("=" * 70 + "\n")

    # Test username
    print("✓ Username Validation:")
    result = Validator.validate_username("john_doe")
    print(f"   Valid: {result.is_valid}, Value: {result.value}")

    # Test URL
    print("\n✓ URL Validation:")
    result = Validator.validate_url("https://github.com/user")
    print(f"   Valid: {result.is_valid}, Value: {result.value}")

    # Test email
    print("\n✓ Email Validation:")
    result = Validator.validate_email("user@example.com")
    print(f"   Valid: {result.is_valid}, Value: {result.value}")

    # Test platform
    print("\n✓ Platform Validation:")
    result = Validator.validate_platform("github")
    print(f"   Valid: {result.is_valid}, Value: {result.value}")

    # Test scan target
    print("\n✓ Scan Target Validation:")
    result = Validator.validate_scan_target("testuser", ["github", "twitter"])
    print(f"   Valid: {result.is_valid}, Target: {result.value}")

    print("\n" + "=" * 70)
    print("Demo completed!")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    demo()

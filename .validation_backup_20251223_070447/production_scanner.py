#!/usr/bin/env python3
"""
HandyOsint Production Scanner - Real HTTP requests with enterprise features.

Advanced OSINT platform reconnaissance with:
- Real HTTP requests across 25+ platforms
- Proxy and DNS customization
- Rate limiting and human mimicking
- Comprehensive error handling
- Async/concurrent scanning
"""

import asyncio
import time
import logging
import random
from datetime import datetime
from typing import Dict, Any, List, Optional
from enum import Enum
from dataclasses import dataclass, field, asdict
from collections import deque

import aiohttp

logger = logging.getLogger(__name__)


# ========================================================================
# DATA MODELS
# ========================================================================

class ScanStatus(Enum):
    """Platform scan status indicators."""

    FOUND = "found"
    NOT_FOUND = "not_found"
    ERROR = "error"
    BLOCKED = "blocked"
    RATE_LIMITED = "rate_limited"
    TIMEOUT = "timeout"


class PlatformCategory(Enum):
    """Platform categories."""

    SOCIAL_MEDIA = "social_media"
    DEVELOPER = "developer"
    CONTENT = "content"
    MESSAGING = "messaging"
    PROFESSIONAL = "professional"
    OTHER = "other"


@dataclass
class PlatformConfig:
    """Platform configuration with validation rules."""

    name: str
    url_template: str
    category: PlatformCategory
    check_method: str = "status_code"
    valid_codes: List[int] = field(default_factory=lambda: [200])
    not_found_codes: List[int] = field(default_factory=lambda: [404])
    blocked_codes: List[int] = field(default_factory=lambda: [403])
    timeout: float = 10.0
    custom_validator: Optional[callable] = None
    max_retries: int = 2

    def __post_init__(self) -> None:
        """Validate and normalize configuration."""
        if not self.valid_codes:
            self.valid_codes = [200]
        if not self.not_found_codes:
            self.not_found_codes = [404]


@dataclass
class ScanResultDetail:
    """Individual platform scan result."""

    platform: str
    platform_id: str
    url: str
    status: str
    status_code: int = 0
    response_time: float = 0.0
    found: bool = False
    content_preview: str = ""
    error: Optional[str] = None
    timestamp: str = field(
        default_factory=lambda: datetime.now().isoformat()
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class UsernameSearchResult:
    """Complete username search result across platforms."""

    username: str
    timestamp: str = field(
        default_factory=lambda: datetime.now().isoformat()
    )
    total_platforms: int = 0
    profiles_found: int = 0
    scan_duration: float = 0.0
    status: str = "pending"
    platforms: Dict[str, ScanResultDetail] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    statistics: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "username": self.username,
            "timestamp": self.timestamp,
            "total_platforms": self.total_platforms,
            "profiles_found": self.profiles_found,
            "scan_duration": self.scan_duration,
            "status": self.status,
            "platforms": {
                k: v.to_dict() for k, v in self.platforms.items()
            },
            "errors": self.errors,
            "statistics": self.statistics,
        }


# ========================================================================
# CUSTOM VALIDATORS
# ========================================================================

def validate_github(content: str) -> bool:
    """Validate GitHub profile exists."""
    return "Page not found" not in content and len(content) > 100


def validate_twitter(content: str) -> bool:
    """Validate Twitter/X profile exists."""
    return (
        "This account doesn't exist" not in content
        and len(content) > 100
    )


def validate_instagram(content: str) -> bool:
    """Validate Instagram profile exists."""
    return (
        "The link you followed may be broken" not in content
        and len(content) > 100
    )


def validate_tiktok(content: str) -> bool:
    """Validate TikTok profile exists."""
    return (
        "Couldn't find this account" not in content
        and len(content) > 100
    )


def validate_facebook(content: str) -> bool:
    """Validate Facebook profile exists."""
    return (
        "Log in to Facebook" not in content
        and len(content) > 100
    )


# ========================================================================
# SCANNER CONFIGURATION
# ========================================================================

class ScannerConfig:
    """Scanner configuration helper."""

    DEFAULT_USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15",
    ]

    @staticmethod
    def get_default_headers() -> Dict[str, str]:
        """Get default HTTP headers."""
        return {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }


# ========================================================================
# PRODUCTION SCANNER
# ========================================================================

class ProductionScanner:
    """Enterprise OSINT scanner with real HTTP requests."""

    def __init__(
        self,
        max_concurrent: int = 10,
        timeout: int = 30,
        min_delay: float = 0.5,
        max_delay: float = 2.0,
        proxies: Optional[List[str]] = None
    ) -> None:
        """Initialize scanner with configuration."""
        self.max_concurrent = max_concurrent
        self.timeout = timeout
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.user_agents = ScannerConfig.DEFAULT_USER_AGENTS
        self.proxy_pool = deque(proxies) if proxies else None
        self.session: Optional[aiohttp.ClientSession] = None
        self.platforms: Dict[str, PlatformConfig] = {}
        self.request_count = 0
        self.total_requests = 0
        self.rate_limiters: Dict[str, float] = {}
        self._init_platforms()

        logger.info(
            "ProductionScanner initialized with %d platforms",
            len(self.platforms)
        )

    def _init_platforms(self) -> None:
        """Initialize platform configurations."""
        platforms_data = [
            ("twitter", "Twitter/X", "https://twitter.com/{username}",
             PlatformCategory.SOCIAL_MEDIA, validate_twitter),
            ("instagram", "Instagram", "https://instagram.com/{username}",
             PlatformCategory.SOCIAL_MEDIA, validate_instagram),
            ("tiktok", "TikTok", "https://tiktok.com/@{username}",
             PlatformCategory.SOCIAL_MEDIA, validate_tiktok),
            ("reddit", "Reddit", "https://reddit.com/user/{username}",
             PlatformCategory.SOCIAL_MEDIA, None),
            ("linkedin", "LinkedIn", "https://linkedin.com/in/{username}",
             PlatformCategory.PROFESSIONAL, None),
            ("snapchat", "Snapchat", "https://snapchat.com/add/{username}",
             PlatformCategory.SOCIAL_MEDIA, None),
            ("telegram", "Telegram", "https://t.me/{username}",
             PlatformCategory.MESSAGING, None),
            ("github", "GitHub", "https://github.com/{username}",
             PlatformCategory.DEVELOPER, validate_github),
            ("gitlab", "GitLab", "https://gitlab.com/{username}",
             PlatformCategory.DEVELOPER, None),
            ("stackoverflow", "Stack Overflow",
             "https://stackoverflow.com/users/{username}",
             PlatformCategory.DEVELOPER, None),
            ("dev_to", "Dev.to", "https://dev.to/{username}",
             PlatformCategory.DEVELOPER, None),
            ("codepen", "CodePen", "https://codepen.io/{username}",
             PlatformCategory.DEVELOPER, None),
            ("youtube", "YouTube", "https://youtube.com/@{username}",
             PlatformCategory.CONTENT, None),
            ("twitch", "Twitch", "https://twitch.tv/{username}",
             PlatformCategory.CONTENT, None),
            ("medium", "Medium", "https://medium.com/@{username}",
             PlatformCategory.CONTENT, None),
            ("pinterest", "Pinterest", "https://pinterest.com/{username}",
             PlatformCategory.CONTENT, None),
            ("spotify", "Spotify", "https://open.spotify.com/user/{username}",
             PlatformCategory.CONTENT, None),
            ("patreon", "Patreon", "https://patreon.com/{username}",
             PlatformCategory.OTHER, None),
            ("mastodon", "Mastodon", "https://mastodon.social/@{username}",
             PlatformCategory.SOCIAL_MEDIA, None),
            ("bluesky", "Bluesky", "https://bsky.app/profile/{username}",
             PlatformCategory.SOCIAL_MEDIA, None),
            ("threads", "Threads", "https://threads.net/@{username}",
             PlatformCategory.SOCIAL_MEDIA, None),
        ]

        for platform_id, name, url, category, validator in platforms_data:
            self.platforms[platform_id] = PlatformConfig(
                name=name,
                url_template=url,
                category=category,
                check_method="content" if validator else "status_code",
                custom_validator=validator,
            )

    def _get_next_proxy(self) -> Optional[str]:
        """Get next proxy from pool in round-robin fashion."""
        if not self.proxy_pool:
            return None
        proxy = self.proxy_pool.popleft()
        self.proxy_pool.append(proxy)
        return proxy

    async def _ensure_session(self) -> None:
        """Ensure HTTP session is initialized."""
        if self.session is None or self.session.closed:
            connector = aiohttp.TCPConnector(
                limit=self.max_concurrent,
                limit_per_host=5,
            )
            timeout = aiohttp.ClientTimeout(total=self.timeout)

            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                trust_env=True,
            )
            logger.info("HTTP session initialized")

    async def _apply_rate_limit(self, platform: str) -> None:
        """Apply rate limiting between requests."""
        if platform in self.rate_limiters:
            elapsed = time.time() - self.rate_limiters[platform]
            if elapsed < 0.1:
                await asyncio.sleep(0.1 - elapsed)
        self.rate_limiters[platform] = time.time()

    def _prepare_headers(self, platform: PlatformConfig) -> Dict[str, str]:
        """Prepare request headers with random User-Agent."""
        headers = ScannerConfig.get_default_headers()
        headers["User-Agent"] = random.choice(self.user_agents)
        return headers

    def _determine_status(
        self,
        response_status: int,
        content: str,
        platform: PlatformConfig
    ) -> tuple:
        """Determine scan status based on response and content."""
        if platform.custom_validator:
            is_valid = platform.custom_validator(content)
            return (
                ScanStatus.FOUND.value if is_valid else ScanStatus.NOT_FOUND.value,
                is_valid,
                None
            )

        if response_status in platform.valid_codes:
            return ScanStatus.FOUND.value, True, None
        if response_status in platform.not_found_codes:
            return ScanStatus.NOT_FOUND.value, False, None
        if response_status in platform.blocked_codes:
            error = f"Access Denied (HTTP {response_status})"
            return ScanStatus.BLOCKED.value, False, error
        if response_status == 429:
            return ScanStatus.RATE_LIMITED.value, False, None

        error = f"HTTP {response_status}"
        return ScanStatus.ERROR.value, False, error

    async def _make_request(
        self,
        url: str,
        platform: PlatformConfig,
        retry_count: int = 0
    ) -> ScanResultDetail:
        """Make HTTP request with retry logic and error handling."""
        start_time = time.time()

        try:
            await self._ensure_session()
            await self._apply_rate_limit(platform.name)

            delay = random.uniform(self.min_delay, self.max_delay)
            await asyncio.sleep(delay)

            headers = self._prepare_headers(platform)
            proxy_url = self._get_next_proxy() if self.proxy_pool else None

            async with self.session.get(
                url,
                headers=headers,
                allow_redirects=True,
                proxy=proxy_url
            ) as response:
                response_time = time.time() - start_time
                self.request_count += 1
                self.total_requests += 1

                try:
                    content = await response.text()
                except aiohttp.ClientPayloadError as read_err:
                    logger.error(
                        "Error reading content from %s: %s",
                        platform.name,
                        str(read_err)
                    )
                    content = ""

                content_preview = content[:500] if len(content) > 500 else content

                status, found, error = self._determine_status(
                    response.status,
                    content,
                    platform
                )

                result = ScanResultDetail(
                    platform=platform.name,
                    platform_id=platform.name,
                    url=str(response.url),
                    status=status,
                    status_code=response.status,
                    response_time=response_time,
                    found=found,
                    content_preview=content_preview,
                    error=error,
                )

                logger.info(
                    "Scanned %s: %s",
                    platform.name,
                    status
                )
                return result

        except asyncio.TimeoutError:
            response_time = time.time() - start_time
            if retry_count < platform.max_retries:
                await asyncio.sleep(1)
                return await self._make_request(url, platform, retry_count + 1)

            return ScanResultDetail(
                platform=platform.name,
                platform_id=platform.name,
                url=url,
                status=ScanStatus.TIMEOUT.value,
                response_time=response_time,
                error="Request timeout",
            )

        except aiohttp.ClientError as client_err:
            response_time = time.time() - start_time
            if retry_count < platform.max_retries:
                await asyncio.sleep(0.5)
                return await self._make_request(url, platform, retry_count + 1)

            return ScanResultDetail(
                platform=platform.name,
                platform_id=platform.name,
                url=url,
                status=ScanStatus.ERROR.value,
                response_time=response_time,
                error=f"Network error: {str(client_err)}",
            )

        except (KeyError, ValueError, asyncio.CancelledError) as err:
            response_time = time.time() - start_time
            logger.error(
                "Error scanning %s: %s",
                platform.name,
                str(err)
            )

            return ScanResultDetail(
                platform=platform.name,
                platform_id=platform.name,
                url=url,
                status=ScanStatus.ERROR.value,
                response_time=response_time,
                error=f"Scan error: {str(err)}",
            )

    async def scan_platform(
        self,
        platform_id: str,
        username: str
    ) -> ScanResultDetail:
        """Scan single platform."""
        if platform_id not in self.platforms:
            return ScanResultDetail(
                platform=platform_id,
                platform_id=platform_id,
                url="",
                status=ScanStatus.ERROR.value,
                error="Platform not configured",
            )

        platform = self.platforms[platform_id]
        url = platform.url_template.format(username=username)
        return await self._make_request(url, platform)

    def _process_scan_results(
        self,
        valid_platforms: List[str],
        results: List[ScanResultDetail]
    ) -> tuple:
        """Process scan results and return statistics."""
        found_count = 0
        error_count = 0
        rate_limited_count = 0
        platform_results = {}
        errors = []

        for idx, result in enumerate(results):
            platform_id = valid_platforms[idx]
            platform_results[platform_id] = result

            if result.found:
                found_count += 1
            elif result.status == ScanStatus.ERROR.value:
                error_count += 1
                if result.error:
                    errors.append(f"{result.platform}: {result.error}")
            elif result.status == ScanStatus.RATE_LIMITED.value:
                rate_limited_count += 1

        avg_response_time = (
            sum(r.response_time for r in results) / len(results)
            if results else 0
        )

        statistics = {
            "total_platforms": len(valid_platforms),
            "profiles_found": found_count,
            "errors": error_count,
            "rate_limited": rate_limited_count,
            "successful_requests": len(
                [r for r in results if r.status != ScanStatus.ERROR.value]
            ),
            "average_response_time": avg_response_time,
            "total_requests": self.total_requests,
        }

        return found_count, platform_results, errors, statistics

    async def scan_username(
        self,
        username: str,
        platforms: Optional[List[str]] = None
    ) -> UsernameSearchResult:
        """Scan username across multiple platforms."""
        self.request_count = 0
        start_time = time.time()

        if not username or len(username.strip()) == 0:
            return UsernameSearchResult(
                username=username,
                status="failed",
                errors=["Invalid username provided"]
            )

        if platforms is None:
            platforms = list(self.platforms.keys())

        valid_platforms = [
            p for p in platforms if p in self.platforms
        ]

        if not valid_platforms:
            return UsernameSearchResult(
                username=username,
                status="failed",
                errors=["No valid platforms specified"],
            )

        semaphore = asyncio.Semaphore(self.max_concurrent)

        async def scan_with_limit(platform_id: str) -> ScanResultDetail:
            async with semaphore:
                try:
                    return await self.scan_platform(platform_id, username)
                except (KeyError, ValueError, asyncio.CancelledError) as err:
                    logger.error(
                        "Error scanning %s: %s",
                        platform_id,
                        str(err)
                    )
                    return ScanResultDetail(
                        platform=self.platforms[platform_id].name,
                        platform_id=platform_id,
                        url="",
                        status=ScanStatus.ERROR.value,
                        error=str(err),
                    )

        tasks = [scan_with_limit(pid) for pid in valid_platforms]
        results = await asyncio.gather(*tasks)

        found_count, platform_results, errors, statistics = (
            self._process_scan_results(valid_platforms, results)
        )

        scan_duration = time.time() - start_time

        result = UsernameSearchResult(
            username=username,
            total_platforms=len(valid_platforms),
            profiles_found=found_count,
            scan_duration=scan_duration,
            status="completed",
            platforms=platform_results,
            errors=errors,
            statistics=statistics,
        )

        logger.info(
            "Scan completed for %s: %d profiles found in %.2fs",
            username,
            found_count,
            scan_duration
        )
        return result

    async def scan(self, username: str) -> UsernameSearchResult:
        """Alias for scan_username."""
        return await self.scan_username(username)

    def get_platform_info(self) -> Dict[str, Any]:
        """Get information about available platforms."""
        categories = {}
        for platform_id, config in self.platforms.items():
            category = config.category.value
            if category not in categories:
                categories[category] = []
            categories[category].append(
                {"id": platform_id, "name": config.name}
            )

        return {
            "total_platforms": len(self.platforms),
            "categories": categories,
            "request_stats": {
                "requests_this_session": self.request_count,
                "total_requests": self.total_requests,
            },
        }

    async def close(self) -> None:
        """Close session and cleanup."""
        if self.session and not self.session.closed:
            await self.session.close()
            logger.info("Session closed")

    async def __aenter__(self) -> 'ProductionScanner':
        """Async context manager entry."""
        await self._ensure_session()
        return self

    async def __aexit__(
        self,
        exc_type: Any,
        exc_val: Any,
        exc_tb: Any
    ) -> None:
        """Async context manager exit."""
        await self.close()


# ========================================================================
# DEMO & TESTING
# ========================================================================

async def demo() -> None:
    """Demo scanner functionality."""
    print("\n" + "=" * 70)
    print("HandyOsint Production Scanner - Demo")
    print("=" * 70 + "\n")

    async with ProductionScanner(max_concurrent=10) as scanner:
        print("🔍 Testing single platform scan (GitHub)...")
        result = await scanner.scan_platform("github", "torvalds")
        print(f"   Status: {result.status}")
        print(f"   Response Time: {result.response_time:.2f}s\n")

        print("🔍 Testing multi-platform scan...")
        platforms = ["github", "twitter", "reddit", "medium", "dev_to"]
        scan_result = await scanner.scan_username("testuser123", platforms)

        print(f"   Username: {scan_result.username}")
        print(f"   Scan Duration: {scan_result.scan_duration:.2f}s")
        print(
            f"   Profiles Found: {scan_result.profiles_found}/"
            f"{scan_result.total_platforms}"
        )
        print(f"   Status: {scan_result.status}\n")

        print("   Platform Results:")
        for platform_id, detail in scan_result.platforms.items():
            icon = "✓" if detail.found else "✗"
            print(f"     {icon} {detail.platform}: {detail.status}")

        print("\n📊 Available Platforms:")
        info = scanner.get_platform_info()
        for category, plat_list in info["categories"].items():
            print(f"   {category}: {len(plat_list)} platforms")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    asyncio.run(demo())

#!/usr/bin/env python3
"""
HandyOsint Production Scanner - Real HTTP requests with enterprise features
Advanced OSINT platform reconnaissance with comprehensive error handling
"""

import asyncio
import time
import logging
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from enum import Enum
from dataclasses import dataclass, field, asdict
import random
from collections import deque
from config.app_config import app_config
import ssl
import socket
from aiohttp import resolver

import aiohttp

from core.cache import RedisCache


logger = logging.getLogger(__name__)


# ============================================================================
# DATA MODELS
# ============================================================================


class ScanStatus(Enum):
    """Platform scan status"""

    FOUND = "found"
    NOT_FOUND = "not_found"
    ERROR = "error"
    PRIVATE = "private"
    BLOCKED = "blocked"
    RATE_LIMITED = "rate_limited"
    TIMEOUT = "timeout"
    PENDING = "pending"


class PlatformCategory(Enum):
    """Platform categories"""

    SOCIAL_MEDIA = "social_media"
    DEVELOPER = "developer"
    CONTENT = "content"
    MESSAGING = "messaging"
    PROFESSIONAL = "professional"
    OTHER = "other"


@dataclass
class PlatformConfig:
    """Platform configuration"""

    name: str
    url_template: str
    category: PlatformCategory
    check_method: str = "status_code"
    valid_codes: List[int] = field(default_factory=lambda: [200])
    not_found_codes: List[int] = field(default_factory=lambda: [404])
    blocked_codes: List[int] = field(default_factory=lambda: [403])
    timeout: float = 10.0
    headers: Dict[str, str] = field(
        default_factory=lambda: {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
    )
    requires_auth: bool = False
    custom_validator: Optional[callable] = None
    retry_on_error: bool = True
    max_retries: int = 2
    rate_limit_delay: float = 0.1

    def __post_init__(self):
        """Validate and normalize config"""
        if not self.valid_codes:
            self.valid_codes = [200]
        if not self.not_found_codes:
            self.not_found_codes = [404]


@dataclass
class ScanResultDetail:
    """Individual platform scan result"""

    platform: str
    platform_id: str
    url: str
    status: str
    status_code: int = 0
    response_time: float = 0.0
    found: bool = False
    headers: Dict[str, str] = field(default_factory=dict)
    content_preview: str = ""
    error: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class UsernameSearchResult:
    """Complete username search result"""

    username: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    total_platforms: int = 0
    profiles_found: int = 0
    scan_duration: float = 0.0
    status: str = "pending"
    platforms: Dict[str, ScanResultDetail] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    statistics: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "username": self.username,
            "timestamp": self.timestamp,
            "total_platforms": self.total_platforms,
            "profiles_found": self.profiles_found,
            "scan_duration": self.scan_duration,
            "status": self.status,
            "platforms": {k: v.to_dict() for k, v in self.platforms.items()},
            "errors": self.errors,
            "statistics": self.statistics,
            "metadata": self.metadata,
        }


# ============================================================================
# CUSTOM VALIDATORS
# ============================================================================


def validate_github(content: str) -> bool:
    """Custom validator for GitHub"""
    return "Page not found" not in content


def validate_twitter(content: str) -> bool:
    """Custom validator for Twitter/X"""
    return (
        "This account doesn’t exist" not in content
        and "Account suspended" not in content
    )


def validate_instagram(content: str) -> bool:
    """Custom validator for Instagram"""
    return (
        "The link you followed may be broken, or the page may have been removed"
        not in content
        and "Page not found" not in content
    )


def validate_tiktok(content: str) -> bool:
    """Custom validator for TikTok"""
    return (
        "Couldn't find this account" not in content
        and "This account can't be found" not in content
    )


def validate_facebook(content: str) -> bool:
    """Custom validator for Facebook"""
    return (
        "Log in to Facebook" not in content
        and "You must log in to continue" not in content
    )


# ============================================================================
# PRODUCTION SCANNER
# ============================================================================


class ProductionScanner:
    """Enterprise OSINT scanner with real HTTP requests"""



    def __init__(self, max_concurrent: Optional[int] = None, timeout: Optional[int] = None):
        """Initialize scanner"""
        self.max_concurrent = max_concurrent or app_config.get('scanner.max_concurrent_requests', 10)
        self.timeout = timeout or app_config.get('scanner.request_timeout', 30)
        self.user_agents = app_config.get('scanner.user_agents')
        if not self.user_agents:
            self.user_agents = [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 14.4; rv:124.0) Gecko/20100101 Firefox/124.0",
                "Mozilla/5.0 (X11; Linux i686; rv:124.0) Gecko/20100101 Firefox/124.0",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 Edg/123.0.2420.81",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 OPR/109.0.0.0",
                "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Mobile Safari/537.36",
                "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
            ]
        
        self.ssl_verify = app_config.get('scanner.ssl_verify', True)
        self.ssl_ca_bundle = app_config.get('scanner.ssl_ca_bundle')
        self.ssl_client_cert = app_config.get('scanner.ssl_client_cert')
        self.ssl_client_key = app_config.get('scanner.ssl_client_key')
        self.min_delay = app_config.get('scanner.min_delay', 1.0)
        self.max_delay = app_config.get('scanner.max_delay', 3.0)
        self.accept_headers = app_config.get('scanner.accept_headers', ["*/*"])
        self.accept_language_headers = app_config.get('scanner.accept_language_headers', ["en-US,en;q=0.9"])
        self.referer_domains = app_config.get('scanner.referer_domains', [])
        self.referer_chance = app_config.get('scanner.referer_chance', 0.5)
        self.disable_dns_cache = app_config.get('scanner.disable_dns_cache', False)
        self.custom_nameservers = app_config.get('scanner.custom_nameservers', [])
        self.proxies = app_config.get('scanner.proxies', [])
        self.proxy_pool = deque(self.proxies) if self.proxies else None
        self.session: Optional[aiohttp.ClientSession] = None
        self.platforms: Dict[str, PlatformConfig] = self._initialize_platforms()
        self.request_count = 0
        self.total_requests = 0
        self.cache = RedisCache()  # Initialize RedisCache
        self.rate_limiters: Dict[str, float] = {}

        logger.info(
            f"ProductionScanner initialized with {len(self.platforms)} platforms"
        )

    def _initialize_platforms(self) -> Dict[str, PlatformConfig]:
        """Initialize all platform configurations"""
        platforms = {}



        # ====================================================================
        # SOCIAL MEDIA PLATFORMS
        # ====================================================================

        platforms["twitter"] = PlatformConfig(
            name="Twitter/X",
            url_template="https://twitter.com/{username}",
            category=PlatformCategory.SOCIAL_MEDIA,
            check_method="content",
            custom_validator=validate_twitter,
        )

        platforms["facebook"] = PlatformConfig(
            name="Facebook",
            url_template="https://facebook.com/{username}",
            category=PlatformCategory.SOCIAL_MEDIA,
            check_method="content",
            custom_validator=validate_facebook,
            requires_auth=True,
        )

        platforms["instagram"] = PlatformConfig(
            name="Instagram",
            url_template="https://instagram.com/{username}",
            category=PlatformCategory.SOCIAL_MEDIA,
            check_method="content",
            custom_validator=validate_instagram,
        )

        platforms["tiktok"] = PlatformConfig(
            name="TikTok",
            url_template="https://tiktok.com/@{username}",
            category=PlatformCategory.SOCIAL_MEDIA,
            check_method="content",
            custom_validator=validate_tiktok,
        )

        platforms["reddit"] = PlatformConfig(
            name="Reddit",
            url_template="https://reddit.com/user/{username}",
            category=PlatformCategory.SOCIAL_MEDIA,
            valid_codes=[200],
            not_found_codes=[404],
        )

        platforms["linkedin"] = PlatformConfig(
            name="LinkedIn",
            url_template="https://linkedin.com/in/{username}",
            category=PlatformCategory.PROFESSIONAL,
            valid_codes=[200, 999],
            not_found_codes=[404],
            requires_auth=True,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept": "text/html,application/xhtml+xml",
            },
        )

        platforms["snapchat"] = PlatformConfig(
            name="Snapchat",
            url_template="https://snapchat.com/add/{username}",
            category=PlatformCategory.SOCIAL_MEDIA,
            valid_codes=[200],
            not_found_codes=[404],
        )

        platforms["telegram"] = PlatformConfig(
            name="Telegram",
            url_template="https://t.me/{username}",
            category=PlatformCategory.MESSAGING,
            valid_codes=[200],
            not_found_codes=[404],
        )

        # ====================================================================
        # DEVELOPER PLATFORMS
        # ====================================================================

        platforms["github"] = PlatformConfig(
            name="GitHub",
            url_template="https://github.com/{username}",
            category=PlatformCategory.DEVELOPER,
            check_method="content",
            custom_validator=validate_github,
        )

        platforms["gitlab"] = PlatformConfig(
            name="GitLab",
            url_template="https://gitlab.com/{username}",
            category=PlatformCategory.DEVELOPER,
            valid_codes=[200],
            not_found_codes=[404],
        )

        platforms["stackoverflow"] = PlatformConfig(
            name="Stack Overflow",
            url_template="https://stackoverflow.com/users/{username}",
            category=PlatformCategory.DEVELOPER,
            valid_codes=[200],
            not_found_codes=[404],
        )

        platforms["medium"] = PlatformConfig(
            name="Medium",
            url_template="https://medium.com/@{username}",
            category=PlatformCategory.CONTENT,
            blocked_codes=[403],
        )

        platforms["dev_to"] = PlatformConfig(
            name="Dev.to",
            url_template="https://dev.to/{username}",
            category=PlatformCategory.DEVELOPER,
            valid_codes=[200],
            not_found_codes=[404],
        )

        platforms["codepen"] = PlatformConfig(
            name="CodePen",
            url_template="https://codepen.io/{username}",
            category=PlatformCategory.DEVELOPER,
            blocked_codes=[403],
        )

        # ====================================================================
        # CONTENT PLATFORMS
        # ====================================================================

        platforms["youtube"] = PlatformConfig(
            name="YouTube",
            url_template="https://youtube.com/@{username}",
            category=PlatformCategory.CONTENT,
            valid_codes=[200],
            not_found_codes=[404],
        )

        platforms["twitch"] = PlatformConfig(
            name="Twitch",
            url_template="https://twitch.tv/{username}",
            category=PlatformCategory.CONTENT,
            valid_codes=[200],
            not_found_codes=[404],
        )

        platforms["pinterest"] = PlatformConfig(
            name="Pinterest",
            url_template="https://pinterest.com/{username}",
            category=PlatformCategory.CONTENT,
            valid_codes=[200],
            not_found_codes=[404],
        )

        platforms["spotify"] = PlatformConfig(
            name="Spotify",
            url_template="https://open.spotify.com/user/{username}",
            category=PlatformCategory.CONTENT,
            valid_codes=[200],
            not_found_codes=[404],
        )

        # ====================================================================
        # OTHER PLATFORMS
        # ====================================================================

        platforms["patreon"] = PlatformConfig(
            name="Patreon",
            url_template="https://patreon.com/{username}",
            category=PlatformCategory.OTHER,
            valid_codes=[200],
            not_found_codes=[404],
        )

        platforms["mastodon"] = PlatformConfig(
            name="Mastodon",
            url_template="https://mastodon.social/@{username}",
            category=PlatformCategory.SOCIAL_MEDIA,
            valid_codes=[200],
            not_found_codes=[404],
        )

        platforms["bluesky"] = PlatformConfig(
            name="Bluesky",
            url_template="https://bsky.app/profile/{username}",
            category=PlatformCategory.SOCIAL_MEDIA,
            valid_codes=[200],
            not_found_codes=[404],
        )

        platforms["threads"] = PlatformConfig(
            name="Threads",
            url_template="https://threads.net/@{username}",
            category=PlatformCategory.SOCIAL_MEDIA,
            valid_codes=[200],
            not_found_codes=[404],
        )

        return platforms

    def _get_next_proxy(self) -> Optional[str]:
        """Get the next proxy from the pool in a round-robin fashion."""
        if not self.proxy_pool:
            return None
        proxy = self.proxy_pool.popleft()
        self.proxy_pool.append(proxy) # Put it back at the end
        return proxy

    async def _ensure_session(self) -> None:
        """Ensure HTTP session is initialized"""
        if self.session is None or self.session.closed:
            # --- DNS Configuration ---
            connector_kwargs = {
                "limit": self.max_concurrent,
                "limit_per_host": 5,
                "family": socket.AF_INET, # Force IPv4 to avoid potential IPv6 issues or delays
            }

            if self.disable_dns_cache:
                connector_kwargs["ttl_dns_cache"] = 0 # Disable DNS cache
                logger.info("DNS caching disabled.")

            if self.custom_nameservers:
                connector_kwargs["resolver"] = resolver.AsyncResolver(nameservers=self.custom_nameservers)
                logger.info(f"Using custom DNS servers: {self.custom_nameservers}")
            else:
                connector_kwargs["ttl_dns_cache"] = 300 # Default if not disabled and no custom resolver

            connector = aiohttp.TCPConnector(**connector_kwargs)
            timeout = aiohttp.ClientTimeout(total=self.timeout)

            # --- TLS Configuration ---
            ssl_context = None
            if not self.ssl_verify:
                ssl_context = False # Disable SSL verification
            elif self.ssl_ca_bundle or self.ssl_client_cert:
                # Create a custom SSL context
                ssl_context = ssl.create_default_context(cafile=self.ssl_ca_bundle)
                if self.ssl_client_cert and self.ssl_client_key:
                    # Resolve client cert/key paths relative to BASE_DIR if they are relative
                    cert_path = app_config.get('scanner.ssl_client_cert')
                    key_path = app_config.get('scanner.ssl_client_key')
                    if cert_path and key_path:
                        ssl_context.load_cert_chain(str(cert_path), str(key_path))
                # Apply hostname verification (default is CERT_REQUIRED)
                ssl_context.check_hostname = self.ssl_verify if isinstance(self.ssl_verify, bool) else True
                # Further customize security options as needed
                # ssl_context.minimum_version = ssl.TLSVersion.TLSv1_2 # Example

            self.session = aiohttp.ClientSession(
                connector=connector, timeout=timeout, trust_env=True, ssl=ssl_context # Pass the SSL context
            )
            logger.info("HTTP session initialized")


    async def _make_request(
        self, url: str, platform: PlatformConfig, retry_count: int = 0
    ) -> ScanResultDetail:
        """Make HTTP request with retry logic"""
        start_time = time.time()
        platform_name = url.split("/")[2] if "/" in url else "unknown"

        try:
            await self._ensure_session()

            # Apply rate limiting
            await self._apply_rate_limit(platform_name)

            # --- Human Mimicking: Random Delay ---
            if self.min_delay is not None and self.max_delay is not None:
                delay = random.uniform(self.min_delay, self.max_delay)
                await asyncio.sleep(delay)
                logger.debug(f"Applying random delay of {delay:.2f}s before request to {platform.name}")

            # Prepare headers with a random User-Agent
            request_headers = platform.headers.copy()
            request_headers["User-Agent"] = random.choice(self.user_agents)
            if self.accept_headers:
                request_headers["Accept"] = random.choice(self.accept_headers)
            if self.accept_language_headers:
                request_headers["Accept-Language"] = random.choice(self.accept_language_headers)
            
            # --- Human Mimicking: Referer Spoofing ---
            if self.referer_domains and random.random() < self.referer_chance:
                referer_domain = random.choice(self.referer_domains)
                request_headers["Referer"] = f"{referer_domain}/"

            proxy_url = None
            if self.proxy_pool:
                proxy_url = self._get_next_proxy()
                if proxy_url:
                    logger.debug(f"Using proxy: {proxy_url} for {platform.name}")

            # Main request block
            try:
                async with self.session.get(
                    url, headers=request_headers, allow_redirects=True, proxy=proxy_url
                ) as response:
                    response_time = time.time() - start_time
                    self.request_count += 1
                    self.total_requests += 1

                    # Read content safely
                    content = ""
                    try:
                        content = await response.text()
                    except aiohttp.ClientPayloadError:
                            platform_id=platform.name,
                        )
                        platform_id=platform.name,
                            status=ScanStatus.ERROR.value,
                            response_time=time.time() - start_time,
                            error=f"Error reading content: {e}",
                        )

                    content_preview = content[:500] if len(content) > 500 else content

                    # Determine status
                    if platform.custom_validator:
                        is_valid = platform.custom_validator(content)
                        if platform.requires_auth and not is_valid:
                            status = ScanStatus.PRIVATE.value
                            found = False
                        elif is_valid:
                            status = ScanStatus.FOUND.value
                            found = True
                        else:
                            status = ScanStatus.NOT_FOUND.value
                            found = False
                    else: # No custom validator, rely on status codes
                        error_message = None # Initialize error_message here

                        if response.status in platform.valid_codes:
                            status = ScanStatus.FOUND.value
                            found = True
                        elif response.status in platform.not_found_codes:
                            status = ScanStatus.NOT_FOUND.value
                            found = False
                        elif response.status in platform.blocked_codes:
                            status = ScanStatus.BLOCKED.value
                            found = False
                            error_message = f"Access Denied (HTTP {response.status} Forbidden)"
                        elif response.status == 429:
                            status = ScanStatus.RATE_LIMITED.value
                            found = False
                        else:
                            status = ScanStatus.ERROR.value
                            found = False
                            error_message = f"Unexpected HTTP status: {response.status}"

                    result = ScanResultDetail(
                        platform=platform.name,
                                                    platform_id=platform.name,                        url=str(response.url),
                        status=status,
                        status_code=response.status,
                        response_time=response_time,
                        found=found,
                        headers=dict(response.headers),
                        content_preview=content_preview,
                        error=error_message if status in [ScanStatus.BLOCKED.value, ScanStatus.ERROR.value] else None,
                    )
                    logger.info(f"Scanned {platform.name}: {status} ({response.status})")
                    return result

            except asyncio.TimeoutError:
                response_time = time.time() - start_time
                result = ScanResultDetail(
                    platform=platform.name,
                    platform_id=platform.name,
                    url=url,
                    status=ScanStatus.TIMEOUT.value,
                    response_time=response_time,
                    error="Request timeout",
                )
                logger.warning(f"{platform.name}: Timeout after {response_time:.2f}s")

                # Retry on timeout
                if retry_count < platform.max_retries:
                    await asyncio.sleep(1)
                    return await self._make_request(url, platform, retry_count + 1)

                return result

            except aiohttp.ClientProxyError as e:
                response_time = time.time() - start_time
                result = ScanResultDetail(
                    platform=platform.name,
                    platform_id=platform.name,
                    url=url,
                    status=ScanStatus.ERROR.value, # or a new ScanStatus.PROXY_ERROR
                    response_time=response_time,
                    error=f"Proxy error: {e}",
                )
                logger.error(f"{platform.name}: Proxy error - {str(e)}")

                # Retry with next proxy
                if retry_count < platform.max_retries:
                    await asyncio.sleep(0.5) # small delay before trying next proxy
                    return await self._make_request(url, platform, retry_count + 1)
                return result

            except aiohttp.ClientHttpProxyError as e:
                return ScanResultDetail(
                    platform=platform.name,
                    platform_id=platform.name,
                    url=url,
                    status=ScanStatus.ERROR.value,
                    response_time=time.time() - start_time,
                    error=f"Proxy error: {e}",
                )

            except aiohttp.ClientError as e:
                response_time = time.time() - start_time
                result = ScanResultDetail(
                    platform=platform.name,
                    platform_id=platform.name,
                    url=url,
                    status=ScanStatus.ERROR.value,
                    response_time=response_time,
                    error=f"Client error: {str(e)}",
                )
                logger.error(f"{platform.name}: {str(e)}")

                if retry_count < platform.max_retries:
                    await asyncio.sleep(0.5)
                    return await self._make_request(url, platform, retry_count + 1)

                return result

            except Exception as e:
                response_time = time.time() - start_time
                result = ScanResultDetail(
                    platform=platform.name,
                    platform_id=platform.name,
                    url=url,
                    status=ScanStatus.ERROR.value,
                    response_time=response_time,
                    error=f"Unexpected error: {str(e)}",
                )
                logger.error(f"{platform.name}: Unexpected error - {str(e)}")
                return result

        except Exception as e: # This catches errors from the initial setup before the main request block
            response_time = time.time() - start_time
            result = ScanResultDetail(
                platform=platform.name,
                platform_id=platform.name,
                url=url,
                status=ScanStatus.ERROR.value,
                response_time=response_time,
                error=f"Pre-request setup error: {str(e)}",
            )
            logger.error(f"{platform.name}: Pre-request setup error - {str(e)}")
            return result

    async def _apply_rate_limit(self, platform: str) -> None:
        """Apply rate limiting between requests"""
        if platform in self.rate_limiters:
            elapsed = time.time() - self.rate_limiters[platform]
            if elapsed < 0.1:
                await asyncio.sleep(0.1 - elapsed)
        self.rate_limiters[platform] = time.time()

    async def scan_platform(self, platform_id: str, username: str) -> ScanResultDetail:
        """Scan single platform"""
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

        # Check Redis cache
        cache_key = f"scan_result:{username}:{platform_id}"
        cached_result_json = await self.cache.get(
            cache_key
        )  # Await the async get method
        if cached_result_json:
            logger.info(f"Redis cache hit for {username} on {platform_id}")
            # Deserialize JSON string back to ScanResultDetail
            cached_data = json.loads(cached_result_json)
            # Create a new ScanResultDetail from the dictionary, ensuring timestamp is updated
            return ScanResultDetail(
                platform=cached_data["platform"],
                platform_id=cached_data["platform_id"],
                url=cached_data["url"],
                status=cached_data["status"],
                status_code=cached_data["status_code"],
                response_time=cached_data["response_time"],
                found=cached_data["found"],
                headers=cached_data["headers"],
                content_preview=cached_data["content_preview"],
                error=cached_data["error"],
                timestamp=datetime.now().isoformat(),  # Update timestamp to current time
            )

        result = await self._make_request(url, platform)

        # Cache the result if it's a "found" or "not_found" status
        if result.status in [ScanStatus.FOUND.value, ScanStatus.NOT_FOUND.value]:
            self.cache.set(cache_key, json.dumps(result.to_dict()))

        return result

    async def scan_username(
        self, username: str, platforms: Optional[List[str]] = None
    ) -> UsernameSearchResult:
        """Scan username across multiple platforms"""
        self.request_count = 0  # Reset for each scan operation
        start_time = time.time()

        # Validate username
        if not username or len(username.strip()) == 0:
            return UsernameSearchResult(
                username=username, status="failed", errors=["Invalid username provided"]
            )

        # Determine platforms to scan
        if platforms is None:
            platforms = list(self.platforms.keys())

        valid_platforms = [p for p in platforms if p in self.platforms]

        if not valid_platforms:
            return UsernameSearchResult(
                username=username,
                status="failed",
                errors=["No valid platforms specified"],
            )

        # Scan with concurrency limit
        semaphore = asyncio.Semaphore(self.max_concurrent)

        async def scan_with_limit(platform_id: str):
            async with semaphore:
                try:
                    return await self.scan_platform(platform_id, username)
                except Exception as e:
                    logger.error(f"Error scanning {platform_id}: {e}")
                    return ScanResultDetail(
                        platform=self.platforms[platform_id].name,
                        platform_id=platform_id,
                        url="",
                        status=ScanStatus.ERROR.value,
                        error=str(e),
                    )

        # Execute all scans concurrently
        tasks = [scan_with_limit(pid) for pid in valid_platforms]
        results = await asyncio.gather(*tasks)

        # Process results
        found_count = 0
        error_count = 0
        rate_limited_count = 0
        platform_results = {}
        errors = []

        for i, result in enumerate(results):
            platform_id = valid_platforms[i]
            platform_results[platform_id] = result

            if result.found:
                found_count += 1
            elif result.status == ScanStatus.ERROR.value:
                error_count += 1
                if result.error:
                    errors.append(f"{result.platform}: {result.error}")
            elif result.status == ScanStatus.RATE_LIMITED.value:
                rate_limited_count += 1

        scan_duration = time.time() - start_time

        # Compile statistics
        statistics = {
            "total_platforms": len(valid_platforms),
            "profiles_found": found_count,
            "errors": error_count,
            "rate_limited": rate_limited_count,
            "successful_requests": len(
                [r for r in results if r.status != ScanStatus.ERROR.value]
            ),
            "average_response_time": (
                sum(r.response_time for r in results) / len(results) if results else 0
            ),
            "total_requests": self.total_requests,
        }

        metadata = {
            "scanner_version": "3.0.0",
            "scanner_name": "ProductionScanner",
            "total_requests_made": self.total_requests,
            "redis_cache_enabled": True,
            "redis_cache_size": self.cache.get_redis_cache_size(),
        }

        result = UsernameSearchResult(
            username=username,
            total_platforms=len(valid_platforms),
            profiles_found=found_count,
            scan_duration=scan_duration,
            status="completed",
            platforms=platform_results,
            errors=errors,
            statistics=statistics,
            metadata=metadata,
        )

        logger.info(
            f"Scan completed for {username}: {found_count} profiles found in {scan_duration:.2f}s"
        )
        return result

    async def scan(self, username: str) -> UsernameSearchResult:
        """Alias for scan_username"""
        return await self.scan_username(username)

    def get_platform_info(self) -> Dict[str, Any]:
        """Get information about available platforms"""
        categories = {}
        for platform_id, config in self.platforms.items():
            category = config.category.value
            if category not in categories:
                categories[category] = []
            categories[category].append({"id": platform_id, "name": config.name})

        return {
            "total_platforms": len(self.platforms),
            "categories": categories,
            "request_stats": {
                "requests_this_session": self.request_count,
                "total_requests": self.total_requests,
                "redis_cache_size": self.cache.get_redis_cache_size(),
            },
        }

    async def close(self) -> None:
        """Close session and cleanup"""
        if self.session and not self.session.closed:
            await self.session.close()
            logger.info("Session closed")

    async def __aenter__(self):
        """Async context manager entry"""
        await self._ensure_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()


# ============================================================================
# DEMO & TESTING
# ============================================================================


async def demo():
    """Demo scanner functionality"""
    print("\n" + "=" * 70)
    print("HandyOsint Production Scanner - Demo")
    print("=" * 70 + "\n")

    async with ProductionScanner(max_concurrent=10) as scanner:
        # Test single platform
        print("🔍 Testing single platform scan (GitHub)...")
        result = await scanner.scan_platform("github", "torvalds")
        print(f"   Status: {result.status}")
        print(f"   Response Time: {result.response_time:.2f}s\n")

        # Test multi-platform scan
        print("🔍 Testing multi-platform scan...")
        platforms = ["github", "twitter", "reddit", "medium", "dev_to"]
        scan_result = await scanner.scan_username("testuser123", platforms)

        print(f"   Username: {scan_result.username}")
        print(f"   Scan Duration: {scan_result.scan_duration:.2f}s")
        print(
            f"   Profiles Found: {scan_result.profiles_found}/{scan_result.total_platforms}"
        )
        print(f"   Status: {scan_result.status}\n")

        print("   Platform Results:")
        for platform_id, detail in scan_result.platforms.items():
            icon = "✓" if detail.found else "✗"
            print(f"     {icon} {detail.platform}: {detail.status}")

        # Get platform info
        print("\n📊 Available Platforms:")
        info = scanner.get_platform_info()
        for category, platforms_list in info["categories"].items():
            print(f"   {category}: {len(platforms_list)} platforms")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    asyncio.run(demo())

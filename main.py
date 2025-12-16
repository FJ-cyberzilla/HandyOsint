#!/usr/bin/env python3
"""
SOCIAL SCAN - Complete Integrated System
Main Application with All Components Synchronized
Production-Ready with Real-time Monitoring
"""

import asyncio
import sys
import os
import json
import time
from datetime import datetime
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
import threading
import psutil
import signal
import atexit
from concurrent.futures import ThreadPoolExecutor

# ============================================================================
# 1. CONFIGURATION SYSTEM (First to load)
# ============================================================================

@dataclass
class SystemConfig:
    """Centralized system configuration"""
    app_name: str = "SOCIAL SCAN"
    version: str = "2.0.0"
    author: str = "Cyberzilla Security"
    license: str = "Educational Use Only"
    
    # Performance settings
    max_concurrent_scans: int = 5
    request_timeout: int = 10
    rate_limit_per_minute: int = 30
    retry_attempts: int = 3
    
    # UI Settings
    enable_ascii_art: bool = True
    enable_colors: bool = True
    refresh_rate: float = 0.1  # UI refresh in seconds
    
    # Monitoring
    enable_health_checks: bool = True
    health_check_interval: int = 5  # seconds
    log_level: str = "INFO"
    
    # Filesystem
    data_dir: str = "./data"
    logs_dir: str = "./logs"
    reports_dir: str = "./reports"
    
    def __post_init__(self):
        """Ensure directories exist"""
        for directory in [self.data_dir, self.logs_dir, self.reports_dir]:
            os.makedirs(directory, exist_ok=True)

# ============================================================================
# 2. LOGGING SYSTEM (Initialize early)
# ============================================================================

class SystemLogger:
    """Unified logging system"""
    
    COLORS = {
        'DEBUG': '\033[90m',    # Gray
        'INFO': '\033[96m',     # Cyan
        'SUCCESS': '\033[92m',  # Green
        'WARNING': '\033[93m',  # Yellow
        'ERROR': '\033[91m',    # Red
        'CRITICAL': '\033[41m', # Red background
        'RESET': '\033[0m'
    }
    
    def __init__(self, config: SystemConfig):
        self.config = config
        self.log_file = os.path.join(config.logs_dir, f"social_scan_{datetime.now().strftime('%Y%m%d')}.log")
        self._setup_logging()
        
    def _setup_logging(self):
        """Setup logging infrastructure"""
        import logging
        self.logger = logging.getLogger('SocialScan')
        self.logger.setLevel(getattr(logging, self.config.log_level))
        
        # File handler
        file_handler = logging.FileHandler(self.log_file)
        file_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        )
        self.logger.addHandler(file_handler)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(self._ColorFormatter())
        self.logger.addHandler(console_handler)
    
    class _ColorFormatter(logging.Formatter):
        """Color formatter for console"""
        def format(self, record):
            levelname = record.levelname
            if levelname in SystemLogger.COLORS:
                record.levelname = f"{SystemLogger.COLORS[levelname]}{levelname}{SystemLogger.COLORS['RESET']}"
            return super().format(record)
    
    def log(self, level: str, message: str, **kwargs):
        """Unified logging method"""
        getattr(self.logger, level.lower())(message, **kwargs)
    
    def info(self, message: str):
        self.log('INFO', message)
    
    def success(self, message: str):
        self.log('INFO', f"✅ {message}")
    
    def warning(self, message: str):
        self.log('WARNING', f"⚠️  {message}")
    
    def error(self, message: str):
        self.log('ERROR', f"❌ {message}")
    
    def debug(self, message: str):
        self.log('DEBUG', f"🔍 {message}")

# ============================================================================
# 3. ASCII ART & TERMINAL UI (Synchronized Display)
# ============================================================================

class ASCIIDisplay:
    """Synchronized ASCII Art Display System"""
    
    # 16-bit Color Palette (256 colors)
    COLORS = {
        # Primary Colors
        'primary': '\033[38;5;27m',      # Cyber Blue
        'secondary': '\033[38;5;46m',    # Neon Green
        'accent': '\033[38;5;196m',      # Threat Red
        'highlight': '\033[38;5;226m',   # Warning Yellow
        
        # Status Colors
        'success': '\033[38;5;46m',
        'error': '\033[38;5;196m',
        'warning': '\033[38;5;226m',
        'info': '\033[38;5;51m',
        
        # UI Elements
        'border': '\033[38;5;240m',
        'text': '\033[38;5;255m',
        'dim': '\033[38;5;244m',
        'reset': '\033[0m'
    }
    
    def __init__(self, config: SystemConfig, logger: SystemLogger):
        self.config = config
        self.logger = logger
        self.display_lock = threading.Lock()
        self.current_screen = "main"
        self._last_refresh = time.time()
        
    def display_banner(self):
        """Display main ASCII banner (thread-safe)"""
        with self.display_lock:
            if not self.config.enable_ascii_art:
                return
            
            banner = f"""
{self.COLORS['primary']}
╔═══════════════════════════════════════════════════════════════════════╗
║                                                                       ║
║   ███████╗ ██████╗  ██████╗██╗ █████╗ ██╗     ███████╗███████╗ █████╗ ███╗   ██╗   ║
║   ██╔════╝██╔═══██╗██╔════╝██║██╔══██╗██║     ██╔════╝██╔════╝██╔══██╗████╗  ██║   ║
║   ███████╗██║   ██║██║     ██║███████║██║     ███████╗█████╗  ███████║██╔██╗ ██║   ║
║   ╚════██║██║   ██║██║     ██║██╔══██║██║     ╚════██║██╔══╝  ██╔══██║██║╚██╗██║   ║
║   ███████║╚██████╔╝╚██████╗██║██║  ██║███████╗███████║███████╗██║  ██║██║ ╚████║   ║
║   ╚══════╝ ╚═════╝  ╚═════╝╚═╝╚═╝  ╚═╝╚══════╝╚══════╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═══╝   ║
║                                                                       ║
║                     C Y B E R S E C U R I T Y   O S I N T             ║
║                                                                       ║
╚═══════════════════════════════════════════════════════════════════════╝
{self.COLORS['reset']}
"""
            print(banner)
            self.logger.debug("Displayed ASCII banner")
    
    def display_status_bar(self, status_info: Dict[str, Any]):
        """Display synchronized status bar"""
        with self.display_lock:
            width = 80
            now = datetime.now().strftime("%H:%M:%S")
            
            # Prepare status segments
            user = f"USER: {status_info.get('username', 'IDLE')}"
            status = f"STATUS: {status_info.get('status', 'READY')}"
            found = f"FOUND: {status_info.get('found', 0)}/{status_info.get('total', 0)}"
            time_display = f"TIME: {now}"
            
            # Create bar
            bar_top = f"{self.COLORS['border']}╔{'═' * (width-2)}╗{self.COLORS['reset']}"
            bar_middle = f"{self.COLORS['border']}║{self.COLORS['reset']}" + \
                        f"{user:<20}{status:<20}{found:<20}{time_display:<16}" + \
                        f"{self.COLORS['border']}║{self.COLORS['reset']}"
            bar_bottom = f"{self.COLORS['border']}╚{'═' * (width-2)}╝{self.COLORS['reset']}"
            
            print(f"\n{bar_top}")
            print(bar_middle)
            print(f"{bar_bottom}\n")
    
    def display_command_panel(self):
        """Display command panel with synchronized updates"""
        with self.display_lock:
            panel = f"""
{self.COLORS['border']}┌─────────────────────────────────────────────────────────────┐{self.COLORS['reset']}
{self.COLORS['border']}│{self.COLORS['primary']} COMMAND PANEL                                                  {self.COLORS['border']}│{self.COLORS['reset']}
{self.COLORS['border']}├─────────────────────────────────────────────────────────────┤{self.COLORS['reset']}
{self.COLORS['border']}│{self.COLORS['text']}   [S]can username      [M]ulti scan       [H]istory           {self.COLORS['border']}│{self.COLORS['reset']}
{self.COLORS['border']}│{self.COLORS['text']}   [P]latforms list     [C]onfiguration    [D]ashboard         {self.COLORS['border']}│{self.COLORS['reset']}
{self.COLORS['border']}│{self.COLORS['text']}   [E]xport results     [V]alidate system  [Q]uit              {self.COLORS['border']}│{self.COLORS['reset']}
{self.COLORS['border']}└─────────────────────────────────────────────────────────────┘{self.COLORS['reset']}
"""
            print(panel)
    
    def display_scan_progress(self, platform: str, status: str, details: str = ""):
        """Display scan progress with synchronized updates"""
        with self.display_lock:
            icons = {
                'scanning': f"{self.COLORS['info']}🔄",
                'found': f"{self.COLORS['success']}✅",
                'not_found': f"{self.COLORS['dim']}❌",
                'error': f"{self.COLORS['error']}⚠️",
                'rate_limited': f"{self.COLORS['warning']}⏸️"
            }
            
            icon = icons.get(status, icons['scanning'])
            platform_text = f"{platform:.<20}"
            status_text = f"{status:.<15}"
            
            line = f"{icon} {self.COLORS['text']}{platform_text}{self.COLORS[status.lower()]}{status_text}{self.COLORS['dim']}{details}"
            
            # Use carriage return for in-place updates
            if status == 'scanning':
                print(f"\r{line}", end='', flush=True)
            else:
                print(f"\r{line}")
    
    def clear_screen(self):
        """Clear screen synchronized"""
        with self.display_lock:
            os.system('cls' if os.name == 'nt' else 'clear')

# ============================================================================
# 4. SCANNER ENGINE (Core Business Logic)
# ============================================================================

class PlatformRegistry:
    """Centralized platform registry"""
    
    PLATFORMS = {
        'github': {
            'url': 'https://github.com/{}',
            'check_method': 'status_code',
            'rate_limit': 30,
            'headers': {'Accept': 'application/vnd.github.v3+json'}
        },
        'twitter': {
            'url': 'https://twitter.com/{}',
            'check_method': 'content_analysis',
            'rate_limit': 15,
            'headers': {'x-twitter-client-language': 'en'}
        },
        'instagram': {
            'url': 'https://instagram.com/{}',
            'check_method': 'status_code',
            'rate_limit': 10
        },
        'linkedin': {
            'url': 'https://linkedin.com/in/{}',
            'check_method': 'pattern_matching',
            'rate_limit': 5
        },
        'facebook': {'url': 'https://facebook.com/{}', 'rate_limit': 5},
        'reddit': {'url': 'https://reddit.com/user/{}', 'rate_limit': 10},
        'tiktok': {'url': 'https://tiktok.com/@{}', 'rate_limit': 5},
        'youtube': {'url': 'https://youtube.com/@{}', 'rate_limit': 10},
        'twitch': {'url': 'https://twitch.tv/{}', 'rate_limit': 10},
        'telegram': {'url': 'https://t.me/{}', 'rate_limit': 10},
        'discord': {'url': 'https://discord.com/users/{}', 'rate_limit': 5},
        'snapchat': {'url': 'https://snapchat.com/add/{}', 'rate_limit': 3},
        'pinterest': {'url': 'https://pinterest.com/{}', 'rate_limit': 5},
        'medium': {'url': 'https://medium.com/@{}', 'rate_limit': 10},
        'devto': {'url': 'https://dev.to/{}', 'rate_limit': 20},
        'keybase': {'url': 'https://keybase.io/{}', 'rate_limit': 20},
        'gravatar': {'url': 'https://gravatar.com/{}', 'rate_limit': 30},
        'aboutme': {'url': 'https://about.me/{}', 'rate_limit': 20},
        'gitlab': {'url': 'https://gitlab.com/{}', 'rate_limit': 20},
        'bitbucket': {'url': 'https://bitbucket.org/{}', 'rate_limit': 20}
    }

class ScannerEngine:
    """Core scanning engine with synchronization"""
    
    def __init__(self, config: SystemConfig, logger: SystemLogger, display: ASCIIDisplay):
        self.config = config
        self.logger = logger
        self.display = display
        self.platforms = PlatformRegistry.PLATFORMS
        self.scan_lock = threading.RLock()
        self.active_scans = 0
        self.max_concurrent = config.max_concurrent_scans
        
        # Statistics
        self.stats = {
            'total_scans': 0,
            'profiles_found': 0,
            'errors': 0,
            'rate_limited': 0
        }
        
        # Rate limiting
        self.rate_limiter = RateLimiter(config.rate_limit_per_minute)
        
        # HTTP client
        self.http_client = HTTPClient(config, logger)
        
        self.logger.success("Scanner engine initialized")
    
    async def scan_username(self, username: str, platforms: List[str] = None) -> Dict[str, Any]:
        """Scan username across platforms (thread-safe)"""
        with self.scan_lock:
            if self.active_scans >= self.max_concurrent:
                raise Exception(f"Maximum concurrent scans reached ({self.max_concurrent})")
            
            self.active_scans += 1
            self.stats['total_scans'] += 1
        
        try:
            self.logger.info(f"Starting scan for username: {username}")
            
            if not platforms:
                platforms = list(self.platforms.keys())
            
            results = {
                'username': username,
                'timestamp': datetime.now().isoformat(),
                'platforms': {},
                'statistics': {
                    'scanned': 0,
                    'found': 0,
                    'errors': 0,
                    'rate_limited': 0
                }
            }
            
            # Scan platforms concurrently with semaphore
            semaphore = asyncio.Semaphore(5)  # Max 5 concurrent requests
            
            async def scan_platform(platform):
                async with semaphore:
                    return await self._scan_single_platform(platform, username)
            
            # Create and run tasks
            tasks = [scan_platform(p) for p in platforms]
            platform_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            for platform, result in zip(platforms, platform_results):
                if isinstance(result, Exception):
                    results['platforms'][platform] = {
                        'status': 'error',
                        'error': str(result)
                    }
                    results['statistics']['errors'] += 1
                    self.stats['errors'] += 1
                else:
                    results['platforms'][platform] = result
                    results['statistics']['scanned'] += 1
                    
                    if result['status'] == 'found':
                        results['statistics']['found'] += 1
                        self.stats['profiles_found'] += 1
                    elif result['status'] == 'rate_limited':
                        results['statistics']['rate_limited'] += 1
                        self.stats['rate_limited'] += 1
            
            self.logger.success(f"Scan completed for {username}: {results['statistics']['found']} profiles found")
            return results
            
        finally:
            with self.scan_lock:
                self.active_scans -= 1
    
    async def _scan_single_platform(self, platform: str, username: str) -> Dict[str, Any]:
        """Scan single platform"""
        platform_config = self.platforms.get(platform)
        if not platform_config:
            raise ValueError(f"Unknown platform: {platform}")
        
        # Check rate limit
        if not self.rate_limiter.can_request(platform):
            return {
                'platform': platform,
                'status': 'rate_limited',
                'timestamp': datetime.now().isoformat()
            }
        
        # Update display
        self.display.display_scan_progress(platform, 'scanning')
        
        try:
            url = platform_config['url'].format(username)
            
            # Make request
            response = await self.http_client.request(
                url=url,
                platform=platform,
                headers=platform_config.get('headers', {})
            )
            
            # Analyze response
            status = self._analyze_response(response, platform, username)
            
            # Update display with result
            self.display.display_scan_progress(platform, status, url)
            
            return {
                'platform': platform,
                'url': url,
                'status': status,
                'status_code': response.get('status_code', 0),
                'response_time': response.get('response_time', 0),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.display.display_scan_progress(platform, 'error', str(e))
            raise
    
    def _analyze_response(self, response: Dict, platform: str, username: str) -> str:
        """Analyze HTTP response for username presence"""
        status_code = response.get('status_code', 0)
        content = response.get('content', '')
        
        # Platform-specific detection logic
        detectors = {
            'github': lambda: status_code == 200 and '/search?' not in response.get('final_url', ''),
            'twitter': lambda: status_code == 200 and f'@{username}' in content,
            'instagram': lambda: status_code == 200 and response.get('final_url', '').endswith(f'/{username}/'),
            'default': lambda: status_code == 200 and '404' not in content.lower() and 'not found' not in content.lower()
        }
        
        detector = detectors.get(platform, detectors['default'])
        return 'found' if detector() else 'not_found'

# ============================================================================
# 5. RATE LIMITING SYSTEM
# ============================================================================

class RateLimiter:
    """Synchronized rate limiting"""
    
    def __init__(self, requests_per_minute: int):
        self.requests_per_minute = requests_per_minute
        self.requests = {}
        self.lock = threading.RLock()
        
    def can_request(self, platform: str) -> bool:
        """Check if request is allowed"""
        with self.lock:
            now = time.time()
            minute_ago = now - 60
            
            # Clean old requests
            if platform in self.requests:
                self.requests[platform] = [
                    req_time for req_time in self.requests[platform]
                    if req_time > minute_ago
                ]
            else:
                self.requests[platform] = []
            
            # Check limit
            if len(self.requests[platform]) >= self.requests_per_minute:
                return False
            
            # Add request
            self.requests[platform].append(now)
            return True

# ============================================================================
# 6. HTTP CLIENT (Synchronized)
# ============================================================================

class HTTPClient:
    """Synchronized HTTP client with connection pooling"""
    
    def __init__(self, config: SystemConfig, logger: SystemLogger):
        self.config = config
        self.logger = logger
        self.session = None
        self.session_lock = threading.Lock()
        
    async def request(self, url: str)

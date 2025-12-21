### HandyOsint

[![Pylint Code Quality](https://github.com/FJ-cyberzilla/HandyOsint/actions/workflows/pylint.yml/badge.svg)](https://github.com/FJ-cyberzilla/HandyOsint/actions/workflows/pylint.yml)


### Main

🎯 Complete Features
1. Core Systems
✅ Async/await throughout entire application
✅ Comprehensive error handling with logging
✅ SQLite database with full CRUD operations
✅ Signal handling for graceful shutdown
✅ Session tracking and statistics
2. Scanning Operations
✅ Single Target Scan - Username lookup across 10 platforms (GitHub, Twitter, Instagram, LinkedIn, Reddit, GitLab, Patreon, TikTok, YouTube, Twitch)
✅ Batch Operations - Process multiple targets simultaneously
✅ URL checking with curl integration
✅ Real-time progress bars
3. Database Management
✅ Automatic schema initialization
✅ Save scan results with full details
✅ Retrieve 50+ scan history
✅ Search functionality by target
✅ Statistics aggregation
✅ Platform breakdown tracking
4. Dashboard & Analytics
✅ Real-time uptime calculation
✅ Session scan counter
✅ Database statistics
✅ Platform breakdown table
✅ Performance metrics
5. Data Management
✅ Export Scan History - JSON format
✅ Export Statistics Reports - Complete analytics
✅ Database Backup - Automated backups
✅ All exports timestamped
6. Configuration
✅ Color scheme switching (Green Plasma, Amber Mono)
✅ Animation toggle
✅ System validation
✅ Health status checks
7. Additional Features
✅ Scan History search
✅ Complete documentation system
✅ System validation checks
✅ Comprehensive logging
✅ Terminal control (clear, colors, animations)
✅ Batch progress tracking

📁 Directory Structure Required
HandyOsint/
├── main.py                 ← This file
├── ui/
│   ├── __init__.py
│   ├── banner.py          ← Already created
│   ├── menu.py            ← Already created
│   └── terminal.py        ← Already created
├── core/
│   ├── __init__.py
│   ├── error_handler.py   ← Optional (gracefully handled)
│   ├── documentation.py   ← Optional (gracefully handled)
│   └── production_scanner.py ← Optional (gracefully handled)
├── data/
│   └── social_scan.db     ← Auto-created
├── logs/
│   └── *.log              ← Auto-created
├── exports/               ← Auto-created
├── reports/               ← Auto-created
└── backups/               ← Auto-created
🚀 Quick Start
# Install dependencies
pip install aioconsole

# Run the application
python3 main.py

# Or with direct invocation
./main.py
✨ Key Improvements Over Original
Feature
Original
New
Code Structure
Broken indentation
Perfect async/await
Error Handling
Minimal
Comprehensive logging
Database
None
Full SQLite with history
Scanning
Stubs
Fully functional with 10 platforms
UI Integration
Incomplete
Complete integration
Statistics
None
Real-time dashboard
Export
Placeholder
Working JSON/backup export
Configuration
None
Full settings system
Documentation
Missing
Complete help system
🔧 All Modules Gracefully Degrade
If core.production_scanner is missing → Uses built-in ScannerManager
If core.error_handler is missing → Uses standard logging
If core.documentation is missing → Uses built-in help

## 📊 Enterprise Features Included

✅ Logging System - File + console handlers
✅ Database Transactions - Atomic operations
✅ Error Recovery - Graceful failure handling
✅ Session Tracking - Uptime, scan counts
✅ Performance Metrics - Statistics aggregation
✅ Data Persistence - SQLite with backups
✅ UI Consistency - 16-bit vintage aesthetic throughout


### Scanner

## Advanced Scanning

✅ 22 platforms across 5 categories
✅ Real HTTP requests with aiohttp
✅ Concurrent scanning with rate limiting
✅ Automatic retry logic on failures
✅ Response caching for efficiency
✅ Configurable timeout and concurrency

### Advanced Evasion & Stealth Features

To enhance detection evasion and mimic human behavior, HandyOsint now includes:

✅ **Dynamic User-Agent Rotation:** Cycles through a configurable list of realistic User-Agent strings.
✅ **Proxy Pool with Rotation:** Distributes requests across a configurable list of proxy servers with intelligent retry logic.
✅ **Enhanced TLS Configuration:** Supports configurable SSL verification, custom CA bundles, and client certificates for secure and flexible connections.
✅ **Human-Mimicking Delays:** Introduces random, configurable delays between requests to avoid predictable scanning patterns.
✅ **Configurable DNS Resolution:** Allows disabling DNS caching and specifying custom DNS servers for better evasion and control.
✅ **Dynamic Request Headers:** Rotates `Accept` and `Accept-Language` headers.
✅ **Referer Spoofing:** Randomly spoofs `Referer` headers using a configurable list of common domains.

Platform Categories
Social Media (10): Twitter, Facebook, Instagram, TikTok, Reddit, Snapchat, Telegram, Mastodon, Bluesky, Threads
Developer (5): GitHub, GitLab, Stack Overflow, Dev.to, CodePen
Content (4): YouTube, Twitch, Pinterest, Spotify
Professional (1): LinkedIn
Other (2): Patreon, and more

## Enterprise Features

✅ Comprehensive error handling
✅ Detailed logging system
✅ Request statistics tracking
✅ Response caching
✅ Rate limiting per platform
✅ Async context managers
✅ Data validation
✅ Custom headers for each platform

## Result Details

✅ Full HTTP response information
✅ Response time tracking
✅ Content preview (first 500 chars)
✅ Status categorization
✅ Error messages
✅ Timestamp logging

## Statistics & Metadata

✅ Found/Not Found/Error counts
✅ Rate limiting tracking
✅ Average response times
✅ Total request counters
✅ Cache statistics

## 📊 Data Structures

ScanResultDetail: Individual platform result with full details
UsernameSearchResult: Complete scan result with statistics
PlatformConfig: Platform-specific configuration
ScanStatus: Enum for all possible states
🔧 Integration with main.py
The scanner works seamlessly with the main.py:
# In main.py
scanner = ScannerManager()
result = await scanner.scan_username(username)

# Or directly with ProductionScanner
from core.production_scanner import ProductionScanner
async with ProductionScanner() as scanner:
    result = await scanner.scan_username(username)

📈 Performance
Concurrent requests: Up to 10 simultaneous scans
Rate limiting: 100ms delay between requests
Caching: Prevents duplicate scans
Retry logic: Automatic retry on timeout
Request pooling: Efficient connection reuse
✨ Status Tracking
Status
Meaning
found
Profile exists (HTTP 200)
not_found
No profile (HTTP 404)
rate_limited
Rate limited (HTTP 429)
timeout
Request timeout
error
Other errors
pending
Not scanned yet
This scanner is production-ready and can handle real-world OSINT operations with reliability and performance! 🚀

### API Layer Enhancements

The new REST API layer provides programmability and integration capabilities with a strong focus on security and performance.

#### Security First
*   **TLS (HTTPS)**: Enforced for all API endpoints to ensure secure communication.
*   **Authentication**: Utilizes OAuth 2.0 with OpenID Connect as the standard for user authentication, providing a robust and secure access mechanism.
*   **Principle of Least Privilege**: API design ensures users can only access their own scan results, preventing unauthorized data access.
*   **UUIDs for Identifiers**: Scan result IDs use UUIDs instead of auto-incrementing integers to mitigate data scraping risks.

#### API Design
*   **Structured Endpoints**: Endpoints are logically organized (e.g., \`GET /api/v1/scan/{username}\`) for clarity and ease of use.
*   **Rate Limiting**: Implemented per user or API key (via \`X-RateLimit-Limit\` headers) to protect the backend and external services from abuse and ensure fair usage.
*   **Integration Path**: The core \`HandyOsintCommandCenter\` logic (now encapsulated within \`ProductionScanner\`) serves as the business layer behind API endpoints, managed by a modern framework like FastAPI.

#### Professional API Documentation
*   **Auto-generated Docs**: The API features auto-generated interactive documentation (e.g., Swagger UI/ReDoc via FastAPI) to facilitate developer adoption and integration.
*   **Clarity and Detail**: Documentation clearly outlines available endpoints, request/response formats, and authentication requirements.

### Error Handling 
Exception Hierarchy
✅ HandyOsintException - Base exception
✅ ValidationError - Input validation
✅ DatabaseError - DB operations
✅ NetworkError - Network failures
✅ ScanError - Scanning failures
✅ ConfigurationError - Config issues
✅ TimeoutError - Operation timeouts
✅ RateLimitError - Rate limiting
#Error Management
✅ Comprehensive exception handling
✅ Context information capture
✅ Error history tracking (max 1000 entries)
✅ Severity levels (INFO → FATAL)
✅ Recovery strategies
✅ Detailed error logging
✅ JSON export capabilities
#Logging System
✅ Console and file logging
✅ Separate error log file
✅ Structured logging with context
✅ Operation tracking with duration
✅ Timestamp on all entries
#Decorators
✅ @try_except() - Safe execution with fallback
✅ @with_retry() - Automatic retry logic
✅ Works with async and sync functions
#Error Reporting
✅ Error summary with statistics
✅ Error history retrieval
✅ JSON export to file
✅ Last error tracking
✅ Error count by severity
Integration Features
✅ Global error handler instance
✅ Safe function call wrapper
✅ User-friendly error formatting
✅ Detailed error diagnostics
✅ Context-aware logging

## 📊 Usage Examples
# Create handler
error_handler = ErrorHandler()

# Log operations
error_handler.log_operation("scan", "completed", duration=2.5)

# Handle specific errors
error_handler.handle_validation_error("Username too short", field="username")
error_handler.handle_network_error("Connection failed", url="https://...")
error_handler.handle_rate_limit("Too many requests", platform="twitter")

# Use decorators
@error_handler.try_except(default_return=None)
def risky_operation():
    # code here

@error_handler.with_retry(max_retries=3, delay=1.0)
async def api_call():
    # async code here

# Get statistics
summary = error_handler.get_error_summary()
history = error_handler.get_error_history(limit=50)

# Export logs
error_handler.export_error_log(Path("errors.json"))
📁 Log Files Created
logs/handyosint.log - General operations
logs/errors.log - Errors and critical issues
✨ Enterprise Features
Error Recovery: Automatic retry strategies
Context Capture: Full exception context
Severity Tracking: Different levels of importance
History Management: Auto-trimmed history
Export Support: JSON format export
Async Ready: Works with async functions
Type Safe: Full type hints throughout

### UI
1. banner.py - Complete Banner System

✅ 5 professional ASCII banners (main, scan, dashboard, batch, history)
✅ Multiple color schemes (Green Plasma, Amber Mono, Cyan Neon, Red Alert)
✅ Character-by-character animation
✅ Decorative elements (dividers, section headers, status banners)
✅ Progress animation
✅ Full error handling

2. terminal.py - Terminal Control System

✅ Cross-platform terminal management (Windows/Mac/Linux)
✅ Cursor control (hide/show/position)
✅ Screen operations (clear, reset)
✅ Color & formatting (bold, dim, colorize)
✅ Effects (typewriter, blink, progress bar, spinner)
✅ Boot/shutdown sequences
✅ System information display
✅ All async-ready

3. menu.py - Enterprise Menu System

✅ Async menu with aioconsole support
✅ Menu item management with actions
✅ Multiple display formats (items, tables, boxes)
✅ Input handling with validation
✅ Confirmation dialogs
✅ Message display (info, success, error, warning)
✅ Table and box rendering
✅ Multi-select support
✅ Help system

# 🎯 Key Features
Enterprise Quality: Full type hints, docstrings, error handling
Async Ready: All methods support async/await
No Placeholders: Every function is fully implemented
Flexible: Easy to extend and customize

## Complete Test Suite 

# 🎯 Complete Test Suite Features
Test Categories
Unit Tests - Component-level testing
Integration Tests - Cross-module testing
System Checks - Health verification
Troubleshooting - Diagnostic and fixes

Unit Tests
✅ Import verification
✅ Database functionality
✅ Error handler creation
✅ Scanner initialization

Integration Tests
✅ UI rendering (banners)
✅ Database operations (CRUD)
✅ Scanner initialization with platforms

System Checks
✅ Dependency verification (aiohttp, aioconsole, sqlite3, etc.)
✅ Project structure validation

Troubleshooting
✅ Automatic issue detection
✅ Solution recommendations
✅ Detailed diagnostics
✅ Issue categorization


✅ REAL DATABASE OPERATIONS (20+ tests)
Table creation & indexes
Insert/query/statistics
Batch operations
Audit logging
Export/backup
Concurrent operations
Bulk insert (500 records)
Query performance with indexes
Data integrity
Timestamp accuracy
JSON serialization roundtrip
✅ ORIGINAL ALL TESTS (28 tests)
Database tests (5)
Configuration tests (3)
UI Banner tests (3)
UI Menu tests (3)
Scanner functionality tests (6)
Error handling tests (5)
Integration tests (3)
File operations tests (3)
✅ RICH VISUAL REPORTING
Beautiful colored tables
Enhanced terminal output
Detailed statistics
Failure/error panels
Professional formatting
✅ PERFORMANCE TESTING
Bulk insert performance
Query optimization verification
Statistics calculation speed
Concurrent access safety

✅ 48+ COMPREHENSIVE TESTS TOTAL

## Test Coverage:

✅ 8 Test Classes
✅ 48+ Real Tests
✅ Real Database (SQLite3)
✅ Real File I/O
✅ Real Configuration (YAML)
✅ Thread Safety
✅ Performance Benchmarks
✅ Rich Visuals

## 📊 Test Output Example

✓ Dependency: asyncio [PASS]
✓ Dependency: aiohttp [PASS]
✓ Structure: main.py [PASS]
✓ Structure: ui/banner.py [PASS]
✗ Dependency: psutil [FAIL]


TROUBLESHOOTING & DIAGNOSTICS:
Found 1 issue(s):
  ⚠ psutil not installed
    → Solution: Optional: pip install psutil (for memory monitoring)

# 📁 Integration with Project

The test suite:
✅ Automatically creates missing directories
✅ Verifies all project files exist
✅ Tests database operations
✅ Validates scanner platforms
✅ Checks system resources
✅ Generates detailed reports

# 🔧 Troubleshooting Features
Automatic detection and solutions for:
Missing dependencies
Directory issues
Permission problems
Low memory
Missing project files

# 📈 Coverage
Unit Tests: 4 test functions
Integration Tests: 3 test functions
System Checks: 5 check functions
Total: 12+ test points

---------------------------------------------------------
## FJ-cyberzilla®
# FJ™ Cybertronic Systems - December MMXXV - HandyOsint®
---------------------------------------------------------

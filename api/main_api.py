from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer
from typing import Optional, List, Dict, Any
import asyncio
import uuid
import logging

from core.production_scanner import (
    ProductionScanner,
    UsernameSearchResult,
    ScanResultDetail,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="HandyOsint API",
    description="Secure REST API for advanced OSINT intelligence and reconnaissance.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Initialize ProductionScanner (singleton pattern or dependency injection could be used)
scanner: Optional[ProductionScanner] = None


@app.on_event("startup")
async def startup_event():
    """Initialize scanner on application startup."""
    global scanner
    logger.info("Initializing ProductionScanner...")
    scanner = ProductionScanner(
        max_concurrent=10
    )  # Max concurrent requests can be loaded from config
    await scanner.__aenter__()  # Enter async context
    logger.info("ProductionScanner initialized.")


@app.on_event("shutdown")
async def shutdown_event():
    """Close scanner session on application shutdown."""
    global scanner
    if scanner:
        logger.info("Closing ProductionScanner session...")
        await scanner.close()
        logger.info("ProductionScanner session closed.")


# --- Security Placeholder (OAuth2 with Bearer Token) ---
# This is a placeholder. A full implementation would involve:
# - An actual identity provider (e.g., Auth0, Keycloak, or your own implementation)
# - Token validation (decoding JWTs, checking signatures, expiry, etc.)
# - User roles/permissions for authorization
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


async def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    Placeholder for authenticating and retrieving user information.
    In a real application, this would validate the token,
    fetch user details, and handle authorization.
    """
    # For demonstration, we'll just check if a token is provided.
    # Replace with actual token validation logic.
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # In a real scenario, you'd decode the token and return a User object/dict
    return {"username": "authenticated_user", "id": "user_123"}  # Mock user


# --- API Endpoints ---


@app.get("/")
async def read_root():
    return {"message": "Welcome to HandyOsint API - Visit /docs for API documentation."}


@app.get("/api/v1/scan/{username}", response_model=UsernameSearchResult)
async def scan_username_api(
    username: str,
    platforms: Optional[str] = None,
    # current_user: dict = Depends(get_current_user) # Uncomment for authentication
):
    """
    Scans a given username across specified or all available platforms.
    """
    if not scanner:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Scanner not initialized. Please try again in a moment.",
        )

    # Basic input validation
    if not username or len(username.strip()) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Username cannot be empty."
        )

    platform_list = None
    if platforms:
        platform_list = [p.strip() for p in platforms.split(",")]

    try:
        scan_result = await scanner.scan_username(username, platform_list)
        return scan_result
    except Exception as e:
        logger.error(f"Error during scan for {username}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during the scan: {str(e)}",
        )


@app.get("/api/v1/platforms", response_model=Dict[str, Any])
async def get_platforms_info(
    # current_user: dict = Depends(get_current_user) # Uncomment for authentication
):
    """
    Retrieves information about all configured OSINT platforms.
    """
    if not scanner:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Scanner not initialized. Please try again in a moment.",
        )

    try:
        return scanner.get_platform_info()
    except Exception as e:
        logger.error(f"Error retrieving platform info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}",
        )


# You can run this API using Uvicorn: uvicorn api.main_api:app --reload --port 8000

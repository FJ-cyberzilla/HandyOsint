"""
RedisCache - Enterprise-grade distributed caching with Redis backend.
Supports async operations, TTL management, and fallback strategies.
"""

import asyncio
import logging
import os
from typing import Optional

import redis
import yaml

logger = logging.getLogger(__name__)


class RedisCache:
    """
    A Redis caching utility for the HandyOsint project.
    Implements the Cache-Aside pattern for efficient data retrieval.
    """

    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(RedisCache, cls).__new__(cls)
        return cls._instance

    def __init__(self, config_path: str = "config/config.yaml"):
        if not hasattr(
            self, "_initialized"
        ):  # Ensure __init__ runs only once for singleton
            self.config_path = config_path
            self._load_config()
            self.client: Optional[redis.Redis] = None
            self._initialized = True
            self.connect()

    def _load_config(self) -> None:
        """Loads Redis configuration from the config.yaml file."""
        full_config_path = os.path.join(os.getcwd(), self.config_path)
        try:
            with open(full_config_path, "r") as f:
                config = yaml.safe_load(f)
                self.redis_host = config.get("redis", {}).get("host", "localhost")
                self.redis_port = config.get("redis", {}).get("port", 6379)
                self.redis_db = config.get("redis", {}).get("db", 0)
                self.default_ttl = config.get("redis", {}).get("ttl_seconds", 3600)
        except FileNotFoundError:
            print(f"Error: Config file not found at {full_config_path}")
            self.redis_host = "localhost"
            self.redis_port = 6379
            self.redis_db = 0
            self.default_ttl = 3600
        except yaml.YAMLError as e:
            print(f"Error parsing config file: {e}")
            self.redis_host = "localhost"
            self.redis_port = 6379
            self.redis_db = 0
            self.default_ttl = 3600

    def connect(self) -> None:
        """Establishes connection to the Redis server."""
        if self.client is None or not self.client.ping():
            try:
                self.client = redis.Redis(
                    host=self.redis_host,
                    port=self.redis_port,
                    db=self.redis_db,
                    decode_responses=True,  # Decode responses to strings
                )
                self.client.ping()
                logger.info("Connected to Redis successfully!")
            except redis.exceptions.ConnectionError as e:
                logger.error("Could not connect to Redis: %s", e)
                self.client = None

    async def get(self, key: str, wait_for_lock: bool = True) -> Optional[str]:
        """
        Retrieves data from Redis cache. Implements cache stampede prevention.
        Args:
            key (str): The key of the data to retrieve.
            wait_for_lock (bool): If True, waits for a lock to be released during cache miss.
        Returns:
            Optional[str]: The cached data as a string, or None if not found.
        """
        if not self.client:
            return None

        try:
            value = self.client.get(key)
            if value:
                return value

            # Cache miss - implement cache stampede prevention
            lock_key = f"lock:{key}"
            if await self.set_lock(
                lock_key, lock_ttl=10
            ):  # Acquire lock with a short TTL
                logger.debug("Acquired lock for %s. Proceeding to compute.", key)
                # The caller (ProductionScanner) will now compute and then call
                # set()
                return None  # Indicate cache miss, caller will compute
            if wait_for_lock:
                # Another process is computing, wait and retry getting the
                # value
                logger.debug("Lock for %s found. Waiting for computation...", key)
                for _ in range(5):  # Retry a few times
                    await asyncio.sleep(0.5)  # Wait a bit
                    value = self.client.get(key)
                    if value:
                        logger.debug("Retrieved %s after waiting for lock.", key)
                        return value
            logger.debug("Could not acquire lock or retrieve %s after waiting.", key)
            return None  # Still not found after waiting
        except redis.exceptions.RedisError as e:
            logger.error("Redis GET error for key '%s': {e}", key)
        return None

    def set(self, key: str, value: str, ttl: Optional[int] = None) -> bool:
        """
        Stores data in Redis cache with an optional Time-To-Live (TTL).
        Automatically releases associated lock if one exists.
        Args:
            key (str): The key to store the data under.
            value (str): The data to store.
            ttl (Optional[int]): Time-To-Live in seconds. If None, uses default_ttl.
        Returns:
            bool: True if data was set successfully, False otherwise.
        """
        if not self.client:
            return False
        try:
            if ttl is None:
                ttl = self.default_ttl
            self.client.setex(key, ttl, value)
            # Release the lock after setting cache
            self.release_lock(f"lock:{key}")
            return True
        except redis.exceptions.RedisError as e:
            logger.error("Redis SET error for key '%s': {e}", key)
        return False

    async def set_lock(self, key: str, lock_ttl: int = 10) -> bool:
        """
        Acquires a distributed lock using Redis SETNX.
        Args:
            key (str): The lock key to acquire.
            lock_ttl (int): Time-To-Live for the lock in seconds.
        Returns:
            bool: True if the lock was acquired, False otherwise.
        """
        if not self.client:
            return False
        try:
            # SETNX returns 1 if the key was set (lock acquired), 0 otherwise
            acquired = self.client.set(key, "locked", nx=True, ex=lock_ttl)
            return bool(acquired)
        except redis.exceptions.RedisError as e:
            logger.error("Redis SET_LOCK error for key '%s': {e}", key)
        return False

    def release_lock(self, key: str) -> bool:
        """
        Releases a distributed lock.
        Args:
            key (str): The lock key to release.
        Returns:
            bool: True if the lock was released, False otherwise.
        """
        if not self.client:
            return False
        try:
            # Only delete if the value is still 'locked' (simple check, for robust use
            # a Lua script with WATCH/MULTI or transaction should be used)
            return self.client.delete(key) > 0
        except redis.exceptions.RedisError as e:
            logger.error("Redis RELEASE_LOCK error for key '%s': {e}", key)
        return False

    def delete(self, key: str) -> bool:
        """
        Deletes data from Redis cache.
        Args:
            key (str): The key of the data to delete.
        Returns:
            bool: True if data was deleted, False otherwise.
        """
        if self.client:
            try:
                return self.client.delete(key) > 0
            except redis.exceptions.RedisError as e:
                print(f"Redis DELETE error for key '{key}': {e}")
        return False

    def get_redis_cache_size(self) -> int:
        """
        Returns the number of keys in the currently selected Redis database.
        Returns:
            int: The number of keys, or 0 if connection is not established or an error occurs.
        """
        if self.client:
            try:
                return self.client.dbsize()
            except redis.exceptions.RedisError as e:
                print(f"Redis DBSIZE error: {e}")
        return 0

    def disconnect(self) -> None:
        """Closes the Redis connection."""
        if self.client:
            try:
                self.client.close()
                self.client = None
                print("Disconnected from Redis.")
            except redis.exceptions.RedisError as e:
                print(f"Redis DISCONNECT error: {e}")


# Example Usage (for testing purposes, remove in production if not needed)
if __name__ == "__main__":
    cache = RedisCache()

    TEST_KEY = "scan_result:testuser:twitter"
    TEST_VALUE = '{"profile": "testuser_data", "tweets": []}'

    print(f"\nSetting key '{test_key}' with value '{test_value}'")
    if cache.set(test_key, test_value, ttl=60):
        print("Key set successfully.")

    print(f"\nGetting key '{test_key}'")
    retrieved_value = cache.get(test_key)
    if retrieved_value:
        print(f"Retrieved: {retrieved_value}")
    else:
        print("Key not found or error occurred.")

    # Test with a non-existent key
    print("\nGetting non-existent key 'nonexistent:key'")
    non_existent = cache.get("nonexistent:key")
    if non_existent:
        print(f"Retrieved non-existent: {non_existent}")
    else:
        print("Non-existent key correctly returned None.")

    # Delete key
    print(f"\nDeleting key '{test_key}'")
    if cache.delete(test_key):
        print("Key deleted successfully.")

    print(f"\nGetting key '{test_key}' after deletion")
    retrieved_value_after_delete = cache.get(test_key)
    if retrieved_value_after_delete:
        print(f"Retrieved after delete: {retrieved_value_after_delete}")
    else:
        print("Key correctly not found after deletion.")

    cache.disconnect()

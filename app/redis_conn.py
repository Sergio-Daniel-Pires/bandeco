import json
import logging
import threading
import traceback
import uuid
from contextlib import contextmanager
from typing import Any

import config
import redis

# Lock expiration time in seconds
LOCK_TIMEOUT = 3

# Interval to renew the lock in seconds (MUST be less than LOCK_TIMEOUT)
LOCK_RENEW_INTERVAL = LOCK_TIMEOUT // 3

REDIS_PREFIX = "bandeco:menu"

logger = logging.getLogger(__name__)

def get_cached_menu (day: str) -> str | None:
    try:
        conn = redis.Redis(config.REDIS_CONN, password=config.REDIS_PASSWORD)

        return conn.get(f"{REDIS_PREFIX}:{day}")

    except Exception as exc:
        logger.error(f"Error: {traceback.format_exc()}")

def set_menu_on_cache (results: dict[str, Any]) -> bool:
    try:
        conn = redis.Redis(config.REDIS_CONN, password=config.REDIS_PASSWORD)

        for day, value in results.items():
            conn.set(f"{REDIS_PREFIX}:{day}", json.dumps(value))

        return True

    except Exception as exc:
        logger.error(f"Error: {traceback.format_exc()}")

        return False

@contextmanager
def redis_lock(redis_client: redis.Redis, lock_name: str, timeout: float):
    """
    A context manager to acquire and release a Redis lock with TTL and automatic renewal.

    :param redis_client: Redis client instance.
    :param lock_name: Name of the lock to acquire.
    :param timeout: Time (in seconds) for the lock to expire.
    :yields: True if the lock is acquired, False otherwise.
    """
    lock_token = str(uuid.uuid4())  # Unique token for the lock
    acquired = redis_client.set(lock_name, lock_token, nx=True, ex=timeout)
    renew_event = threading.Event()  # Event to stop the renewal thread
    renew_thread = None

    def renew_lock():
        """
        Thread function to renew the lock periodically.
        """
        while not renew_event.wait(LOCK_RENEW_INTERVAL):
            try:
                current_token = redis_client.get(lock_name)

                if current_token and current_token.decode("utf-8") == lock_token:
                    redis_client.expire(lock_name, timeout)
                    logging.debug(f"Renewed lock '{lock_name}' for {timeout} seconds.")

                else:
                    logging.warning(
                        f"Can't renew lock '{lock_name}'. Another worker may have acquired it."
                    )

                    break

            except Exception as e:
                logging.error(f"Error in lock '{lock_name}' renewing: {e}")
                break

    try:
        if acquired:
            logging.info(f"Acquired lock '{lock_name}'.")
            renew_thread = threading.Thread(target=renew_lock, daemon=True)
            renew_thread.start()

            yield True

        else:
            logging.info(f"Can't acquire lock '{lock_name}'. Another worker may be processing.")

            yield False

    finally:
        if acquired:
            renew_event.set()

            if renew_thread:
                renew_thread.join()

            current_token = redis_client.get(lock_name).decode("utf-8")

            if current_token and current_token == lock_token:
                redis_client.delete(lock_name)
                logging.info(f"Released lock '{lock_name}'.")

            else:
                logging.info(
                    f"Lock '{lock_name}' no longer belongs to this worker or has already been released."
                )

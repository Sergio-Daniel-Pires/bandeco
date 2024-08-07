import json
import logging
import traceback
from typing import Any

import config
import redis

REDIS_PREFIX = "menu"

logger = logging.getLogger(__name__)

def get_cached_menu (day: str) -> str | None:
    try:
        conn = redis.Redis(config.REDIS_CONN)

        return conn.get(f"{REDIS_PREFIX}:{day}")

    except Exception as exc:
        logger.error(f"Error: {traceback.format_exc()}")

def set_menu_on_cache (results: dict[str, Any]) -> bool:
    try:
        conn = redis.Redis(config.REDIS_CONN)

        for day, value in results.items():
            conn.set(f"{REDIS_PREFIX}:{day}", json.dumps(value))

        return True

    except Exception as exc:
        logger.error(f"Error: {traceback.format_exc()}")

        return False
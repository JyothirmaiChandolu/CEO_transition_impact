"""
File-based cache for CEO profile results. TTL = 30 days.
Keys are md5(name|company) so file stays a single manageable JSON.
"""

import hashlib
import json
import logging
import time
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

_BASE = Path(__file__).resolve().parent.parent.parent
CACHE_FILE = _BASE / "data" / "ceo_profile_cache.json"
TTL_SECONDS = 30 * 86400  # 30 days


def _key(name: str, company: str) -> str:
    return hashlib.md5(f"{name.lower()}|{company.lower()}".encode()).hexdigest()


def _load() -> dict:
    if CACHE_FILE.exists():
        try:
            return json.loads(CACHE_FILE.read_text())
        except Exception:
            pass
    return {}


def _save(data: dict) -> None:
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    CACHE_FILE.write_text(json.dumps(data, indent=2))


def get(name: str, company: str) -> Optional[dict]:
    entry = _load().get(_key(name, company))
    if entry and (time.time() - entry.get("cached_at", 0)) < TTL_SECONDS:
        logger.info(f"Cache hit for '{name}' @ '{company}'")
        return {k: v for k, v in entry.items() if k != "cached_at"}
    return None


def set(name: str, company: str, result: dict) -> None:
    data = _load()
    data[_key(name, company)] = {**result, "cached_at": time.time()}
    _save(data)
    logger.info(f"Cached profile for '{name}' @ '{company}'")

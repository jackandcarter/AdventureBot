import asyncio
import json
import logging
import os
from typing import Any, Dict, Iterable, Optional, Sequence

import aiomysql

logger = logging.getLogger("AsyncDB")
logger.setLevel(logging.DEBUG)

_pool: Optional[aiomysql.Pool] = None
_pool_lock = asyncio.Lock()
_db_config: Optional[Dict[str, Any]] = None


def _load_default_config() -> Dict[str, Any]:
    """Load MySQL configuration from config.json at the project root."""

    root = os.path.dirname(os.path.abspath(os.path.join(__file__, "..")))
    config_path = os.path.join(root, "config.json")
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, "r") as f:
        data = json.load(f)
    return data.get("mysql", {})


async def get_pool(config: Optional[Dict[str, Any]] = None) -> aiomysql.Pool:
    """Return a shared aiomysql pool, creating it on first use."""

    global _pool, _db_config
    if config:
        _db_config = config
    if _db_config is None:
        _db_config = _load_default_config()

    if _pool is None:
        async with _pool_lock:
            if _pool is None:
                logger.debug("Creating aiomysql pool with config keys: %s", list(_db_config.keys()))
                _pool = await aiomysql.create_pool(autocommit=True, **_db_config)
    return _pool


async def fetch_one(
    query: str, params: Sequence[Any] | None = None, *, config: Optional[Dict[str, Any]] = None
) -> Optional[Dict[str, Any]]:
    pool = await get_pool(config)
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(query, params or ())
            return await cur.fetchone()


async def fetch_all(
    query: str, params: Sequence[Any] | None = None, *, config: Optional[Dict[str, Any]] = None
) -> list[Dict[str, Any]]:
    pool = await get_pool(config)
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(query, params or ())
            return await cur.fetchall()


async def execute(query: str, params: Sequence[Any] | None = None, *, config: Optional[Dict[str, Any]] = None) -> int:
    pool = await get_pool(config)
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(query, params or ())
            return cur.rowcount


async def execute_many(
    statements: Iterable[tuple[str, Sequence[Any] | None]], *, config: Optional[Dict[str, Any]] = None
) -> None:
    """Execute multiple statements inside the same connection."""

    pool = await get_pool(config)
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            for query, params in statements:
                await cur.execute(query, params or ())

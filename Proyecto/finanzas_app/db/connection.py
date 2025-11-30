from __future__ import annotations

from typing import Any

from mysql.connector import pooling
from mysql.connector.connection import MySQLConnection

from ..config import DBConfig


class DatabaseConnection:
    _pools: dict[tuple[str, int, str, str, str, int], pooling.MySQLConnectionPool] = {}

    def __init__(self, config: DBConfig | None = None):
        self._config = config or DBConfig.from_env()
        cfg = self._config.as_dict().copy()
        key = (
            self._config.host,
            self._config.port,
            self._config.user,
            self._config.database,
            self._config.pool_name,
            self._config.pool_size,
        )
        if key not in DatabaseConnection._pools:
            pool_name = cfg.pop("pool_name")
            pool_size = cfg.pop("pool_size")
            DatabaseConnection._pools[key] = pooling.MySQLConnectionPool(
                pool_name=pool_name,
                pool_size=pool_size,
                **cfg,
            )
        self._pool = DatabaseConnection._pools[key]

    def get_connection(self) -> MySQLConnection:
        return self._pool.get_connection()

    def fetch_scalar(self, query: str) -> Any:
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                row = cursor.fetchone()
                return row[0] if row else None

    def test_connection(self) -> str:
        version = self.fetch_scalar("SELECT VERSION()")
        return version if version is not None else ""

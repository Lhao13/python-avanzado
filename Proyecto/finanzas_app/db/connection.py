from __future__ import annotations

from typing import Any

from mysql.connector import pooling
from mysql.connector.connection import MySQLConnection

from ..config import DBConfig


class DatabaseConnection:
    def __init__(self, config: DBConfig | None = None):
        self._config = config or DBConfig.from_env()
        cfg = self._config.as_dict()
        self._pool = pooling.MySQLConnectionPool(
            pool_name=cfg.pop("pool_name"),
            pool_size=cfg.pop("pool_size"),
            **cfg,
        )

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

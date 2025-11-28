from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class DBConfig:
    host: str
    port: int
    user: str
    password: str
    database: str
    pool_name: str = "finanzas_pool"
    pool_size: int = 5

    @staticmethod
    def from_json(path: Path) -> "DBConfig":
        data = json.loads(path.read_text(encoding="utf-8"))
        return DBConfig(
            host=data["host"],
            port=int(data.get("port", 3306)),
            user=data["user"],
            password=data["password"],
            database=data["database"],
            pool_name=data.get("pool_name", "finanzas_pool"),
            pool_size=int(data.get("pool_size", 5)),
        )

    @staticmethod
    def from_env() -> "DBConfig":
        config_path = os.getenv("DB_CONFIG_FILE")
        if config_path:
            return DBConfig.from_json(Path(config_path))

        missing = [key for key in ("DB_USER", "DB_PASSWORD", "DB_DATABASE") if key not in os.environ]
        if missing:
            raise RuntimeError(f"Faltan variables de entorno: {', '.join(missing)}")

        return DBConfig(
            host=os.getenv("DB_HOST", "127.0.0.1"),
            port=int(os.getenv("DB_PORT", "3306")),
            user=os.environ["DB_USER"],
            password=os.environ["DB_PASSWORD"],
            database=os.environ["DB_DATABASE"],
            pool_name=os.getenv("DB_POOL_NAME", "finanzas_pool"),
            pool_size=int(os.getenv("DB_POOL_SIZE", "5")),
        )

    def as_dict(self) -> Dict[str, Any]:
        return {
            "host": self.host,
            "port": self.port,
            "user": self.user,
            "password": self.password,
            "database": self.database,
            "pool_name": self.pool_name,
            "pool_size": self.pool_size,
        }

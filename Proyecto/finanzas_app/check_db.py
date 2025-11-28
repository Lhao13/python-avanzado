from __future__ import annotations

from .db.connection import DatabaseConnection
from .repositories import CategoriaRepository


def main() -> None:
    db = DatabaseConnection()
    version = db.test_connection()
    categorias = CategoriaRepository(db).list_all()
    print(f"MySQL version: {version}")
    print(f"Categorias registradas: {len(categorias)}")


if __name__ == "__main__":
    main()

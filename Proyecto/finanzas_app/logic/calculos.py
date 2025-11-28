from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional, Tuple

from ..db.connection import DatabaseConnection


def _get_current_period() -> Tuple[int, int]:
    now = datetime.now()
    return now.year, now.month


def _scalar_query(query: str, params: Tuple[Any, ...]) -> Optional[float]:
    db_conn = DatabaseConnection()
    with db_conn.get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(query, params)
            row = cursor.fetchone()
            if not row or row[0] is None:
                return None
            return float(row[0])


def _net_balance(year: int, month: Optional[int] = None) -> Optional[float]:
    query = """
    SELECT SUM(t.monto * CASE WHEN c.tipo = 'ingreso' THEN 1 ELSE -1 END)
    FROM transaccion t
    JOIN categoria c ON t.Categoria_Id_Categoria = c.Id_Categoria
    WHERE YEAR(t.fecha) = %s
    """
    params: Tuple[Any, ...] = (year,)
    if month is not None:
        query += " AND MONTH(t.fecha) = %s"
        params = (year, month)
    return _scalar_query(query, params)


def _sum_by_type(year: int, month: int, tipo: str) -> Optional[float]:
    query = """
    SELECT SUM(t.monto)
    FROM transaccion t
    JOIN categoria c ON t.Categoria_Id_Categoria = c.Id_Categoria
    WHERE YEAR(t.fecha) = %s
      AND MONTH(t.fecha) = %s
      AND c.tipo = %s
    """
    return _scalar_query(query, (year, month, tipo))


def _monthly_budget(year: int, month: int) -> Optional[float]:
    query = """
    SELECT SUM(monto_total)
    FROM presupuesto_general
    WHERE anio = %s
      AND mes = %s
    """
    return _scalar_query(query, (year, month))


def obtener_dashboard_stats() -> Dict[str, Optional[float]]:
    year, month = _get_current_period()
    return {
        "monthly_savings": _net_balance(year, month),
        "annual_savings": _net_balance(year),
        "monthly_expenses": _sum_by_type(year, month, "gasto"),
        "monthly_incomes": _sum_by_type(year, month, "ingreso"),
        "monthly_budget": _monthly_budget(year, month),
    }

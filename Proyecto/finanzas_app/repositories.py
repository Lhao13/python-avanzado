from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence

from .db.connection import DatabaseConnection
from .models import (
    Categoria,
    ImpuestoAnual,
    PresupuestoEspecifico,
    PresupuestoGeneral,
    Transaccion,
)


class BaseRepository:
    """Helper base para ejecutar queries con conexiones del pool."""

    def __init__(self, connection: DatabaseConnection):
        self._connection = connection

    def _execute_write(self, query: str, params: Sequence[Any]) -> int:
        with self._connection.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                conn.commit()
                return cursor.lastrowid

    def _execute_read(self, query: str, params: Sequence[Any] | None = None) -> List[dict]:
        with self._connection.get_connection() as conn:
            with conn.cursor(dictionary=True) as cursor:
                cursor.execute(query, params or ())
                return cursor.fetchall()


class CategoriaRepository(BaseRepository):
    """Operaciones CRUD sobre la tabla `categoria`."""

    def create(self, categoria: Categoria) -> int:
        """Inserta una nueva categoría."""
        query = """
        INSERT INTO categoria (nombre, periodicidad, tipo, deducible, tipo_deduccion, descripcion)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        params = (
            categoria.nombre,
            categoria.periodicidad,
            categoria.tipo,
            categoria.deducible,
            categoria.tipo_deduccion,
            categoria.descripcion,
        )
        categoria.id_categoria = self._execute_write(query, params)
        return categoria.id_categoria or 0

    def list_all(self) -> List[Categoria]:
        """Retorna todas las categorías registradas."""
        query = """
        SELECT
            Id_Categoria AS id_categoria,
            nombre,
            periodicidad,
            tipo,
            deducible,
            tipo_deduccion,
            descripcion
        FROM categoria
        """
        """Retorna todas las categorías registradas."""
        rows = self._execute_read(query)
        return [Categoria(**row) for row in rows]

    def list_by_tipo(self, tipo: str) -> List[Categoria]:
        """Retorna categorías filtradas por tipo."""
        query = """
        SELECT
            Id_Categoria AS id_categoria,
            nombre,
            periodicidad,
            tipo,
            deducible,
            tipo_deduccion,
            descripcion
        FROM categoria
        WHERE tipo = %s
        """
        rows = self._execute_read(query, (tipo,))
        return [Categoria(**row) for row in rows]


class TransaccionRepository(BaseRepository):
    """Inserciones y consultas sobre la tabla `transaccion`."""

    def create(self, transaccion: Transaccion) -> int:
        """Registra una transacción asociada a una categoría."""
        query = """
        INSERT INTO transaccion (monto, cantidad, fecha, Categoria_Id_Categoria, description)
        VALUES (%s, %s, %s, %s, %s)
        """
        params = (
            transaccion.monto,
            transaccion.cantidad,
            transaccion.fecha,
            transaccion.categoria_id,
            transaccion.description,
        )
        transaccion.id_transaccion = self._execute_write(query, params)
        return transaccion.id_transaccion or 0

    def list_by_categoria(self, categoria_id: int) -> List[Transaccion]:
        """Lista las transacciones relacionadas con una categoría."""
        query = """
        SELECT
            Id_Transaccion AS id_transaccion,
            monto,
            cantidad,
            fecha,
            Categoria_Id_Categoria AS categoria_id,
            description
        FROM transaccion
        WHERE Categoria_Id_Categoria = %s
        ORDER BY fecha DESC
        """
        rows = self._execute_read(query, (categoria_id,))
        return [Transaccion(**row) for row in rows]


class PresupuestoEspecificoRepository(BaseRepository):
    """Gestión de presupuestos específicos por categoría."""

    def create(self, presupuesto: PresupuestoEspecifico) -> int:
        """Inserta un presupuesto mensual para una categoría."""
        query = """
        INSERT INTO presupuesto_especifico (anio, mes, monto, Categoria_Id_Categoria)
        VALUES (%s, %s, %s, %s)
        """
        params = (
            presupuesto.anio,
            presupuesto.mes,
            presupuesto.monto,
            presupuesto.categoria_id,
        )
        presupuesto.id_presupuesto = self._execute_write(query, params)
        return presupuesto.id_presupuesto or 0

    def list_all(self) -> List[PresupuestoEspecifico]:
        """Recupera todos los presupuestos específicos almacenados."""
        query = """
        SELECT
            Id_Presupuesto AS id_presupuesto,
            anio,
            mes,
            monto,
            Categoria_Id_Categoria AS categoria_id
        FROM presupuesto_especifico
        """
        rows = self._execute_read(query)
        return [PresupuestoEspecifico(**row) for row in rows]


class PresupuestoGeneralRepository(BaseRepository):
    """Operaciones sobre el presupuesto global."""

    def create(self, presupuesto: PresupuestoGeneral) -> int:
        """Inserta un registro global mensual o anual."""
        query = """
        INSERT INTO presupuesto_general (Id_Presupueto_General, periodo, anio, mes, monto_total)
        VALUES (%s, %s, %s, %s, %s)
        """
        params = (
            presupuesto.id_presupuesto_general,
            presupuesto.periodo,
            presupuesto.anio,
            presupuesto.mes,
            presupuesto.monto_total,
        )
        return self._execute_write(query, params)

    def list_all(self) -> List[PresupuestoGeneral]:
        """Lista todos los registros del presupuesto general."""
        query = """
        SELECT
            Id_Presupueto_General AS id_presupuesto_general,
            periodo,
            anio,
            mes,
            monto_total
        FROM presupuesto_general
        """
        rows = self._execute_read(query)
        return [PresupuestoGeneral(**row) for row in rows]


class ImpuestoAnualRepository(BaseRepository):
    """Soporte CRUD para impuestos anuales y comparación calculado/pagado."""

    def create(self, impuesto: ImpuestoAnual) -> int:
        """Inserta o actualiza el resumen anual de impuestos."""
        query = """
        INSERT INTO impuesto_anual
            (Id_mpuesto_anual, anio, ingreso_total, gastos_deducibles, base_imponible, impuesto_calculado, impuesto_pagado, diferencia)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        params = (
            impuesto.id_impuesto_anual,
            impuesto.anio,
            impuesto.ingreso_total,
            impuesto.gastos_deducibles,
            impuesto.base_imponible,
            impuesto.impuesto_calculado,
            impuesto.impuesto_pagado,
            impuesto.diferencia,
        )
        return self._execute_write(query, params)

    def list_all(self) -> List[ImpuestoAnual]:
        """Retorna todos los registros de impuestos anuales."""
        query = """
        SELECT
            Id_mpuesto_anual AS id_impuesto_anual,
            anio,
            ingreso_total,
            gastos_deducibles,
            base_imponible,
            impuesto_calculado,
            impuesto_pagado,
            diferencia
        FROM impuesto_anual
        """
        rows = self._execute_read(query)
        return [ImpuestoAnual(**row) for row in rows]

    def register_paid_tax(self, anio: int, paid_amount: float) -> int:
        """Actualiza el monto pagado para un año dado."""
        query = """
        UPDATE impuesto_anual
        SET impuesto_pagado = %s
        WHERE anio = %s
        """
        return self._execute_write(query, (paid_amount, anio))

    def register_deductions(self, anio: int, deducibles: float) -> int:
        """Registra el total de gastos deducibles declarados."""
        query = """
        UPDATE impuesto_anual
        SET gastos_deducibles = %s
        WHERE anio = %s
        """
        return self._execute_write(query, (deducibles, anio))

    def fetch_summary_by_year(self, anio: int) -> Optional[Dict[str, Any]]:
        """Obtiene los valores calculados y pagados de un año específico."""
        query = """
        SELECT
            anio,
            ingreso_total,
            gastos_deducibles,
            base_imponible,
            impuesto_calculado,
            impuesto_pagado,
            diferencia
        FROM impuesto_anual
        WHERE anio = %s
        """
        rows = self._execute_read(query, (anio,))
        return rows[0] if rows else None

    def compare_calculated_vs_paid(self, anio: int) -> Optional[Dict[str, float]]:
        """Devuelve la diferencia entre impuesto estimado y pagado por año."""
        summary = self.fetch_summary_by_year(anio)
        if not summary:
            return None
        return {
            "anio": summary["anio"],
            "calculado": summary.get("impuesto_calculado", 0.0) or 0.0,
            "pagado": summary.get("impuesto_pagado", 0.0) or 0.0,
            "diferencia": (summary.get("impuesto_calculado", 0.0) or 0.0)
            - (summary.get("impuesto_pagado", 0.0) or 0.0),
        }


class FinancialReportRepository(BaseRepository):
    """Consultas compuestas para ahorros, presupuestos, gastos, ingresos e impuestos."""
    def _apply_year_filter(self, base: str, year: Optional[int], suffix: str = "") -> str:
        if year is None:
            return base
        return f"{base} WHERE YEAR(t.fecha) = %s{suffix}" if suffix else f"{base} WHERE YEAR(t.fecha) = %s"

    def monthly_savings(self, year: Optional[int] = None) -> List[Dict[str, Any]]:
        """Calcula ahorro neto mensual (ingresos - gastos)."""
        where = ""
        params: Sequence[Any] = ()
        if year is not None:
            where = "WHERE YEAR(t.fecha) = %s"
            params = (year,)
        query = f"""
        SELECT
            DATE_FORMAT(t.fecha, '%Y-%m') AS periodo,
            SUM(t.monto * CASE WHEN c.tipo = 'ingreso' THEN 1 ELSE -1 END) AS ahorro
        FROM transaccion t
        JOIN categoria c ON t.Categoria_Id_Categoria = c.Id_Categoria
        {where}
        GROUP BY periodo
        ORDER BY periodo
        """
        return self._execute_read(query, params)

    def annual_savings(self) -> List[Dict[str, Any]]:
        """Agrupa el ahorro anual por año."""
        query = """
        SELECT
            YEAR(t.fecha) AS anio,
            SUM(t.monto * CASE WHEN c.tipo = 'ingreso' THEN 1 ELSE -1 END) AS ahorro
        FROM transaccion t
        JOIN categoria c ON t.Categoria_Id_Categoria = c.Id_Categoria
        GROUP BY anio
        ORDER BY anio
        """
        return self._execute_read(query)

    def get_monthly_global_budget(self, year: Optional[int] = None) -> List[Dict[str, Any]]:
        """Suma mensual del presupuesto general."""
        params: Sequence[Any] = ()
        filter_clause = ""
        if year is not None:
            filter_clause = "WHERE anio = %s"
            params = (year,)
        query = f"""
        SELECT anio, mes, SUM(monto_total) AS monto_total
        FROM presupuesto_general
        {filter_clause}
        GROUP BY anio, mes
        ORDER BY anio, mes
        """
        return self._execute_read(query, params)

    def get_annual_global_budget(self) -> List[Dict[str, Any]]:
        """Presupuesto agregado por año."""
        query = """
        SELECT anio, SUM(monto_total) AS monto_total
        FROM presupuesto_general
        GROUP BY anio
        ORDER BY anio
        """
        return self._execute_read(query)

    def get_budget_by_category(self, year: Optional[int] = None) -> List[Dict[str, Any]]:
        """Presupuestos específicos con nombre de categoría."""
        params: Sequence[Any] = ()
        filter_clause = ""
        if year is not None:
            filter_clause = "WHERE p.anio = %s"
            params = (year,)
        query = f"""
        SELECT
            p.anio,
            p.mes,
            c.Id_Categoria AS categoria_id,
            c.nombre,
            p.monto
        FROM presupuesto_especifico p
        JOIN categoria c ON p.Categoria_Id_Categoria = c.Id_Categoria
        {filter_clause}
        ORDER BY p.anio, p.mes, c.nombre
        """
        return self._execute_read(query, params)

    def _expense_query(
        self,
        periodicidad: str,
        year: Optional[int],
        month: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        filters = ["c.tipo = 'gasto'", "c.periodicidad = %s"]
        params: list[Any] = [periodicidad]
        if year is not None:
            filters.append("YEAR(t.fecha) = %s")
            params.append(year)
        if month is not None:
            filters.append("MONTH(t.fecha) = %s")
            params.append(month)
        query = f"""
        SELECT
            c.Id_Categoria AS categoria_id,
            c.nombre,
            SUM(t.monto) AS total
        FROM transaccion t
        JOIN categoria c ON t.Categoria_Id_Categoria = c.Id_Categoria
        WHERE {' AND '.join(filters)}
        GROUP BY c.Id_Categoria, c.nombre
        ORDER BY total DESC
        """
        return self._execute_read(query, tuple(params))

    def monthly_fixed_expenses(self, year: Optional[int] = None, month: Optional[int] = None) -> List[Dict[str, Any]]:
        """Gastos categorizados como fijos mensuales."""
        return self._expense_query("mensual", year, month)

    def variable_expenses(self, year: Optional[int] = None, month: Optional[int] = None) -> List[Dict[str, Any]]:
        """Gastos clasificados como variables."""
        return self._expense_query("variable", year, month)

    def annual_expenses(self, year: Optional[int] = None) -> List[Dict[str, Any]]:
        """Gastos con periodicidad anual."""
        return self._expense_query("anual", year)

    def incomes_by_category(self, year: Optional[int] = None) -> List[Dict[str, Any]]:
        """Ingresos totales por categoría."""
        params: Sequence[Any] = ()
        clause = ""
        if year is not None:
            clause = "AND YEAR(t.fecha) = %s"
            params = (year,)
        query = f"""
        SELECT
            c.Id_Categoria AS categoria_id,
            c.nombre,
            SUM(t.monto) AS total
        FROM transaccion t
        JOIN categoria c ON t.Categoria_Id_Categoria = c.Id_Categoria
        WHERE c.tipo = 'ingreso'
        {clause}
        GROUP BY c.Id_Categoria, c.nombre
        ORDER BY total DESC
        """
        if year is not None:
            params = (year,)
        return self._execute_read(query, params)

    def monthly_incomes(self, year: Optional[int] = None) -> List[Dict[str, Any]]:
        """Agrupa ingresos mensuales."""
        params: Sequence[Any] = ()
        clause = ""
        if year is not None:
            clause = "AND YEAR(t.fecha) = %s"
            params = (year,)
        query = f"""
        SELECT
            DATE_FORMAT(t.fecha, '%Y-%m') AS periodo,
            SUM(t.monto) AS total
        FROM transaccion t
        JOIN categoria c ON t.Categoria_Id_Categoria = c.Id_Categoria
        WHERE c.tipo = 'ingreso'
        {clause}
        GROUP BY periodo
        ORDER BY periodo
        """
        return self._execute_read(query, params)

    def annual_incomes(self) -> List[Dict[str, Any]]:
        """Agrupa ingresos por año."""
        query = """
        SELECT
            YEAR(t.fecha) AS anio,
            SUM(t.monto) AS total
        FROM transaccion t
        JOIN categoria c ON t.Categoria_Id_Categoria = c.Id_Categoria
        WHERE c.tipo = 'ingreso'
        GROUP BY anio
        ORDER BY anio
        """
        return self._execute_read(query)

    def annual_report(self, anio: int) -> Dict[str, Any]:
        """Compone un reporte anual integrando todas las métricas."""
        return {
            "savings": self.monthly_savings(year=anio),
            "budgets": {
                "monthly": self.get_monthly_global_budget(year=anio),
                "category": self.get_budget_by_category(year=anio),
            },
            "expenses": {
                "fijos": self.monthly_fixed_expenses(year=anio),
                "variables": self.variable_expenses(year=anio),
                "anuales": self.annual_expenses(year=anio),
            },
            "incomes": {
                "monthly": self.monthly_incomes(year=anio),
                "category": self.incomes_by_category(year=anio),
                "annual": self.annual_incomes(),
            },
        }

    def get_available_years(self) -> list[int]:
        query = """
        SELECT DISTINCT YEAR(fecha) AS anio
        FROM transaccion
        ORDER BY anio
        """
        rows = self._execute_read(query)
        return [int(row["anio"]) for row in rows if row.get("anio")]

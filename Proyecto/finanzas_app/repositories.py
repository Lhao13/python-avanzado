from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence

from .db.connection import DatabaseConnection
from .models import (
    Categoria,
    ImpuestoAnual,
    PresupuestoEspecifico,
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

    def list_by_categoria(self, categoria_id: int, year: Optional[int] = None) -> List[Transaccion]:
        """Lista las transacciones relacionadas con una categoría, opcionalmente filtradas por año."""
        params: list[Any] = [categoria_id]
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
        """
        if year is not None:
            query += " AND YEAR(fecha) = %s"
            params.append(year)
        query += " ORDER BY fecha DESC"
        rows = self._execute_read(query, tuple(params))
        return [Transaccion(**row) for row in rows]

    def list_all_with_category(self) -> List[Dict[str, Any]]:
        """Lista todas las transacciones con el nombre de categoría asociado."""
        query = """
        SELECT
            t.Id_Transaccion AS id_transaccion,
            t.monto,
            t.cantidad,
            t.fecha,
            t.description,
            c.Id_Categoria AS categoria_id,
            c.nombre AS categoria
        FROM transaccion t
        JOIN categoria c ON t.Categoria_Id_Categoria = c.Id_Categoria
        ORDER BY t.fecha DESC
        """
        return self._execute_read(query)

    def list_variable_transactions(self, year: int) -> List[Transaccion]:
        """Transacciones variables realizadas durante el año requerido."""
        params: list[Any] = [year]
        query = """
        SELECT
            Id_Transaccion AS id_transaccion,
            monto,
            cantidad,
            fecha,
            Categoria_Id_Categoria AS categoria_id,
            description
        FROM transaccion t
        JOIN categoria c ON t.Categoria_Id_Categoria = c.Id_Categoria
        WHERE c.tipo = 'gasto'
          AND c.periodicidad = 'variable'
          AND YEAR(t.fecha) = %s
        ORDER BY fecha DESC
        """
        rows = self._execute_read(query, tuple(params))
        return [Transaccion(**row) for row in rows]

    def update(self, transaccion: Transaccion) -> int:
        """Actualiza campos editables de una transacción existente."""
        query = """
        UPDATE transaccion
        SET monto = %s,
            cantidad = %s,
            fecha = %s,
            description = %s
        WHERE Id_Transaccion = %s
        """
        params = (
            transaccion.monto,
            transaccion.cantidad,
            transaccion.fecha,
            transaccion.description,
            transaccion.id_transaccion,
        )
        return self._execute_write(query, params)

    def delete(self, transaccion_id: int) -> int:
        """Elimina una transacción por su identificador."""
        query = """
        DELETE FROM transaccion
        WHERE Id_Transaccion = %s
        """
        return self._execute_write(query, (transaccion_id,))


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

    def list_by_month(self, year: int, month: int) -> List[Dict[str, Any]]:
        query = """
        SELECT
            p.Id_Presupuesto AS id_presupuesto,
            p.anio,
            p.mes,
            p.monto,
            c.Id_Categoria AS categoria_id,
            c.nombre
        FROM presupuesto_especifico p
        JOIN categoria c ON p.Categoria_Id_Categoria = c.Id_Categoria
        WHERE p.anio = %s AND p.mes = %s
        ORDER BY c.nombre
        """
        return self._execute_read(query, (year, month))

    def delete(self, presupuesto_id: int) -> int:
        query = """
        DELETE FROM presupuesto_especifico
        WHERE Id_Presupuesto = %s
        """
        return self._execute_write(query, (presupuesto_id,))

    def list_by_month(self, year: int, month: int) -> List[Dict[str, Any]]:
        query = """
        SELECT
            p.Id_Presupuesto AS id_presupuesto,
            p.anio,
            p.mes,
            p.monto,
            c.Id_Categoria AS categoria_id,
            c.nombre
        FROM presupuesto_especifico p
        JOIN categoria c ON p.Categoria_Id_Categoria = c.Id_Categoria
        WHERE p.anio = %s AND p.mes = %s
        ORDER BY c.nombre
        """
        return self._execute_read(query, (year, month))

    def delete(self, presupuesto_id: int) -> int:
        query = """
        DELETE FROM presupuesto_especifico
        WHERE Id_Presupuesto = %s
        """
        return self._execute_write(query, (presupuesto_id,))



class ImpuestoAnualRepository(BaseRepository):
    """Operaciones mínimas sobre el impuesto anual histórico."""

    def save_paid_tax(self, anio: int, impuesto_pagado: float) -> int:
        """Inserta o actualiza el registro del impuesto pagado por año."""
        query = """
        INSERT INTO impuesto_anual (anio, impuesto_pagado)
        VALUES (%s, %s)
        ON DUPLICATE KEY UPDATE impuesto_pagado = VALUES(impuesto_pagado)
        """
        return self._execute_write(query, (anio, impuesto_pagado))

    def list_tax_payments(self) -> List[Dict[str, Any]]:
        """Recupera los pagos de impuesto almacenados ordenados por año."""
        query = """
        SELECT anio, impuesto_pagado
        FROM impuesto_anual
        ORDER BY anio
        """
        return self._execute_read(query)


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

    def budget_by_category_for_month(self, year: int, month: int) -> List[Dict[str, Any]]:
        """Detalle de presupuestos específicos para el mes y año dados."""
        query = """
        SELECT
            c.Id_Categoria AS categoria_id,
            c.nombre,
            p.monto
        FROM presupuesto_especifico p
        JOIN categoria c ON p.Categoria_Id_Categoria = c.Id_Categoria
        WHERE p.anio = %s
          AND p.mes = %s
        ORDER BY c.nombre
        """
        params: Sequence[Any] = (year, month)
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

    def _sum_amount_by_type(self, year: int, tipo: str, month: Optional[int] = None) -> float:
        """Suma total para un tipo de transacción en el período indicado."""
        filters = ["c.tipo = %s", "YEAR(t.fecha) = %s"]
        params: list[Any] = [tipo, year]
        if month is not None:
            filters.append("MONTH(t.fecha) = %s")
            params.append(month)
        query = f"""
        SELECT SUM(t.monto) AS total
        FROM transaccion t
        JOIN categoria c ON t.Categoria_Id_Categoria = c.Id_Categoria
        WHERE {' AND '.join(filters)}
        """
        rows = self._execute_read(query, tuple(params))
        if not rows:
            return 0.0
        return float(rows[0].get("total") or 0.0)

    def total_expenses(self, year: int, month: Optional[int] = None) -> float:
        """Totaliza los gastos del período."""
        return self._sum_amount_by_type(year, "gasto", month)

    def total_incomes(self, year: int, month: Optional[int] = None) -> float:
        """Totaliza los ingresos del período."""
        return self._sum_amount_by_type(year, "ingreso", month)

    def expenses_by_category(self, year: int, month: Optional[int] = None) -> List[Dict[str, Any]]:
        """Lista de gastos agrupados por categoría para el año (y mes opcional)."""
        filters = ["c.tipo = 'gasto'", "YEAR(t.fecha) = %s"]
        params: list[Any] = [year]
        if month is not None:
            filters.append("MONTH(t.fecha) = %s")
            params.append(month)
        query = f"""
        SELECT
            c.nombre AS categoria,
            SUM(t.monto) AS total
        FROM transaccion t
        JOIN categoria c ON t.Categoria_Id_Categoria = c.Id_Categoria
        WHERE {' AND '.join(filters)}
        GROUP BY c.Id_Categoria, c.nombre
        ORDER BY total DESC
        """
        return self._execute_read(query, tuple(params))

    def incomes_by_category_for_month(self, year: int, month: int) -> List[Dict[str, Any]]:
        """Ingresa los totales por categoría dentro del mes indicado."""
        query = """
        SELECT
            c.nombre AS categoria,
            SUM(t.monto) AS total
        FROM transaccion t
        JOIN categoria c ON t.Categoria_Id_Categoria = c.Id_Categoria
        WHERE c.tipo = 'ingreso'
          AND YEAR(t.fecha) = %s
          AND MONTH(t.fecha) = %s
        GROUP BY c.Id_Categoria, c.nombre
        ORDER BY total DESC
        """
        return self._execute_read(query, (year, month))

    def expenses_by_category_by_month(self, year: int) -> List[Dict[str, Any]]:
        """Agrupa los gastos por mes y categoría para montar gráficos apilados."""
        query = """
        SELECT
            MONTH(t.fecha) AS mes,
            c.nombre AS categoria,
            SUM(t.monto) AS total
        FROM transaccion t
        JOIN categoria c ON t.Categoria_Id_Categoria = c.Id_Categoria
        WHERE c.tipo = 'gasto'
          AND YEAR(t.fecha) = %s
        GROUP BY mes, c.Id_Categoria, c.nombre
        ORDER BY mes, total DESC
        """
        return self._execute_read(query, (year,))

    def daily_totals_by_type(self, year: int, month: int, tipo: str) -> List[Dict[str, Any]]:
        """Totales diarios para un tipo de transacción dentro de un mes."""
        query = """
        SELECT
            DATE(t.fecha) AS fecha,
            SUM(t.monto) AS total
        FROM transaccion t
        JOIN categoria c ON t.Categoria_Id_Categoria = c.Id_Categoria
        WHERE YEAR(t.fecha) = %s
          AND MONTH(t.fecha) = %s
          AND c.tipo = %s
        GROUP BY DATE(t.fecha)
        ORDER BY DATE(t.fecha)
        """
        return self._execute_read(query, (year, month, tipo))

    def weekly_expense_heatmap(self, year: int, month: int) -> List[Dict[str, Any]]:
        """Datos para representar el gasto por semana y día de la semana."""
        query = """
        SELECT
            WEEK(t.fecha, 1) AS semana,
            DAYOFWEEK(t.fecha) AS dia_semana,
            SUM(t.monto) AS total
        FROM transaccion t
        JOIN categoria c ON t.Categoria_Id_Categoria = c.Id_Categoria
        WHERE YEAR(t.fecha) = %s
          AND MONTH(t.fecha) = %s
          AND c.tipo = 'gasto'
        GROUP BY semana, dia_semana
        ORDER BY semana, dia_semana
        """
        return self._execute_read(query, (year, month))

    def monthly_expense_totals(self, year: int) -> List[Dict[str, Any]]:
        """Totales de gastos por cada mes del año para el gráfico anual."""
        query = """
        SELECT
            MONTH(t.fecha) AS mes,
            SUM(t.monto) AS total
        FROM transaccion t
        JOIN categoria c ON t.Categoria_Id_Categoria = c.Id_Categoria
        WHERE c.tipo = 'gasto'
          AND YEAR(t.fecha) = %s
        GROUP BY mes
        ORDER BY mes
        """
        return self._execute_read(query, (year,))

    def fixed_expenses_by_year(self, year: int) -> List[Dict[str, Any]]:
        """Totales por categoría para los gastos fijos dentro del año."""
        return self._expense_query("mensual", year)

    def fixed_monthly_expenses_by_category(self, year: int) -> List[Dict[str, Any]]:
        """Totales mensuales por categoría de los gastos fijos del año."""
        query = """
        SELECT
            MONTH(t.fecha) AS mes,
            c.nombre,
            SUM(t.monto) AS total
        FROM transaccion t
        JOIN categoria c ON t.Categoria_Id_Categoria = c.Id_Categoria
        WHERE c.tipo = 'gasto'
          AND c.periodicidad = 'mensual'
          AND YEAR(t.fecha) = %s
        GROUP BY mes, c.nombre
        ORDER BY mes, c.nombre
        """
        return self._execute_read(query, (year,))
    def variable_monthly_totals(self, year: int) -> List[Dict[str, Any]]:
        """Suma mensual de gastos variables para el año indicado."""
        query = """
        SELECT
            MONTH(t.fecha) AS mes,
            SUM(t.monto) AS total
        FROM transaccion t
        JOIN categoria c ON t.Categoria_Id_Categoria = c.Id_Categoria
        WHERE c.tipo = 'gasto'
          AND c.periodicidad = 'variable'
          AND YEAR(t.fecha) = %s
        GROUP BY MONTH(t.fecha)
        ORDER BY mes
        """
        return self._execute_read(query, (year,))
        
    def variable_monthly_totals_by_category(self, year: int, category_id: int) -> List[Dict[str, Any]]:
        """Suma mensual de gastos variables para una categoría específica."""
        query = """
        SELECT
            MONTH(t.fecha) AS mes,
            SUM(t.monto) AS total
        FROM transaccion t
        JOIN categoria c ON t.Categoria_Id_Categoria = c.Id_Categoria
        WHERE c.tipo = 'gasto'
          AND c.periodicidad = 'variable'
          AND c.Id_Categoria = %s
          AND YEAR(t.fecha) = %s
        GROUP BY MONTH(t.fecha)
        ORDER BY mes
        """
        return self._execute_read(query, (category_id, year))

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

    def monthly_incomes_by_category(self, year: Optional[int] = None) -> List[Dict[str, Any]]:
        """Totaliza ingresos mensuales por categoría."""
        params: Sequence[Any] = ()
        clause = ""
        if year is not None:
            clause = "AND YEAR(t.fecha) = %s"
            params = (year,)
        query = f"""
        SELECT
            DATE_FORMAT(t.fecha, '%Y-%m') AS periodo,
            c.nombre,
            SUM(t.monto) AS total
        FROM transaccion t
        JOIN categoria c ON t.Categoria_Id_Categoria = c.Id_Categoria
        WHERE c.tipo = 'ingreso'
        {clause}
        GROUP BY periodo, c.nombre
        ORDER BY periodo, c.nombre
        """
        return self._execute_read(query, params)

    def annual_report(self, anio: int) -> Dict[str, Any]:
        """Compone un reporte anual integrando todas las métricas."""
        return {
            "savings": self.monthly_savings(year=anio),
            "budgets": {
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

    def _transaction_detail_query(self, filters: list[str], params: list[Any]) -> List[Dict[str, Any]]:
        """Base para consultas detalladas de transacciones con categoría."""
        query = f"""
        SELECT
            t.Id_Transaccion AS id_transaccion,
            t.monto,
            t.cantidad,
            t.fecha,
            t.description,
            c.Id_Categoria AS categoria_id,
            c.nombre AS categoria,
            c.tipo AS categoria_tipo
        FROM transaccion t
        JOIN categoria c ON t.Categoria_Id_Categoria = c.Id_Categoria
        WHERE {' AND '.join(filters)}
        ORDER BY t.fecha DESC
        """
        return self._execute_read(query, tuple(params))

    def transactions_for_year(self, year: int) -> List[Dict[str, Any]]:
        """Trae todas las transacciones realizadas durante el año seleccionado."""
        filters = ["YEAR(t.fecha) = %s"]
        params: list[Any] = [year]
        return self._transaction_detail_query(filters, params)

    def transactions_for_month(self, year: int, month: int) -> List[Dict[str, Any]]:
        """Trae las transacciones del mes y año seleccionados."""
        filters = ["YEAR(t.fecha) = %s", "MONTH(t.fecha) = %s"]
        params = [year, month]
        return self._transaction_detail_query(filters, params)

    def get_available_years(self) -> list[int]:
        query = """
        SELECT DISTINCT YEAR(fecha) AS anio
        FROM transaccion
        ORDER BY anio
        """
        rows = self._execute_read(query)
        return [int(row["anio"]) for row in rows if row.get("anio")]

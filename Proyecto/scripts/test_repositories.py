from __future__ import annotations

import os
import sys
import uuid
from contextlib import suppress
from datetime import date
from pathlib import Path
from typing import Iterable, Optional

sys.path.append(str(Path(__file__).resolve().parents[1]))
from finanzas_app import (
    Categoria,
    ImpuestoAnual,
    PresupuestoEspecifico,
    PresupuestoGeneral,
    Transaccion,
    CategoriaRepository,
    FinancialReportRepository,
    ImpuestoAnualRepository,
    PresupuestoEspecificoRepository,
    PresupuestoGeneralRepository,
    TransaccionRepository,
    DatabaseConnection,
)


def ensure_config_env() -> None:
    if os.getenv("DB_CONFIG_FILE"):
        return
    config_path = Path(__file__).resolve().parents[0].parent / "db_config.json"
    if not config_path.exists():
        raise FileNotFoundError("db_config.json no encontrado")
    os.environ["DB_CONFIG_FILE"] = str(config_path)


def execute_raw(connection: DatabaseConnection, query: str, params: Iterable = ()) -> None:
    with connection.get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, tuple(params))
            conn.commit()


def main() -> None:
    ensure_config_env()
    connection = DatabaseConnection()
    print("Conectado a MySQL", connection.test_connection())

    categoria_repo = CategoriaRepository(connection)
    trans_repo = TransaccionRepository(connection)
    presupuesto_especifico_repo = PresupuestoEspecificoRepository(connection)
    presupuesto_general_repo = PresupuestoGeneralRepository(connection)
    impuesto_repo = ImpuestoAnualRepository(connection)
    report_repo = FinancialReportRepository(connection)

    income_cat = Categoria(
        nombre=f"TestIngreso-{uuid.uuid4().hex[:6]}",
        periodicidad="mensual",
        tipo="ingreso",
        descripcion="Categoria de prueba ingreso",
    )
    fixed_cat = Categoria(
        nombre=f"TestFijo-{uuid.uuid4().hex[:6]}",
        periodicidad="mensual",
        tipo="gasto",
        descripcion="Categoria de prueba gasto fijo",
    )
    variable_cat = Categoria(
        nombre=f"TestVariable-{uuid.uuid4().hex[:6]}",
        periodicidad="variable",
        tipo="gasto",
        descripcion="Categoria de prueba gasto variable",
    )
    anual_cat = Categoria(
        nombre=f"TestAnual-{uuid.uuid4().hex[:6]}",
        periodicidad="anual",
        tipo="gasto",
        descripcion="Categoria gasto anual",
    )
    categorias = [income_cat, fixed_cat, variable_cat, anual_cat]

    transacciones: list[Transaccion] = []
    presupuesto_general_id: Optional[int] = None
    impuesto_id: Optional[int] = None
    try:
        for categoria in categorias:
            categoria_repo.create(categoria)
        print("Categorias creadas:", [cat.id_categoria for cat in categorias])

        transacciones = [
            Transaccion(
                monto=1500.0,
                cantidad=1,
                fecha=date(2025, 1, 15),
                categoria_id=income_cat.id_categoria,
                description="Ingreso salarial prueba",
            ),
            Transaccion(
                monto=400.0,
                cantidad=1,
                fecha=date(2025, 1, 25),
                categoria_id=fixed_cat.id_categoria,
                description="Gasto fijo prueba",
            ),
            Transaccion(
                monto=220.0,
                cantidad=1,
                fecha=date(2025, 6, 12),
                categoria_id=variable_cat.id_categoria,
                description="Gasto variable prueba",
            ),
            Transaccion(
                monto=1200.0,
                cantidad=1,
                fecha=date(2025, 3, 8),
                categoria_id=anual_cat.id_categoria,
                description="Gasto anual prueba",
            ),
        ]
        for transaccion in transacciones:
            trans_repo.create(transaccion)
        print("Transacciones insertadas:", [t.id_transaccion for t in transacciones])

        presupuesto_general = PresupuestoGeneral(
            periodo="mensual",
            anio=2019,
            mes=11,
            monto_total=5000.0,
        )
        presupuesto_general_id = presupuesto_general_repo.create(presupuesto_general)
        print("Presupuesto general creado")

        for cat in (fixed_cat, variable_cat):
            presupuesto_especifico = PresupuestoEspecifico(
                anio=2025,
                mes=11,
                monto=1000.0 if cat is fixed_cat else 400.0,
                categoria_id=cat.id_categoria,
            )
            presupuesto_especifico_repo.create(presupuesto_especifico)
        print("Presupuestos especificos insertados")

        impuesto = ImpuestoAnual(
            anio=2025,
            ingreso_total=20000.0,
            gastos_deducibles=3500.0,
            base_imponible=16500.0,
            impuesto_calculado=1900.0,
            impuesto_pagado=1500.0,
            diferencia=400.0,
        )
        impuesto_id = impuesto_repo.create(impuesto)
        print("Impuesto anual creado")

        print("Ahorro mensual:", report_repo.monthly_savings(year=2025))
        print("Ahorro anual:", report_repo.annual_savings())
        print("Presupuesto mensual global:", report_repo.get_monthly_global_budget(year=2025))
        print("Presupuesto anual global:", report_repo.get_annual_global_budget())
        print("Presupuesto por categoria:", report_repo.get_budget_by_category(year=2025))
        print("Gastos fijos mensuales:", report_repo.monthly_fixed_expenses(year=2025))
        print("Gastos variables:", report_repo.variable_expenses(year=2025))
        print("Gastos anuales:", report_repo.annual_expenses(year=2025))
        print("Ingresos por categoria:", report_repo.incomes_by_category(year=2025))
        print("Ingresos mensuales:", report_repo.monthly_incomes(year=2025))
        print("Ingresos anuales:", report_repo.annual_incomes())
        print("Reporte anual:", report_repo.annual_report(2025))
        print("Diferencia impuesto calculado vs pagado:", impuesto_repo.compare_calculated_vs_paid(2025))
    finally:
        print("Limpiando registros de prueba")
        with suppress(Exception):
            for transaccion in transacciones:
                execute_raw(connection, "DELETE FROM transaccion WHERE Id_Transaccion = %s", (transaccion.id_transaccion,))
            execute_raw(
                connection,
                "DELETE FROM presupuesto_especifico WHERE Categoria_Id_Categoria IN (%s, %s)",
                (fixed_cat.id_categoria, variable_cat.id_categoria),
            )
            if presupuesto_general_id:
                execute_raw(
                    connection,
                    "DELETE FROM presupuesto_general WHERE Id_Presupueto_General = %s",
                    (presupuesto_general_id,),
                )
            if impuesto_id:
                execute_raw(
                    connection,
                    "DELETE FROM impuesto_anual WHERE Id_mpuesto_anual = %s",
                    (impuesto_id,),
                )
            for cat in categorias:
                if cat.id_categoria:
                    execute_raw(connection, "DELETE FROM categoria WHERE Id_Categoria = %s", (cat.id_categoria,))
        print("Registros de prueba eliminados")


if __name__ == "__main__":
    main()

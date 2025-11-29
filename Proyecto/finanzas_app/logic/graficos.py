"""Herramientas ligeras para representar gráficas simples con Tkinter."""

from __future__ import annotations

from calendar import month_name
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import pandas as pd
import tkinter as tk
from matplotlib.figure import Figure
from matplotlib import pyplot as plt
from plotnine import *

from ..db.connection import DatabaseConnection
from ..repositories import FinancialReportRepository, ImpuestoAnualRepository


def _value_for_type(year: int, month: int, tipo: str) -> float:
    """Consulta la suma de montos de una categoría de tipo `tipo` en el mes solicitado."""
    query = """
    SELECT SUM(t.monto)
    FROM transaccion t
    JOIN categoria c ON t.Categoria_Id_Categoria = c.Id_Categoria
    WHERE YEAR(t.fecha) = %s
      AND MONTH(t.fecha) = %s
      AND c.tipo = %s
    """
    with DatabaseConnection().get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, (year, month, tipo))
            row = cursor.fetchone()
            if not row or row[0] is None:
                return 0.0
            return float(row[0])


def _get_period(year: Optional[int] = None, month: Optional[int] = None) -> Tuple[int, int]:
    """Devuelve (año, mes) usando la fecha actual cuando no se especifica un valor."""
    now = datetime.now()
    return (year or now.year, month or now.month)


def monthly_comparison_data(year: Optional[int] = None, month: Optional[int] = None) -> Tuple[str, Tuple[Tuple[str, float], Tuple[str, float]]]:
    """Entrega la etiqueta legible con los montos de ingresos y gastos del periodo."""
    period_year, period_month = _get_period(year, month)
    label = f"{month_name[period_month]} {period_year}"
    ingresos = _value_for_type(period_year, period_month, "ingreso")
    gastos = _value_for_type(period_year, period_month, "gasto")
    return label, (("Ingresos", ingresos), ("Gastos", gastos))


def render_monthly_comparison(canvas: tk.Canvas, year: Optional[int] = None, month: Optional[int] = None) -> None:
    """Dibuja un gráfico con barras proporcionales a los valores retornados por `monthly_comparison_data`."""
    label, data = monthly_comparison_data(year, month)
    canvas.delete("all")
    width = int(canvas.cget("width") or canvas.winfo_reqwidth() or 400)
    height = int(canvas.cget("height") or canvas.winfo_reqheight() or 240)
    padding = 16
    chart_height = height - padding * 4
    chart_width = width - padding * 2
    max_value = max(value for _, value in data) or 1.0
    bar_width = chart_width / (len(data) * 2)

    # Título y etiqueta del período en la parte superior del lienzo.
    canvas.create_text(width / 2, padding / 1.5, text="Comparativa del mes", font=(None, 11, "bold"))
    canvas.create_text(width / 2, padding * 1.8, text=label, font=(None, 9))

    baseline = padding * 3 + chart_height
    canvas.create_line(padding, baseline, width - padding, baseline, fill="#666")

    colors = ["#4caf50", "#e53935"]
    for idx, (name, value) in enumerate(data):
        normalized = value / max_value
        bar_height = normalized * chart_height
        x0 = padding + idx * bar_width * 2 + bar_width / 2
        x1 = x0 + bar_width
        y0 = baseline - bar_height
        canvas.create_rectangle(x0, y0, x1, baseline, fill=colors[idx % len(colors)], outline="")
        canvas.create_text((x0 + x1) / 2, y0 - 12, text=f"${value:,.2f}", font=(None, 9), fill="#222")
        canvas.create_text((x0 + x1) / 2, baseline + 12, text=name, font=(None, 10, "bold"))

    for i in range(5):
        value = max_value * (i / 4)
        y = baseline - (value / max_value) * chart_height
        canvas.create_line(padding - 6, y, padding, y, fill="#bbb")
        canvas.create_text(padding - 8, y, text=f"${value:,.0f}", anchor="e", font=(None, 8))


def monthly_budget_pie_data(year: Optional[int] = None, month: Optional[int] = None) -> Tuple[str, List[Tuple[str, float]]]:
    """Recupera los montos del presupuesto específico y etiqueta para el gráfico de pastel."""
    period_year, period_month = _get_period(year, month)
    label = f"Presupuesto {month_name[period_month]} {period_year}"
    repo = FinancialReportRepository(DatabaseConnection())
    rows = repo.budget_by_category_for_month(period_year, period_month)
    data: List[Tuple[str, float]] = []
    for row in rows:
        monto = float(row.get("monto") or 0.0)
        if monto <= 0:
            continue
        nombre = row.get("nombre") or "Sin categoría"
        data.append((nombre, monto))
    return label, data


def budget_pie_figure(year: int, month: int) -> Figure:
    """Devuelve un pastel de los presupuestos del periodo usando Matplotlib."""
    label, slices = monthly_budget_pie_data(year, month)
    fig = Figure(figsize=(6, 4))
    ax = fig.subplots()
    if not slices:
        ax.text(0.5, 0.5, "Sin presupuesto específico", ha="center", va="center", fontsize=11, color="#888")
        ax.set_axis_off()
        return fig

    totals = [value for _, value in slices]
    labels = [name for name, _ in slices]
    cmap = plt.get_cmap("Set3")
    colors = [cmap(i / max(len(labels) - 1, 1)) for i in range(len(labels))]
    # Dibujamos el pastel con porcentajes y leyenda lateral para la categoría.
    wedges, _, _ = ax.pie(
        totals,
        labels=None,
        autopct="%.1f%%",
        startangle=90,
        colors=colors,
        wedgeprops={"edgecolor": "white"},
    )
    ax.set_title(label)
    ax.axis("equal")
    ax.legend(
        wedges,
        labels,
        title="Categoría",
        loc="center left",
        bbox_to_anchor=(1, 0.5),
        frameon=False,
    )
    return fig


def _objective_total_for_month(year: int, month: int) -> float:
    repo = FinancialReportRepository(DatabaseConnection())
    rows = repo.budget_by_category_for_month(year, month)
    return sum(float(row.get("monto") or 0.0) for row in rows)


def monthly_objective_comparison_data(
    year: Optional[int] = None, month: Optional[int] = None
) -> Tuple[str, Tuple[Tuple[str, float], Tuple[str, float]], float]:
    period_year, period_month = _get_period(year, month)
    label = f"{month_name[period_month]} {period_year}"
    ingresos = _value_for_type(period_year, period_month, "ingreso")
    objetivo = _objective_total_for_month(period_year, period_month)
    difference = ingresos - objetivo
    return label, (("Ingresos", ingresos), ("Objetivo gastos", objetivo)), difference


def objective_comparison_figure(year: int, month: int) -> Figure:
    label, data, difference = monthly_objective_comparison_data(year, month)
    records = [{"tipo": name, "total": value} for name, value in data]
    df = pd.DataFrame(records)
    fig = Figure(figsize=(6, 4))
    if df.empty:
        ax = fig.subplots()
        ax.text(0.5, 0.5, "Sin datos", ha="center", va="center", fontsize=11, color="#666")
        ax.set_axis_off()
        return fig

    # Usamos plotnine para mantener la línea visual con los demás gráficos.
    plot = (
        ggplot(df, aes(x="tipo", y="total", fill="tipo"))
        + geom_col(width=0.6)
        + labs(title=label, x="Tipo", y="Monto ($)")
        + scale_fill_brewer(type="qual", palette="Set2")
        + theme_minimal()
        + theme(
            axis_text_x=element_text(rotation=0, hjust=0.5),
            figure_size=(6, 4),
            legend_position="none",
        )
    )
    figure = plot.draw()
    ax = figure.axes[0]
    ax.text(0.02, 0.95, f"Ahorro mensual: ${difference:,.2f}", transform=ax.transAxes, va="top", fontsize=9, color="#555")
    return figure


def fixed_monthly_stacked_data(year: int) -> Tuple[List[str], List[str], Dict[str, List[float]]]:
    repo = FinancialReportRepository(DatabaseConnection())
    rows = repo.fixed_monthly_expenses_by_category(year)
    months = [month_name[i] for i in range(1, 13)]
    categories = sorted({(row.get("nombre") or "Sin categoría") for row in rows})
    data: Dict[str, List[float]] = {category: [0.0] * len(months) for category in categories}
    for row in rows:
        mes = int(row.get("mes") or 0)
        if not 1 <= mes <= len(months):
            continue
        nombre = row.get("nombre") or "Sin categoría"
        monto = float(row.get("total") or 0.0)
        if nombre not in data:
            data[nombre] = [0.0] * len(months)
            categories.append(nombre)
        data[nombre][mes - 1] = monto
    return months, categories, data


def fixed_category_stacked_figure(year: int) -> Figure:
    months, categories, series = fixed_monthly_stacked_data(year)
    records: list[dict[str, float | str]] = []
    for category in categories:
        values = series.get(category, [0.0] * len(months))
        for idx, total in enumerate(values):
            records.append({"mes": months[idx], "categoria": category, "total": total})
    df = pd.DataFrame(records)
    if df.empty:
        fig = Figure(figsize=(8, 4))
        ax = fig.subplots()
        ax.text(0.5, 0.5, "Sin datos", ha="center", va="center", fontsize=11, color="#666")
        ax.set_axis_off()
        return fig
    plot = (
        ggplot(df, aes(x="mes", y="total", fill="categoria"))
        + geom_bar(stat="identity")
        + labs(title=f"Gastos fijos mensuales {year}", x="Mes", y="Gastos ($)")
        + scale_fill_brewer(type="qual", palette="Set3")
        + scale_x_discrete(limits=months)
        + theme_minimal()
        + theme(
            axis_text_x=element_text(rotation=45, hjust=1),
            figure_size=(8, 4),
            legend_position="right",
        )
    )
    figure = plot.draw()
    return figure


def variable_month_pie_data(year: int, month: int) -> Tuple[str, List[Tuple[str, float]]]:
    label = f"Gastos variables {month_name[month]} {year}"
    repo = FinancialReportRepository(DatabaseConnection())
    rows = repo.variable_expenses(year=year, month=month)
    data: List[Tuple[str, float]] = []
    for row in rows:
        total = float(row.get("total") or 0.0)
        if total <= 0:
            continue
        nombre = row.get("nombre") or "Sin categoría"
        data.append((nombre, total))
    return label, data


def variable_annual_trend_data(year: int, category_id: Optional[int] = None, category_label: str | None = None) -> Tuple[str, List[Tuple[str, float]]]:
    descriptor = "" if not category_label or category_label == "Todas" else f" de {category_label}"
    label = f"Gastos variables por mes{descriptor} {year}"
    repo = FinancialReportRepository(DatabaseConnection())
    rows = (
        repo.variable_monthly_totals(year)
        if category_id is None
        else repo.variable_monthly_totals_by_category(year, category_id)
    )
    months: List[Tuple[str, float]] = []
    for row in rows:
        mes = int(row.get("mes") or 0)
        if mes <= 0:
            continue
        total = float(row.get("total") or 0.0)
        months.append((month_name[mes], total))
    return label, months


def variable_month_pie_figure(year: int, month: int) -> Figure:
    label, data = variable_month_pie_data(year, month)
    records = [{"categoria": name, "total": total} for name, total in data]
    df = pd.DataFrame(records)
    if df.empty:
        fig = Figure(figsize=(6, 4))
        ax = fig.subplots()
        ax.text(0.5, 0.5, "Sin datos", ha="center", va="center", fontsize=11, color="#666")
        ax.set_axis_off()
        return fig
    fig = Figure(figsize=(6, 4))
    ax = fig.subplots()
    totals = df["total"].tolist()
    labels = df["categoria"].tolist()
    cmap = plt.get_cmap("Set3")
    colors = [cmap(i / max(len(labels) - 1, 1)) for i in range(len(labels))]
    # Dibujamos un pastel clásico usando los totales y etiquetamos con leyendas laterales.
    wedges, _, _ = ax.pie(
        totals,
        labels=None,
        autopct="%.1f%%",
        startangle=90,
        colors=colors,
        wedgeprops={"edgecolor": "white"},
    )
    ax.set_title(label)
    ax.axis("equal")
    ax.legend(
        wedges,
        labels,
        title="Categorías",
        loc="center left",
        bbox_to_anchor=(1, 0.5),
        frameon=False,
    )
    return fig


def variable_annual_trend_figure(year: int, category_id: Optional[int] = None, category_label: str | None = None) -> Figure:
    label, data = variable_annual_trend_data(year, category_id, category_label)
    df = pd.DataFrame(data, columns=["mes", "total"])
    if df.empty:
        fig = Figure(figsize=(8, 4))
        ax = fig.subplots()
        ax.text(0.5, 0.5, "Sin datos", ha="center", va="center", fontsize=11, color="#666")
        ax.set_axis_off()
        return fig
    limits = [row[0] for row in data]
    plot = (
        ggplot(df, aes(x="mes", y="total", group=1))
        + geom_line(color="#1976d2", size=1.4)
        + geom_point(color="#1976d2", size=3)
        + labs(title=label, x="Mes", y="Gastos ($)")
        + scale_x_discrete(limits=limits)
        + theme_minimal()
        + theme(
            axis_text_x=element_text(rotation=45, hjust=1),
            figure_size=(8, 4),
        )
    )
    figure = plot.draw()
    return figure


def monthly_incomes_stacked_figure(year: int) -> Figure:
    repo = FinancialReportRepository(DatabaseConnection())
    rows = repo.monthly_incomes_by_category(year)
    months = [month_name[i] for i in range(1, 13)]
    if not rows:
        fig = Figure(figsize=(8, 4))
        ax = fig.subplots()
        ax.text(0.5, 0.5, "Sin datos", ha="center", va="center", fontsize=11, color="#666")
        ax.set_axis_off()
        return fig
    records: list[dict[str, float | str]] = []
    for row in rows:
        periodo = row.get("periodo") or ""
        nombre = row.get("nombre") or "Sin categoría"
        total = float(row.get("total") or 0.0)
        try:
            month_index = int(periodo.split("-")[1])
        except (IndexError, ValueError):
            continue
        if not 1 <= month_index <= 12:
            continue
        records.append({"mes": month_name[month_index], "categoria": nombre, "total": total})
    df = pd.DataFrame(records)
    if df.empty:
        fig = Figure(figsize=(8, 4))
        ax = fig.subplots()
        ax.text(0.5, 0.5, "Sin datos", ha="center", va="center", fontsize=11, color="#666")
        ax.set_axis_off()
        return fig
    df["mes"] = pd.Categorical(df["mes"], categories=months, ordered=True)
    plot = (
        ggplot(df, aes(x="mes", y="total", fill="categoria"))
        + geom_col(position="stack")
        + labs(title=f"Ingresos mensuales por categoría {year}", x="Mes", y="Ingresos ($)")
        + scale_fill_brewer(type="qual", palette="Set3")
        + scale_x_discrete(limits=months)
        + theme_minimal()
        + theme(
            axis_text_x=element_text(rotation=45, hjust=1),
            figure_size=(8, 4),
        )
    )
    figure = plot.draw()
    return figure


def annual_incomes_figure() -> Figure:
    repo = FinancialReportRepository(DatabaseConnection())
    rows = repo.annual_incomes()
    df = pd.DataFrame(rows)
    if df.empty:
        fig = Figure(figsize=(8, 4))
        ax = fig.subplots()
        ax.text(0.5, 0.5, "Sin datos", ha="center", va="center", fontsize=11, color="#666")
        ax.set_axis_off()
        return fig
    df["anio"] = df["anio"].astype(int)
    df["anio_str"] = df["anio"].astype(str)
    plot = (
        ggplot(df, aes(x="anio_str", y="total"))
        + geom_col(fill="#42a5f5", width=0.7)
        + labs(title="Ingresos anuales", x="Año", y="Ingresos ($)")
        + theme_minimal()
        + theme(
            axis_text_x=element_text(rotation=45, hjust=1),
            figure_size=(8, 4),
        )
    )
    figure = plot.draw()
    return figure


def annual_tax_paid_figure() -> Figure:
    """Construye la barra de los impuestos pagados por año."""
    repo = ImpuestoAnualRepository(DatabaseConnection())
    rows = repo.list_tax_payments()
    df = pd.DataFrame(rows)
    fig = Figure(figsize=(8, 4))
    if df.empty:
        ax = fig.subplots()
        ax.text(0.5, 0.5, "Sin registros", ha="center", va="center", fontsize=11, color="#666")
        ax.set_axis_off()
        return fig
    df["anio"] = df["anio"].astype(int)
    df["anio_str"] = df["anio"].astype(str)
    df["impuesto_pagado"] = df["impuesto_pagado"].astype(float)
    plot = (
        ggplot(df, aes(x="anio_str", y="impuesto_pagado"))
        + geom_col(fill="#8e24aa", width=0.7)
        + labs(title="Impuesto pagado por año", x="Año", y="Impuesto pagado ($)")
        + theme_minimal()
        + theme(
            axis_text_x=element_text(rotation=45, hjust=1),
            figure_size=(8, 4),
        )
    )
    return plot.draw()


def _empty_placeholder_figure(message: str, size: tuple[int, int] = (8, 4)) -> Figure:
    fig = Figure(figsize=size)
    ax = fig.subplots()
    ax.text(0.5, 0.5, message, ha="center", va="center", fontsize=11, color="#666")
    ax.set_axis_off()
    return fig


def monthly_spending_bar_figure(year: int, month: int) -> Figure:
    repo = FinancialReportRepository(DatabaseConnection())
    rows = repo.expenses_by_category(year, month)
    if not rows:
        return _empty_placeholder_figure("Sin datos de gasto por categoría")
    df = pd.DataFrame(rows)
    df["total"] = df["total"].astype(float)
    plot = (
        ggplot(df, aes(x="categoria", y="total", fill="categoria"))
        + geom_col(show_legend=False)
        + labs(title=f"Gasto por categoría {month_name[month]} {year}", x="Categoría", y="Total ($)")
        + theme_minimal()
        + theme(axis_text_x=element_text(rotation=45, hjust=1), figure_size=(8, 4))
    )
    return plot.draw()


def monthly_spending_pie_figure(year: int, month: int) -> Figure:
    repo = FinancialReportRepository(DatabaseConnection())
    rows = repo.expenses_by_category(year, month)
    df = pd.DataFrame(rows)
    if df.empty:
        return _empty_placeholder_figure("Sin datos para el pastel de gasto")
    df["total"] = df["total"].astype(float)
    fig = Figure(figsize=(6, 4))
    ax = fig.subplots()
    wedges, _, _ = ax.pie(
        df["total"],
        labels=None,
        autopct="%.1f%%",
        startangle=90,
        wedgeprops={"edgecolor": "white"},
    )
    ax.legend(wedges, df["categoria"], title="Categoría", loc="center left", bbox_to_anchor=(1, 0.5))
    ax.set_title(f"% Gasto por categoría {month_name[month]} {year}")
    ax.axis("equal")
    return fig


def monthly_daily_expense_line_figure(year: int, month: int) -> Figure:
    repo = FinancialReportRepository(DatabaseConnection())
    rows = repo.daily_totals_by_type(year, month, "gasto")
    if not rows:
        return _empty_placeholder_figure("Sin datos diarios de gasto")
    df = pd.DataFrame(rows)
    df["total"] = df["total"].astype(float)
    df["fecha"] = pd.to_datetime(df["fecha"])
    plot = (
        ggplot(df, aes(x="fecha", y="total"))
        + geom_line(color="#d32f2f")
        + geom_point(color="#d32f2f")
        + labs(title=f"Evolución diaria del gasto {month_name[month]} {year}", x="Día", y="Monto ($)")
        + theme_minimal()
        + theme(axis_text_x=element_text(rotation=45, hjust=1), figure_size=(8, 4))
    )
    return plot.draw()


def monthly_income_vs_expense_stacked_figure(year: int, month: int) -> Figure:
    repo = FinancialReportRepository(DatabaseConnection())
    expense_rows = repo.daily_totals_by_type(year, month, "gasto")
    income_rows = repo.daily_totals_by_type(year, month, "ingreso")
    df_expense = pd.DataFrame(expense_rows)
    df_income = pd.DataFrame(income_rows)
    if df_expense.empty and df_income.empty:
        return _empty_placeholder_figure("Sin datos de ingresos y gastos diarios")
    df_expense["total"] = df_expense["total"].astype(float)
    df_income["total"] = df_income["total"].astype(float)
    df_expense["tipo"] = "Gasto"
    df_income["tipo"] = "Ingreso"
    df_union = pd.concat([df_expense, df_income], ignore_index=True)
    df_union["fecha"] = pd.to_datetime(df_union["fecha"])
    plot = (
        ggplot(df_union, aes(x="fecha", y="total", fill="tipo"))
        + geom_col(position="stack")
        + labs(title=f"Ingresos vs gastos diarios {month_name[month]} {year}", x="Día", y="Monto ($)")
        + theme_minimal()
        + theme(axis_text_x=element_text(rotation=45, hjust=1), figure_size=(8, 4))
    )
    return plot.draw()


def monthly_expense_heatmap_figure(year: int, month: int) -> Figure:
    repo = FinancialReportRepository(DatabaseConnection())
    rows = repo.weekly_expense_heatmap(year, month)
    if not rows:
        return _empty_placeholder_figure("Sin datos para el heatmap")
    df = pd.DataFrame(rows)
    df["total"] = df["total"].astype(float)
    pivot = df.pivot(index="dia_semana", columns="semana", values="total").fillna(0)
    fig = Figure(figsize=(8, 4))
    ax = fig.subplots()
    cmap = plt.get_cmap("YlOrRd")
    c = ax.imshow(pivot, aspect="auto", cmap=cmap)
    ax.set_yticks(range(len(pivot.index)))
    weekday_labels = ["Dom", "Lun", "Mar", "Mié", "Jue", "Vie", "Sáb"]
    ax.set_yticklabels([weekday_labels[int(idx) - 1] for idx in pivot.index])
    ax.set_xticks(range(len(pivot.columns)))
    ax.set_xticklabels([str(int(col)) for col in pivot.columns])
    ax.set_xlabel("Semana del año")
    ax.set_title(f"Heatmap semanal de gasto {month_name[month]} {year}")
    fig.colorbar(c, ax=ax, label="$ gasto")
    return fig


def annual_expense_line_figure(year: int) -> Figure:
    repo = FinancialReportRepository(DatabaseConnection())
    rows = repo.monthly_expense_totals(year)
    if not rows:
        return _empty_placeholder_figure("Sin datos mensuales de gasto")
    df = pd.DataFrame(rows)
    df["mes"] = df["mes"].astype(int)
    df["total"] = df["total"].astype(float)
    df["mes_nombre"] = df["mes"].apply(lambda m: month_name[int(m)])
    plot = (
        ggplot(df, aes(x="mes_nombre", y="total", group=1))
        + geom_line(color="#d84315")
        + geom_point(color="#d84315")
        + labs(title=f"Gasto mensual durante {year}", x="Mes", y="Total ($)")
        + theme_minimal()
        + theme(axis_text_x=element_text(rotation=45, hjust=1), figure_size=(8, 4))
    )
    return plot.draw()


def annual_expense_by_category_stacked_figure(year: int) -> Figure:
    repo = FinancialReportRepository(DatabaseConnection())
    rows = repo.expenses_by_category_by_month(year)
    if not rows:
        return _empty_placeholder_figure("Sin datos por categoría")
    df = pd.DataFrame(rows)
    df["mes"] = df["mes"].astype(int)
    df["total"] = df["total"].astype(float)
    df["mes_nombre"] = df["mes"].apply(lambda m: month_name[int(m)])
    plot = (
        ggplot(df, aes(x="mes_nombre", y="total", fill="categoria"))
        + geom_col(position="stack")
        + labs(title=f"Gasto por categoría por mes {year}", x="Mes", y="Total ($)")
        + theme_minimal()
        + theme(axis_text_x=element_text(rotation=45, hjust=1), figure_size=(8, 4))
    )
    return plot.draw()


def annual_expense_boxplot_figure(year: int) -> Figure:
    repo = FinancialReportRepository(DatabaseConnection())
    rows = repo.monthly_expense_totals(year)
    if not rows:
        return _empty_placeholder_figure("Sin datos para el boxplot")
    df = pd.DataFrame(rows)
    df["total"] = df["total"].astype(float)
    plot = (
        ggplot(df, aes(x="1", y="total"))
        + geom_boxplot()
        + labs(title=f"Variación mensual del gasto en {year}", x="", y="Monto ($)")
        + theme_minimal()
        + theme(axis_text_x=element_blank(), figure_size=(6, 4))
    )
    return plot.draw()


def annual_cumulative_savings_figure(year: int) -> Figure:
    repo = FinancialReportRepository(DatabaseConnection())
    rows = repo.monthly_savings(year)
    if not rows:
        return _empty_placeholder_figure("Sin datos de ahorro acumulado")
    df = pd.DataFrame(rows)
    df["periodo"] = pd.to_datetime(df["periodo"])
    df = df.sort_values("periodo")
    df["ahorro"] = df["ahorro"].astype(float)
    df["acumulado"] = df["ahorro"].cumsum()
    plot = (
        ggplot(df, aes(x="periodo", y="acumulado"))
        + geom_line(color="#2e7d32")
        + geom_point(color="#2e7d32")
        + labs(title=f"Ahorro acumulado {year}", x="Mes", y="Ahorro acumulado ($)")
        + theme_minimal()
        + theme(axis_text_x=element_text(rotation=45, hjust=1), figure_size=(8, 4))
    )
    return plot.draw()
"""Herramientas ligeras para representar gráficas simples con Tkinter."""

from __future__ import annotations

from calendar import month_name
from datetime import datetime
from typing import Optional, Tuple

import tkinter as tk

from ..db.connection import DatabaseConnection


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
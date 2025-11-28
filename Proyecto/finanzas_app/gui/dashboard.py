"""Tablero principal que resume indicadores clave."""

from __future__ import annotations

import tkinter as tk

from ..logic.calculos import obtener_dashboard_stats
from ..logic.graficos import monthly_comparison_data, render_monthly_comparison


def _format_currency(value: float | None) -> str:
    if value is None:
        return "Sin datos"
    return f"${value:,.0f}"


class DashboardFrame(tk.Frame):
    """Vista de estados financieros para mostrar la información inicial."""

    def __init__(self, parent: tk.Misc) -> None:
        super().__init__(parent, padx=24, pady=24)
        stats = obtener_dashboard_stats()
        period_label, _ = monthly_comparison_data()

        # Encabezado con saludo y periodo actual para el usuario.
        tk.Label(self, text="¡Hola! Este es tu resumen financiero", font=(None, 14, "bold"), anchor="w").grid(row=0, column=0, columnspan=2, sticky="w")
        tk.Label(self, text=f"Estadísticas del {period_label}", font=(None, 10), fg="#555").grid(row=1, column=0, columnspan=2, sticky="w", pady=(0, 12))

        rows = [
            ("Ahorro mensual", _format_currency(stats.get("monthly_savings"))),
            ("Ahorro anual", _format_currency(stats.get("annual_savings"))),
            ("Gastos del mes", _format_currency(stats.get("monthly_expenses"))),
            ("Ingresos del mes", _format_currency(stats.get("monthly_incomes"))),
            ("Presupuesto mes", _format_currency(stats.get("monthly_budget"))),
        ]
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)

        for idx, (label_text, value) in enumerate(rows, start=2):
            row_frame = tk.Frame(self)
            row_frame.grid(row=idx, column=0, columnspan=2, sticky="ew", pady=4)
            tk.Label(row_frame, text=f"{label_text}:", width=18, anchor="w").pack(side="left")
            tk.Label(row_frame, text=value, width=12, anchor="e", font=(None, 12, "bold")).pack(side="right")

        # Área de dibujo para la comparativa mensual de ingresos vs gastos.
        chart_frame = tk.LabelFrame(self, text="Gastos vs Ingresos", padx=12, pady=12)
        chart_frame.grid(row=len(rows) + 2, column=0, columnspan=2, sticky="ew", pady=(16, 0))
        chart_canvas = tk.Canvas(chart_frame, width=520, height=260, bg="white", highlightthickness=0)
        chart_canvas.pack(fill="both", expand=True)

        # Redibuja el gráfico cada vez que cambia el tamaño para mantener proporciones.
        def _redraw_chart(event: tk.Event | None = None) -> None:
            render_monthly_comparison(chart_canvas)

        chart_canvas.bind("<Configure>", _redraw_chart)

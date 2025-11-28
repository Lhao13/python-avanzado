"""Tablero principal que resume indicadores clave."""

from __future__ import annotations

import tkinter as tk

from ..logic.calculos import obtener_dashboard_stats


def _format_currency(value: float | None) -> str:
    if value is None:
        return "Sin datos"
    return f"${value:,.0f}"


class DashboardFrame(tk.Frame):
    """Vista de estados financieros para mostrar la información inicial."""

    def __init__(self, parent: tk.Misc) -> None:
        super().__init__(parent, padx=24, pady=24)
        stats = obtener_dashboard_stats()
        rows = [
            ("Ahorro mensual", _format_currency(stats.get("monthly_savings"))),
            ("Ahorro anual", _format_currency(stats.get("annual_savings"))),
            ("Gastos del mes", _format_currency(stats.get("monthly_expenses"))),
            ("Ingresos del mes", _format_currency(stats.get("monthly_incomes"))),
            ("Presupuesto mes", _format_currency(stats.get("monthly_budget"))),
        ]
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)

        for idx, (label_text, value) in enumerate(rows):
            row_frame = tk.Frame(self)
            row_frame.grid(row=idx, column=0, columnspan=2, sticky="ew", pady=4)
            tk.Label(row_frame, text=f"{label_text}:", width=18, anchor="w").pack(side="left")
            tk.Label(row_frame, text=value, width=10, anchor="e", font=(None, 12, "bold")).pack(side="right")

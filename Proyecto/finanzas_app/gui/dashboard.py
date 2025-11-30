"""Tablero principal que resume indicadores clave."""

from __future__ import annotations

from datetime import datetime
import tkinter as tk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from ..logic.calculos import obtener_dashboard_stats
from ..logic.graficos import (
    budget_pie_figure,
    monthly_comparison_data,
    objective_comparison_figure,
)
from .theme import Theme


def _format_currency(value: float | None) -> str:
    if value is None:
        return "Sin datos"
    return f"${value:,.0f}"


class DashboardFrame(tk.Frame):
    """Vista de estados financieros para mostrar la información inicial."""

    def __init__(self, parent: tk.Misc) -> None:
        super().__init__(parent, padx=24, pady=24, bg=Theme.BACKGROUND)
        stats = obtener_dashboard_stats()
        period_label, _ = monthly_comparison_data()

        # Encabezado con saludo y periodo actual para el usuario.
        tk.Label(
            self,
            text="¡Hola! Este es tu resumen financiero",
            font=(None, 14, "bold"),
            anchor="w",
            bg=Theme.BACKGROUND,
            fg=Theme.PRIMARY_TEXT,
        ).grid(row=0, column=0, columnspan=2, sticky="w")
        tk.Label(
            self,
            text=f"Estadísticas del {period_label}",
            font=(None, 10),
            fg=Theme.SECONDARY_TEXT,
            bg=Theme.BACKGROUND,
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(0, 12))

        rows = [
            ("Ahorro mensual", _format_currency(stats.get("monthly_savings"))),
            ("Gastos del mes", _format_currency(stats.get("monthly_expenses"))),
            ("Ingresos del mes", _format_currency(stats.get("monthly_incomes"))),
            ("Presupuesto mes", _format_currency(stats.get("monthly_budget"))),
        ]
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)

        for idx, (label_text, value) in enumerate(rows, start=2):
            row_frame = tk.Frame(self, bg=Theme.CARD_BG)
            row_frame.grid(row=idx, column=0, columnspan=2, sticky="ew", pady=4)
            tk.Label(
                row_frame,
                text=f"{label_text}:",
                width=18,
                anchor="w",
                bg=Theme.CARD_BG,
                fg=Theme.PRIMARY_TEXT,
            ).pack(side="left")
            tk.Label(
                row_frame,
                text=value,
                width=12,
                anchor="e",
                font=(None, 12, "bold"),
                bg=Theme.CARD_BG,
                fg=Theme.ACTION_COLOR,
            ).pack(side="right")

        # Espacio para los gráficos lado a lado.
        # Cada sección gráfica usa el fondo general para mantener la jerarquía visual.
        charts_container = tk.Frame(self, bg=Theme.BACKGROUND)
        charts_container.grid(row=len(rows) + 2, column=0, columnspan=2, sticky="nsew", pady=(16, 0))
        charts_container.columnconfigure(0, weight=1)
        charts_container.columnconfigure(1, weight=1)

        bar_frame = tk.LabelFrame(
            charts_container,
            text="Gastos vs Ingresos",
            padx=12,
            pady=12,
            bg=Theme.CARD_BG,
            fg=Theme.PRIMARY_TEXT,
        )
        bar_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        pie_frame = tk.LabelFrame(
            charts_container,
            text="Presupuesto específico",
            padx=12,
            pady=12,
            bg=Theme.CARD_BG,
            fg=Theme.PRIMARY_TEXT,
        )
        pie_frame.grid(row=0, column=1, sticky="nsew", padx=(8, 0))

        self._bar_canvas: FigureCanvasTkAgg | None = None
        self._pie_canvas: FigureCanvasTkAgg | None = None
        # Los contenedores de los gráficos heredan el fondo de la tarjeta para evitar contrastes bruscos.
        self._bar_container = tk.Frame(bar_frame, bg=Theme.CARD_BG)
        self._bar_container.pack(fill="both", expand=True)
        self._pie_container = tk.Frame(pie_frame, bg=Theme.CARD_BG)
        self._pie_container.pack(fill="both", expand=True)

        self._bar_container.bind("<Configure>", lambda _: self._refresh_bar_chart())
        self._pie_container.bind("<Configure>", lambda _: self._refresh_pie_chart())

        self._refresh_bar_chart()
        self._refresh_pie_chart()

    def _refresh_bar_chart(self) -> None:
        year, month = self._current_period()
        figure = objective_comparison_figure(year, month)
        self._bar_canvas = self._render_figure_on_container(self._bar_container, figure, self._bar_canvas)

    def _refresh_pie_chart(self) -> None:
        year, month = self._current_period()
        figure = budget_pie_figure(year, month)
        self._pie_canvas = self._render_figure_on_container(self._pie_container, figure, self._pie_canvas)

    def _current_period(self) -> tuple[int, int]:
        now = datetime.now()
        return now.year, now.month

    def _render_figure_on_container(
        self,
        container: tk.Misc,
        figure: Figure,
        existing: FigureCanvasTkAgg | None,
    ) -> FigureCanvasTkAgg:
        if existing:
            existing.get_tk_widget().destroy()
        canvas = FigureCanvasTkAgg(figure, master=container)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        # Mantiene la referencia para poder re-renderizar rápidamente cuando cambie el tamaño.
        return canvas

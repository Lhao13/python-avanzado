"""Vista para comparar distintos cortes de ingresos."""

from __future__ import annotations

from calendar import month_name
from datetime import datetime
from typing import Any, Sequence

import tkinter as tk
from tkinter import ttk, messagebox

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from ..db.connection import DatabaseConnection
from ..logic.graficos import annual_incomes_figure, monthly_incomes_stacked_figure
from ..repositories import FinancialReportRepository


def _format_money(value: float | None) -> str:
    if value is None:
        return "Sin datos"
    return f"${value:,.2f}"


def _make_tree(frame: tk.Frame, title: str, columns: tuple[str, ...]) -> ttk.Treeview:
    labelframe = ttk.LabelFrame(frame, text=title, padding=12)
    tree = ttk.Treeview(labelframe, columns=columns, show="headings", height=8)
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, anchor="center", width=160)
    tree.pack(fill="both", expand=True)
    labelframe.pack(fill="both", expand=True, pady=6)
    return tree


class IngresosFrame(tk.Frame):
    """Panel con los reportes mensuales, anuales y por categoría."""

    def __init__(self, parent: tk.Misc) -> None:
        super().__init__(parent, padx=12, pady=12)
        self._report = FinancialReportRepository(DatabaseConnection())
        self._monthly_year_var = tk.StringVar(value=str(self._initial_year()))
        self._available_years = self._report.get_available_years() or [self._initial_year()]
        if str(self._initial_year()) not in map(str, self._available_years):
            self._available_years.append(self._initial_year())
        self._available_years = sorted(set(self._available_years))

        control_frame = tk.Frame(self)
        control_frame.pack(fill="x", pady=(0, 12))
        self._build_monthly_controls(control_frame)

        body_frame = tk.Frame(self)
        body_frame.pack(fill="both", expand=True)
        body_frame.columnconfigure(0, weight=1)
        body_frame.columnconfigure(1, weight=1)

        tree_frame = tk.Frame(body_frame)
        tree_frame.grid(row=0, column=0, sticky="nsew")
        chart_frame = tk.Frame(body_frame)
        chart_frame.grid(row=0, column=1, sticky="nsew")

        self._monthly_tree = _make_tree(tree_frame, "Ingresos mensuales", ("Mes", "Total"))
        self._annual_tree = _make_tree(tree_frame, "Ingresos anuales", ("Año", "Total"))
        self._category_tree = _make_tree(tree_frame, "Ingresos por categoría", ("Categoría", "Total"))

        self._monthly_chart_canvas: FigureCanvasTkAgg | None = None
        self._annual_chart_canvas: FigureCanvasTkAgg | None = None
        self._monthly_chart_container: tk.Frame | None = None
        self._annual_chart_container: tk.Frame | None = None
        self._build_charts_section(chart_frame)

        self._refresh_monthly()
        self._refresh_annual()
        self._refresh_category()
        self._refresh_monthly_chart()
        self._refresh_annual_chart()

    def _initial_year(self) -> int:
        return datetime.now().year

    def _build_monthly_controls(self, parent: tk.Frame) -> None:
        frame = tk.LabelFrame(parent, text="Mensuales", padx=8, pady=6)
        frame.pack(side="left", padx=6, fill="x", expand=True)
        tk.Label(frame, text="Año").grid(row=0, column=0, sticky="w")
        combo = ttk.Combobox(frame, textvariable=self._monthly_year_var, state="readonly", width=8)
        combo["values"] = [str(year) for year in self._available_years]
        combo.grid(row=1, column=0, padx=(0, 8))
        tk.Button(frame, text="Actualizar", command=self._refresh_monthly).grid(row=1, column=1)
        # Este control solo afecta el reporte mensual.

    def _refresh_monthly(self) -> None:
        try:
            year = int(self._monthly_year_var.get())
        except ValueError:
            messagebox.showerror("Ingresos mensuales", "El año debe ser numérico.")
            return
        rows = self._report.monthly_incomes(year=year)
        month_values: dict[str, float] = {row["periodo"]: row.get("total", 0.0) for row in rows}
        self._populate_monthly(month_values, year)
        self._refresh_monthly_chart(year)

    def _populate_monthly(self, month_values: dict[str, float], year: int) -> None:
        for child in self._monthly_tree.get_children():
            self._monthly_tree.delete(child)
        for month_index in range(1, 13):
            label = month_name[month_index]
            period_key = f"{year}-{month_index:02d}"
            total = month_values.get(period_key)
            self._monthly_tree.insert("", "end", values=(label, _format_money(total)))
        # Se reconstruye la vista mensual con los 12 meses incluso si hay datos faltantes.

    def _refresh_annual(self) -> None:
        rows = self._report.annual_incomes()
        self._populate_tree(self._annual_tree, rows, "anio")

    def _refresh_category(self) -> None:
        rows = self._report.incomes_by_category()
        self._populate_tree(self._category_tree, rows, "nombre")

    def _build_charts_section(self, parent: tk.Frame) -> None:
        frame = tk.Frame(parent)
        frame.pack(fill="both", expand=True)
        frame.columnconfigure(0, weight=1)

        monthly_frame = ttk.LabelFrame(frame, text="Ingresos mensuales por categoría", padding=8)
        monthly_frame.pack(fill="both", expand=True, pady=(0, 6))
        self._monthly_chart_container = tk.Frame(monthly_frame)
        self._monthly_chart_container.pack(fill="both", expand=True)
        self._monthly_chart_container.bind("<Configure>", lambda _: self._refresh_monthly_chart())

        annual_frame = ttk.LabelFrame(frame, text="Ingresos anuales", padding=8)
        annual_frame.pack(fill="both", expand=True)
        self._annual_chart_container = tk.Frame(annual_frame)
        self._annual_chart_container.pack(fill="both", expand=True)
        self._annual_chart_container.bind("<Configure>", lambda _: self._refresh_annual_chart())

    def _refresh_monthly_chart(self, year_override: int | None = None) -> None:
        try:
            year = year_override if year_override is not None else int(self._monthly_year_var.get())
        except ValueError:
            return
        if not self._monthly_chart_container:
            return
        figure = monthly_incomes_stacked_figure(year)
        self._monthly_chart_canvas = self._render_figure_on_container(
            self._monthly_chart_container, figure, self._monthly_chart_canvas
        )

    def _refresh_annual_chart(self) -> None:
        if not self._annual_chart_container:
            return
        figure = annual_incomes_figure()
        self._annual_chart_canvas = self._render_figure_on_container(
            self._annual_chart_container, figure, self._annual_chart_canvas
        )

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
        # Mantiene la referencia para poder refrescar el lienzo cuando se redimensiona.
        return canvas

    def _populate_tree(self, tree: ttk.Treeview, rows: Sequence[dict[str, Any]], label_key: str) -> None:
        for child in tree.get_children():
            tree.delete(child)
        if not rows:
            tree.insert("", "end", values=("Sin datos", ""))
            return
        for row in rows:
            label = row.get(label_key, "-")
            tree.insert("", "end", values=(label, _format_money(row.get("total"))))
        # Cada fila combina la etiqueta deseada con el total formateado.

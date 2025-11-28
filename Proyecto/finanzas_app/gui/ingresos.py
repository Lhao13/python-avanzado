"""Vista para comparar distintos cortes de ingresos."""

from __future__ import annotations

from calendar import month_name
from datetime import datetime
from typing import Any, Sequence

import tkinter as tk
from tkinter import ttk, messagebox

from ..db.connection import DatabaseConnection
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

        self._monthly_tree = _make_tree(self, "Ingresos mensuales", ("Mes", "Total"))
        self._annual_tree = _make_tree(self, "Ingresos anuales", ("Año", "Total"))
        self._category_tree = _make_tree(self, "Ingresos por categoría", ("Categoría", "Total"))

        self._refresh_monthly()
        self._refresh_annual()
        self._refresh_category()

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

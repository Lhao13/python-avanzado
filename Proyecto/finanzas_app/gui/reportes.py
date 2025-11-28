"""Panel para reportes financieros."""

from __future__ import annotations

from calendar import month_name
from datetime import datetime
from typing import List

import tkinter as tk
from tkinter import ttk, messagebox

from ..db.connection import DatabaseConnection
from ..repositories import FinancialReportRepository


def _format_money(value: float | None) -> str:
    if value is None:
        return "Sin datos"
    return f"${value:,.2f}"


class ReportesFrame(tk.Frame):
    """Panel que genera reportes anuales o mensuales con los datos completos."""

    def __init__(self, parent: tk.Misc) -> None:
        super().__init__(parent, padx=12, pady=12)
        self._repo = FinancialReportRepository(DatabaseConnection())
        self._annual_year_var = tk.StringVar()
        self._monthly_year_var = tk.StringVar()
        self._monthly_month_var = tk.StringVar(value=month_name[datetime.now().month])

        tk.Label(self, text="REPORTES", font=(None, 14, "bold")).pack(anchor="w")
        self._build_annual_section()
        self._build_monthly_section()
        self._build_transactions_table()
        self._refresh_available_years()

    def _build_annual_section(self) -> None:
        frame = tk.LabelFrame(self, text="Reporte anual", padx=8, pady=8)
        frame.pack(fill="x", pady=(8, 4))
        tk.Label(frame, text="Muestra todas las transacciones de un año.").grid(row=0, column=0, sticky="w")
        self._annual_year_combo = ttk.Combobox(frame, textvariable=self._annual_year_var, state="readonly", width=12)
        self._annual_year_combo.grid(row=1, column=0, pady=(6, 0))
        ttk.Button(frame, text="Generar reporte anual", command=self._generate_annual_report).grid(row=1, column=1, padx=(12, 0), pady=(6, 0))

    def _build_monthly_section(self) -> None:
        frame = tk.LabelFrame(self, text="Reporte mensual", padx=8, pady=8)
        frame.pack(fill="x", pady=(4, 8))
        tk.Label(frame, text="Selecciona año y mes para ver el detalle.").grid(row=0, column=0, columnspan=3, sticky="w")
        tk.Label(frame, text="Año").grid(row=1, column=0, sticky="w", pady=(6, 0))
        self._monthly_year_combo = ttk.Combobox(frame, textvariable=self._monthly_year_var, state="readonly", width=10)
        self._monthly_year_combo.grid(row=1, column=1, pady=(6, 0))
        tk.Label(frame, text="Mes").grid(row=2, column=0, sticky="w")
        month_values = [month_name[i] for i in range(1, 13)]
        ttk.Combobox(frame, textvariable=self._monthly_month_var, state="readonly", values=month_values, width=12).grid(row=2, column=1)
        ttk.Button(frame, text="Generar reporte mensual", command=self._generate_monthly_report).grid(row=3, column=0, columnspan=2, pady=(8, 0))

    def _build_transactions_table(self) -> None:
        container = tk.LabelFrame(self, text="Transacciones", padx=4, pady=4)
        container.pack(fill="both", expand=True)

        columns = ("id", "fecha", "categoria", "tipo", "monto", "cantidad", "descripcion")
        self._transactions_tree = ttk.Treeview(container, columns=columns, show="headings")
        for column in columns:
            anchor = "center" if column in ("id", "fecha", "tipo", "categoria") else "e"
            heading = column.replace("_", " ").title()
            self._transactions_tree.heading(column, text=heading)
            self._transactions_tree.column(column, anchor=anchor, width=120)

        self._transactions_tree.grid(row=0, column=0, sticky="nsew")
        container.rowconfigure(0, weight=1)
        container.columnconfigure(0, weight=1)

        scrollbar_y = ttk.Scrollbar(container, orient="vertical", command=self._transactions_tree.yview)
        scrollbar_y.grid(row=0, column=1, sticky="ns")
        self._transactions_tree.configure(yscrollcommand=scrollbar_y.set)

        scrollbar_x = ttk.Scrollbar(container, orient="horizontal", command=self._transactions_tree.xview)
        scrollbar_x.grid(row=1, column=0, sticky="ew")
        self._transactions_tree.configure(xscrollcommand=scrollbar_x.set)

    def _refresh_available_years(self) -> None:
        years = self._repo.get_available_years()
        if not years:
            years = [datetime.now().year]
        values = [str(year) for year in sorted(set(years))]
        self._annual_year_combo["values"] = values
        self._monthly_year_combo["values"] = values
        latest = values[-1]
        self._annual_year_var.set(latest)
        self._monthly_year_var.set(latest)

    def _generate_annual_report(self) -> None:
        try:
            year = int(self._annual_year_var.get())
        except ValueError:
            messagebox.showerror("Reportes", "Selecciona un año válido para generar el reporte anual.")
            return
        rows = self._repo.transactions_for_year(year)
        self._populate_transactions(rows)

    def _generate_monthly_report(self) -> None:
        try:
            year = int(self._monthly_year_var.get())
        except ValueError:
            messagebox.showerror("Reportes", "Selecciona un año válido para el reporte mensual.")
            return
        month = self._month_name_to_number(self._monthly_month_var.get())
        if month is None:
            messagebox.showerror("Reportes", "Selecciona un mes válido para el reporte mensual.")
            return
        rows = self._repo.transactions_for_month(year, month)
        self._populate_transactions(rows)

    def _populate_transactions(self, rows: List[dict]) -> None:
        for child in self._transactions_tree.get_children():
            self._transactions_tree.delete(child)
        if not rows:
            self._transactions_tree.insert("", "end", values=("—", "—", "—", "—", "—", "—", "Sin datos"))
            return
        for row in rows:
            fecha = row.get("fecha")
            fecha_str = fecha.strftime("%d/%m/%Y") if hasattr(fecha, "strftime") else (fecha or "—")
            self._transactions_tree.insert(
                "",
                "end",
                values=(
                    row.get("id_transaccion"),
                    fecha_str,
                    row.get("categoria"),
                    row.get("categoria_tipo"),
                    _format_money(row.get("monto")),
                    row.get("cantidad") or "—",
                    row.get("description") or "",
                ),
            )

    @staticmethod
    def _month_name_to_number(name: str) -> int | None:
        try:
            return list(month_name).index(name)
        except ValueError:
            return None

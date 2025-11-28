"""Panel para visualizar gastos fijos, variables y por categoría."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Callable

import tkinter as tk
from tkinter import ttk, messagebox

from ..db.connection import DatabaseConnection
from ..repositories import CategoriaRepository, FinancialReportRepository, TransaccionRepository


def _format_money(value: float | None) -> str:
    if value is None:
        return "Sin datos"
    return f"${value:,.2f}"


def _make_tree(frame: tk.Frame, title: str, columns: tuple[str, ...]) -> ttk.Treeview:
    labelframe = ttk.LabelFrame(frame, text=title, padding=12)
    tree = ttk.Treeview(labelframe, columns=columns, show="headings", height=6)
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, anchor="center", width=180)
    tree.pack(fill="both", expand=True)
    labelframe.pack(fill="both", expand=True, pady=6)
    return tree


class GastosFrame(tk.Frame):
    """Panel con secciones para gastos fijos, variables y por categoría."""

    def __init__(self, parent: tk.Misc) -> None:
        super().__init__(parent, padx=12, pady=12)
        self._db_connection = DatabaseConnection()
        self._report_repo = FinancialReportRepository(self._db_connection)
        self._categoria_repo = CategoriaRepository(self._db_connection)
        self._trans_repo = TransaccionRepository(self._db_connection)
        self._fixed_month_var = tk.StringVar(value="1")
        self._fixed_year_var = tk.StringVar(value=str(self._current_year()))
        self._variable_month_var = tk.StringVar(value="1")
        self._variable_year_var = tk.StringVar(value=str(self._current_year()))
        self._category_var = tk.StringVar()
        categories = self._categoria_repo.list_by_tipo("gasto")
        # Cacheamos nombre->id para usar en el filtro historicado.
        self._category_catalog = {cat.nombre: cat.id_categoria for cat in categories}
        if categories:
            self._category_var.set(categories[0].nombre)
        else:
            self._category_var.set("Sin categorías")

        control_frame = tk.Frame(self)
        control_frame.pack(fill="x", pady=(0, 12))
        self._build_controls(control_frame, "Fijos", self._fixed_month_var, self._fixed_year_var, self._refresh_fixed)
        self._build_controls(
            control_frame,
            "Variables",
            self._variable_month_var,
            self._variable_year_var,
            self._refresh_variable,
        )
        self._build_category_controls(control_frame)

        self._fixed_tree = _make_tree(self, "Gastos fijos mensuales", ("Categoría", "Total"))
        self._variable_tree = _make_tree(self, "Gastos variables mensuales", ("Categoría", "Total"))
        self._category_tree = _make_tree(self, "Historial por categoría", ("Fecha", "Total", "Cantidad"))

        self._refresh_fixed()
        self._refresh_variable()
        self._refresh_category_history()

    def _current_year(self) -> int:
        return datetime.now().year

    def _build_controls(
        self,
        parent: tk.Frame,
        title: str,
        month_var: tk.StringVar,
        year_var: tk.StringVar,
        callback: Callable[[], None],
        month_enabled: bool = True,
    ) -> None:
        frame = tk.LabelFrame(parent, text=title, padx=8, pady=6)
        frame.pack(side="left", padx=6, fill="x", expand=True)
        if month_enabled:
            tk.Label(frame, text="Mes").grid(row=0, column=0, sticky="w")
            combo = ttk.Combobox(frame, textvariable=month_var, state="readonly", width=5)
            combo["values"] = [str(i) for i in range(1, 13)]
            combo.grid(row=1, column=0, padx=(0, 8))
        tk.Label(frame, text="Año").grid(row=0, column=1, sticky="w")
        tk.Entry(frame, textvariable=year_var, width=6).grid(row=1, column=1, padx=(0, 8))
        tk.Button(frame, text="Actualizar", command=callback).grid(row=1, column=2)

    def _refresh_fixed(self) -> None:
        try:
            month = int(self._fixed_month_var.get())
            year = int(self._fixed_year_var.get())
        except ValueError:
            messagebox.showerror("Gastos fijos", "Mes y año deben ser numéricos.")
            return
        rows = self._report_repo.monthly_fixed_expenses(year=year, month=month)
        self._populate_tree(self._fixed_tree, rows)

    def _refresh_variable(self) -> None:
        try:
            month = int(self._variable_month_var.get())
            year = int(self._variable_year_var.get())
        except ValueError:
            messagebox.showerror("Gastos variables", "Mes y año deben ser numéricos.")
            return
        rows = self._report_repo.variable_expenses(year=year, month=month)
        self._populate_tree(self._variable_tree, rows)

    def _build_category_controls(self, parent: tk.Frame) -> None:
        frame = tk.LabelFrame(parent, text="Por categoría", padx=8, pady=6)
        frame.pack(side="left", padx=6, fill="x", expand=True)
        tk.Label(frame, text="Categoría").grid(row=0, column=0, sticky="w")
        combo = ttk.Combobox(frame, textvariable=self._category_var, state="readonly")
        combo["values"] = list(self._category_catalog.keys()) or ["Sin categorías"]
        combo.grid(row=1, column=0, padx=(0, 8))
        tk.Button(frame, text="Actualizar", command=self._refresh_category_history).grid(row=1, column=1)
        # No tiene mes/año porque muestra el histórico completo de la categoría.

    def _refresh_category_history(self) -> None:
        selected = self._category_var.get()
        category_id = self._category_catalog.get(selected)
        if category_id is None:
            messagebox.showwarning("Historial por categoría", "No hay categorías registradas para mostrar.")
            self._populate_history([])
            return
        # Pedimos todas las transacciones de la categoría seleccionada.
        rows = self._trans_repo.list_by_categoria(category_id)
        self._populate_history(rows)

    def _populate_history(self, rows: list[Any]) -> None:
        for child in self._category_tree.get_children():
            self._category_tree.delete(child)
        if not rows:
            self._category_tree.insert("", "end", values=("Sin datos", "", ""))
            return
        # Insertamos cada transacción, formateando monto y fecha.
        for row in rows:
            total = _format_money(getattr(row, "monto", None))
            fecha = getattr(row, "fecha", None)
            cantidad = getattr(row, "cantidad", "-")
            fecha_str = fecha.strftime("%Y-%m-%d") if hasattr(fecha, "strftime") else str(fecha)
            self._category_tree.insert("", "end", values=(fecha_str, total, cantidad))

    def _populate_tree(self, tree: ttk.Treeview, rows: list[dict[str, Any]]) -> None:
        for child in tree.get_children():
            tree.delete(child)
        if not rows:
            tree.insert("", "end", values=("Sin datos", ""))
            return
        # Cada fila contiene el nombre de la categoría y un total formateado.
        for row in rows:
            tree.insert("", "end", values=(row.get("nombre", "-"), _format_money(row.get("total"))))

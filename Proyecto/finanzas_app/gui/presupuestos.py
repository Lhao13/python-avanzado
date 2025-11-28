from __future__ import annotations

from datetime import datetime
import tkinter as tk
from tkinter import messagebox, ttk

from ..db.connection import DatabaseConnection
from ..models import Categoria, PresupuestoEspecifico, PresupuestoGeneral
from ..repositories import (
    CategoriaRepository,
    PresupuestoEspecificoRepository,
    PresupuestoGeneralRepository,
)


class PresupuestosFrame(tk.Frame):
    """Vista para registrar presupuestos mensual, anual y específicos."""

    def __init__(self, parent: tk.Misc) -> None:
        super().__init__(parent, padx=24, pady=24)
        self._db_connection = DatabaseConnection()
        self._categoria_repo = CategoriaRepository(self._db_connection)
        self._presupuesto_general_repo = PresupuestoGeneralRepository(self._db_connection)
        self._presupuesto_especifico_repo = PresupuestoEspecificoRepository(self._db_connection)
        self._expense_categories = self._load_expense_categories()
        self._category_lookup = {
            f"{cat.id_categoria} - {cat.nombre}": cat.id_categoria for cat in self._expense_categories
        }

        now = datetime.now()
        self._monthly_year_var = tk.StringVar(value=str(now.year))
        self._monthly_month_var = tk.StringVar(value=str(now.month))
        self._monthly_amount_var = tk.StringVar()

        self._annual_year_var = tk.StringVar(value=str(now.year))
        self._annual_amount_var = tk.StringVar()

        self._specific_category_var = tk.StringVar()
        self._specific_year_var = tk.StringVar(value=str(now.year))
        self._specific_month_var = tk.StringVar(value=str(now.month))
        self._specific_amount_var = tk.StringVar()

        self._build_ui()

    def _load_expense_categories(self) -> list[Categoria]:
        categories = self._categoria_repo.list_all()
        return [cat for cat in categories if cat.tipo == "gasto"]

    def _build_ui(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        container = tk.Frame(self)
        container.pack(fill="both", expand=True)

        self._build_monthly_section(container).grid(row=0, column=0, sticky="ew", pady=8)
        self._build_annual_section(container).grid(row=1, column=0, sticky="ew", pady=8)
        self._build_specific_section(container).grid(row=2, column=0, sticky="ew", pady=8)

    def _build_monthly_section(self, parent: tk.Frame) -> ttk.LabelFrame:
        labelframe = ttk.LabelFrame(parent, text="Presupuesto mensual global", padding=12)
        self._build_row(labelframe, "Año", tk.Entry(labelframe, textvariable=self._monthly_year_var))
        self._build_row(labelframe, "Mes", self._make_month_combo(labelframe, self._monthly_month_var))
        self._build_row(labelframe, "Monto", tk.Entry(labelframe, textvariable=self._monthly_amount_var))
        tk.Button(labelframe, text="Guardar mensual", command=self._save_monthly).grid(
            row=3, column=0, columnspan=2, pady=(8, 0)
        )
        return labelframe

    def _build_annual_section(self, parent: tk.Frame) -> ttk.LabelFrame:
        labelframe = ttk.LabelFrame(parent, text="Presupuesto anual global", padding=12)
        self._build_row(labelframe, "Año", tk.Entry(labelframe, textvariable=self._annual_year_var))
        self._build_row(labelframe, "Monto", tk.Entry(labelframe, textvariable=self._annual_amount_var))
        tk.Button(labelframe, text="Guardar anual", command=self._save_annual).grid(
            row=2, column=0, columnspan=2, pady=(8, 0)
        )
        return labelframe

    def _build_specific_section(self, parent: tk.Frame) -> ttk.LabelFrame:
        labelframe = ttk.LabelFrame(parent, text="Presupuestos específicos", padding=12)
        combo = ttk.Combobox(labelframe, textvariable=self._specific_category_var, state="readonly")
        combo["values"] = list(self._category_lookup.keys())
        if combo["values"]:
            combo.current(0)
        self._build_row(labelframe, "Categoría", combo)
        self._build_row(labelframe, "Año", tk.Entry(labelframe, textvariable=self._specific_year_var))
        self._build_row(labelframe, "Mes", self._make_month_combo(labelframe, self._specific_month_var))
        self._build_row(labelframe, "Monto", tk.Entry(labelframe, textvariable=self._specific_amount_var))
        tk.Button(labelframe, text="Guardar específico", command=self._save_specific).grid(
            row=4, column=0, columnspan=2, pady=(8, 0)
        )
        return labelframe

    def _build_row(self, parent: tk.Frame, label: str, widget: tk.Widget) -> None:
        row = parent.grid_size()[1]
        tk.Label(parent, text=f"{label}:").grid(row=row, column=0, sticky="e", padx=(0, 6), pady=4)
        widget.grid(row=row, column=1, sticky="ew", pady=4)
        parent.columnconfigure(1, weight=1)

    def _make_month_combo(self, parent: tk.Frame, variable: tk.StringVar) -> ttk.Combobox:
        combo = ttk.Combobox(parent, textvariable=variable, state="readonly")
        combo["values"] = [str(i) for i in range(1, 13)]
        combo.current(int(variable.get()) - 1 if variable.get().isdigit() else 0)
        return combo

    def _parse_int(self, value: str, field: str) -> int:
        try:
            return int(value)
        except ValueError as exc:
            raise ValueError(f"{field} debe ser un número entero.") from exc

    def _parse_float(self, value: str, field: str) -> float:
        try:
            return float(value)
        except ValueError as exc:
            raise ValueError(f"{field} debe ser un número válido.") from exc

    def _save_monthly(self) -> None:
        try:
            year = self._parse_int(self._monthly_year_var.get().strip(), "Año")
            month = self._parse_int(self._monthly_month_var.get().strip(), "Mes")
            amount = self._parse_float(self._monthly_amount_var.get().strip(), "Monto")
            presupuesto = PresupuestoGeneral(
                periodo="mensual", anio=year, mes=month, monto_total=amount
            )
            self._presupuesto_general_repo.create(presupuesto)
            messagebox.showinfo("Presupuesto mensual", "Presupuesto mensual guardado correctamente.")
            self._monthly_amount_var.set("")
        except Exception as exc:
            messagebox.showerror("Presupuesto mensual", str(exc))

    def _save_annual(self) -> None:
        try:
            year = self._parse_int(self._annual_year_var.get().strip(), "Año")
            amount = self._parse_float(self._annual_amount_var.get().strip(), "Monto")
            presupuesto = PresupuestoGeneral(periodo="anual", anio=year, monto_total=amount)
            self._presupuesto_general_repo.create(presupuesto)
            messagebox.showinfo("Presupuesto anual", "Presupuesto anual guardado correctamente.")
            self._annual_amount_var.set("")
        except Exception as exc:
            messagebox.showerror("Presupuesto anual", str(exc))

    def _save_specific(self) -> None:
        try:
            category_key = self._specific_category_var.get()
            categoria_id = self._category_lookup.get(category_key)
            if not categoria_id:
                raise ValueError("Selecciona una categoría de gasto válida.")
            year = self._parse_int(self._specific_year_var.get().strip(), "Año")
            month = self._parse_int(self._specific_month_var.get().strip(), "Mes")
            amount = self._parse_float(self._specific_amount_var.get().strip(), "Monto")
            presupuesto = PresupuestoEspecifico(
                anio=year, mes=month, monto=amount, categoria_id=categoria_id
            )
            self._presupuesto_especifico_repo.create(presupuesto)
            messagebox.showinfo("Presupuesto específico", "Presupuesto específico guardado correctamente.")
            self._specific_amount_var.set("")
        except Exception as exc:
            messagebox.showerror("Presupuesto específico", str(exc))

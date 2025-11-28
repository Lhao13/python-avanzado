"""Panel dedicado a revisar y comparar datos fiscales."""

from __future__ import annotations

from calendar import month_name
from datetime import datetime
from typing import List, Tuple

import tkinter as tk
from tkinter import ttk, messagebox

from ..db.connection import DatabaseConnection
from ..logic.calculos import annual_tax_summary, available_years, tax_difference
from ..models import ImpuestoAnual
from ..repositories import ImpuestoAnualRepository


def _format_money(value: float | None) -> str:
    if value is None:
        return "Sin datos"
    return f"${value:,.2f}"


def _create_card(parent: tk.Frame, title: str, text_var: tk.StringVar) -> tk.Frame:
    """Construye una tarjeta con título y valor que después se coloca en el grid."""
    frame = tk.Frame(parent, bd=1, relief="solid", padx=8, pady=6)
    tk.Label(frame, text=title, font=(None, 10, "bold")).pack(anchor="w")
    tk.Label(frame, textvariable=text_var, font=(None, 12)).pack(anchor="w")
    return frame


class ImpuestosFrame(tk.Frame):
    """Interfaz para calcular y contrastar impuestos anuales."""

    def __init__(self, parent: tk.Misc) -> None:
        super().__init__(parent, padx=12, pady=12)
        self._impuesto_repo = ImpuestoAnualRepository(DatabaseConnection())
        self._years = available_years() or [self._current_year()]
        if str(self._current_year()) not in map(str, self._years):
            self._years.append(self._current_year())
        self._years = sorted(set(self._years))
        self._year_var = tk.StringVar(master=self, value=str(self._years[-1]))
        self._payment_month_var = tk.StringVar(master=self, value=month_name[self._current_month()])
        self._payment_amount_var = tk.StringVar(master=self)
        self._payment_history: List[Tuple[str, float, datetime]] = []

        self._income_var = tk.StringVar(master=self, value="Sin datos")
        self._deductible_var = tk.StringVar(master=self, value="Sin datos")
        self._base_var = tk.StringVar(master=self, value="Sin datos")
        self._calculated_var = tk.StringVar(master=self, value="Sin datos")
        self._paid_total_var = tk.StringVar(master=self, value=_format_money(0.0))
        self._difference_var = tk.StringVar(master=self, value="Sin datos")

        tk.Label(self, text="IMPUESTOS", font=(None, 14, "bold")).pack(anchor="w")
        self._build_year_selector()

        content = tk.Frame(self)
        content.pack(fill="both", expand=True)
        self._build_summary_board(content)
        self._build_actions(content)

        self._render_payment_history()
        self._load_summary()

    def _current_year(self) -> int:
        return datetime.now().year

    def _current_month(self) -> int:
        return datetime.now().month

    def _build_year_selector(self) -> None:
        frame = tk.LabelFrame(self, text="Año fiscal", padx=8, pady=6)
        frame.pack(fill="x", pady=(0, 12))
        combo = ttk.Combobox(frame, textvariable=self._year_var, state="readonly", width=10)
        combo["values"] = [str(year) for year in self._years]
        combo.grid(row=0, column=0, padx=(0, 12))
        ttk.Button(frame, text="Cargar datos", command=self._load_summary).grid(row=0, column=1)

    def _build_summary_board(self, parent: tk.Frame) -> None:
        tk.Label(parent, text="SECCIÓN 1 — RESUMEN FISCAL DEL AÑO", font=(None, 10, "bold")).pack(anchor="w")
        grid = tk.Frame(parent)
        grid.pack(fill="x")
        # Dividir las tarjetas en dos filas de tres columnas para aprovechar mejor el espacio.
        grid.columnconfigure((0, 1, 2), weight=1)
        cards = [
            ("Ingreso total anual", self._income_var),
            ("Gastos deducibles", self._deductible_var),
            ("Base imponible", self._base_var),
            ("Impuesto calculado", self._calculated_var),
            ("Impuesto pagado", self._paid_total_var),
            ("Diferencia", self._difference_var),
        ]
        for index, (title, text_var) in enumerate(cards):
            row = index // 3
            column = index % 3
            card = _create_card(grid, title, text_var)
            card.grid(row=row, column=column, sticky="nsew", padx=6, pady=6)

    def _build_actions(self, parent: tk.Frame) -> None:
        actions = tk.LabelFrame(parent, text="SECCIÓN 2 — PAGOS REGISTRADOS", padx=8, pady=8)
        actions.pack(fill="both", expand=True, pady=(12, 0))
        tk.Label(actions, text="Registrar impuesto pagado").grid(row=0, column=0, columnspan=3, sticky="w")

        month_combo = ttk.Combobox(actions, textvariable=self._payment_month_var, state="readonly", width=16)
        month_combo["values"] = [month_name[i] for i in range(1, 13)]
        month_combo.grid(row=1, column=0, pady=(4, 0))
        tk.Label(actions, text="Monto").grid(row=1, column=1, sticky="w", padx=(12, 0))
        tk.Entry(actions, textvariable=self._payment_amount_var, width=12).grid(row=1, column=2, padx=(4, 0))

        ttk.Button(actions, text="Registrar pago", command=self._register_payment).grid(row=2, column=0, columnspan=3, pady=(8, 0))
        ttk.Button(actions, text="Guardar resumen anual", command=self._save_summary).grid(row=3, column=0, columnspan=3, pady=(8, 0))
        tk.Label(
            actions,
            text="Los registros que vayas creando se listan abajo para seguir el avance fiscal.",
            wraplength=420,
        ).grid(row=4, column=0, columnspan=3, pady=(8, 0))

        actions.rowconfigure(5, weight=1)
        history_frame = tk.Frame(actions)
        history_frame.grid(row=5, column=0, columnspan=3, sticky="nsew", pady=(12, 0))
        history_frame.columnconfigure(0, weight=1)

        # Configurar la tabla que lista los pagos para llevar un seguimiento continuo.
        columns = ("mes", "monto", "fecha")
        self._payments_tree = ttk.Treeview(history_frame, columns=columns, show="headings", height=6)
        self._payments_tree.heading("mes", text="Mes")
        self._payments_tree.heading("monto", text="Monto")
        self._payments_tree.heading("fecha", text="Registrado")
        self._payments_tree.column("mes", anchor="center", width=140)
        self._payments_tree.column("monto", anchor="center", width=120)
        self._payments_tree.column("fecha", anchor="center", width=160)
        self._payments_tree.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(history_frame, orient="vertical", command=self._payments_tree.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self._payments_tree.configure(yscrollcommand=scrollbar.set)

    def _load_summary(self) -> None:
        try:
            year = int(self._year_var.get())
        except ValueError:
            messagebox.showerror("Impuestos", "Selecciona un año fiscal válido.")
            return
        summary = annual_tax_summary(year)
        self._income_var.set(_format_money(summary.get("income_total")))
        self._deductible_var.set(_format_money(summary.get("deductible_expenses")))
        self._base_var.set(_format_money(summary.get("base_imponible")))
        self._calculated_var.set(_format_money(summary.get("calculated_tax")))
        self._reset_payment_records()
        self._update_difference(year)

    def _update_paid_display(self) -> None:
        total = self._total_paid()
        self._paid_total_var.set(_format_money(total))

    def _reset_payment_records(self) -> None:
        """Borra los pagos cargados y actualiza el árbol y totales."""
        self._payment_history.clear()
        self._render_payment_history()
        self._update_paid_display()

    def _update_difference(self, year: int) -> None:
        difference = tax_difference(year, self._total_paid())
        if difference is None:
            self._difference_var.set("Sin datos")
        else:
            self._difference_var.set(_format_money(difference))

    def _total_paid(self) -> float:
        return sum(entry[1] for entry in self._payment_history)

    def _register_payment(self) -> None:
        month = self._payment_month_var.get()
        try:
            amount = float(self._payment_amount_var.get())
        except ValueError:
            messagebox.showerror("Impuestos", "Ingresa un monto válido para el impuesto pagado.")
            return
        self._payment_amount_var.set("")
        self._payment_history.append((month, amount, datetime.now()))
        self._update_paid_display()
        self._update_difference(int(self._year_var.get()))
        self._render_payment_history()
        messagebox.showinfo("Impuestos", f"Pago registrado para {month}: {_format_money(amount)}")

    def _render_payment_history(self) -> None:
        for child in self._payments_tree.get_children():
            self._payments_tree.delete(child)
        if not self._payment_history:
            self._payments_tree.insert("", "end", values=("Sin registros", "", ""))
            return
        for month, amount, recorded_at in self._payment_history:
            timestamp = recorded_at.strftime("%d/%m %H:%M")
            self._payments_tree.insert(
                "",
                "end",
                values=(month, _format_money(amount), timestamp),
            )

    def _save_summary(self) -> None:
        try:
            year = int(self._year_var.get())
        except ValueError:
            messagebox.showerror("Impuestos", "Selecciona un año válido para guardar el resumen.")
            return
        summary = annual_tax_summary(year)
        paid_total = self._total_paid()
        calculated_tax = summary.get("calculated_tax") or 0.0
        diferencia = calculated_tax - paid_total
        # Guardar el resumen anual usando el año como clave única para evitar duplicados.
        impuesto = ImpuestoAnual(
            anio=year,
            ingreso_total=summary.get("income_total"),
            gastos_deducibles=summary.get("deductible_expenses"),
            base_imponible=summary.get("base_imponible"),
            impuesto_calculado=calculated_tax,
            impuesto_pagado=paid_total,
            diferencia=diferencia,
        )
        try:
            self._impuesto_repo.upsert_summary(impuesto)
        except Exception as exc:
            messagebox.showerror("Impuestos", f"No se pudo guardar el resumen: {exc}")
            return
        self._difference_var.set(_format_money(diferencia))
        messagebox.showinfo("Impuestos", f"Resumen del {year} guardado correctamente.")

"""Panel dedicado al registro sencillo de impuestos anuales."""

from __future__ import annotations

from datetime import datetime

import tkinter as tk
from tkinter import ttk, messagebox

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from ..db.connection import DatabaseConnection
from ..logic.graficos import annual_tax_paid_figure
from ..repositories import ImpuestoAnualRepository


def _format_money(value: float | None) -> str:
    if value is None:
        return "Sin datos"
    return f"${value:,.2f}"


class ImpuestosFrame(tk.Frame):
    """Componente principal que expone los controles que pidió el usuario."""

    def __init__(self, parent: tk.Misc) -> None:
        super().__init__(parent, padx=12, pady=12)
        self._db_connection = DatabaseConnection()
        self._impuesto_repo = ImpuestoAnualRepository(self._db_connection)
        self._year_var = tk.StringVar(value=str(self._current_year()))
        self._amount_var = tk.StringVar()
        self._chart_container: ttk.Frame | None = None
        self._chart_canvas: FigureCanvasTkAgg | None = None

        tk.Label(self, text="IMPUESTOS", font=(None, 14, "bold")).pack(anchor="w")
        self._build_message_section()
        self._build_tax_entry_section()
        self._build_records_section()
        self._build_chart_section()

        self._refresh_records()
        self._refresh_tax_chart()

    def _current_year(self) -> int:
        return datetime.now().year

    def _build_message_section(self) -> None:
        section = ttk.LabelFrame(self, text="Disclaimer", padding=8)
        section.pack(fill="x", pady=(0, 12))
        tk.Label(section, text="Este panel permite registrar y visualizar impuestos anuales. Estos valores seran utilizados como descuento final en la tabla de gastos.").pack(anchor="w")


    def _build_tax_entry_section(self) -> None:
        section = ttk.LabelFrame(self, text="Registrar impuesto anual", padding=8)
        section.pack(fill="x", pady=(0, 12))
        tk.Label(section, text="Año").grid(row=0, column=0, sticky="w")
        tk.Label(section, text="Impuesto pagado").grid(row=0, column=1, sticky="w", padx=(12, 0))
        tk.Entry(section, textvariable=self._year_var, width=12).grid(row=1, column=0, pady=(4, 0))
        tk.Entry(section, textvariable=self._amount_var, width=18).grid(row=1, column=1, padx=(12, 0), pady=(4, 0))
        ttk.Button(section, text="Guardar", command=self._save_tax_entry).grid(row=1, column=2, padx=(12, 0))

    def _build_records_section(self) -> None:
        section = ttk.LabelFrame(self, text="Pagos registrados", padding=8)
        section.pack(fill="x", pady=(0, 12))
        columns = ("anio", "pagado")
        self._records_tree = ttk.Treeview(section, columns=columns, show="headings", height=6)
        self._records_tree.heading("anio", text="Año")
        self._records_tree.heading("pagado", text="Impuesto pagado")
        self._records_tree.column("anio", width=100, anchor="center")
        self._records_tree.column("pagado", anchor="center")
        self._records_tree.pack(side="left", fill="x", expand=True)
        scrollbar = ttk.Scrollbar(section, orient="vertical", command=self._records_tree.yview)
        scrollbar.pack(side="right", fill="y")
        self._records_tree.configure(yscrollcommand=scrollbar.set)

    def _build_chart_section(self) -> None:
        section = ttk.LabelFrame(self, text="Gráfico de impuestos", padding=8)
        section.pack(fill="both", expand=True)
        self._chart_container = ttk.Frame(section)
        self._chart_container.pack(fill="both", expand=True)
        self._chart_container.bind("<Configure>", lambda _: self._refresh_tax_chart())

    def _show_user_message(self) -> None:
        message = self._message_var.get().strip() or "Sin mensaje"
        messagebox.showinfo("Mensaje al usuario", message)

    def _save_tax_entry(self) -> None:
        try:
            year = int(self._year_var.get())
        except ValueError:
            messagebox.showerror("Impuestos", "Proporciona un año válido.")
            return
        try:
            amount = float(self._amount_var.get())
        except ValueError:
            messagebox.showerror("Impuestos", "Ingresa un monto numérico para el impuesto pagado.")
            return
        try:
            self._impuesto_repo.save_paid_tax(year, amount)
        except Exception as exc:
            messagebox.showerror("Impuestos", f"No se pudo guardar el registro: {exc}")
            return
        self._amount_var.set("")
        self._refresh_records()
        self._refresh_tax_chart()
        messagebox.showinfo("Impuestos", f"Impuesto del {year} guardado correctamente.")

    def _refresh_records(self) -> None:
        rows = self._impuesto_repo.list_tax_payments()
        for child in self._records_tree.get_children():
            self._records_tree.delete(child)
        if not rows:
            self._records_tree.insert("", "end", values=("Sin datos", ""))
            return
        for row in rows:
            year = row.get("anio")
            paid = row.get("impuesto_pagado")
            self._records_tree.insert("", "end", values=(year or "-", _format_money(paid)))

    def _refresh_tax_chart(self) -> None:
        if self._chart_container is None:
            return
        figure = annual_tax_paid_figure()
        self._chart_canvas = self._render_figure_on_container(self._chart_container, figure, self._chart_canvas)

    def _render_figure_on_container(
        self,
        container: tk.Misc,
        figure,
        existing: FigureCanvasTkAgg | None,
    ) -> FigureCanvasTkAgg:
        if existing:
            existing.get_tk_widget().destroy()
        canvas = FigureCanvasTkAgg(figure, master=container)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        return canvas

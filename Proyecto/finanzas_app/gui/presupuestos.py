from __future__ import annotations

from datetime import datetime
from typing import Any

import tkinter as tk
from tkinter import messagebox, ttk

from ..db.connection import DatabaseConnection
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from ..logic.graficos import budget_pie_figure, objective_comparison_figure
from ..models import Categoria, PresupuestoEspecifico
from ..repositories import CategoriaRepository, PresupuestoEspecificoRepository


class PresupuestosFrame(tk.Frame):
    """Gestor de objetivos de gasto por categoría y sus comparativas."""

    def __init__(self, parent: tk.Misc) -> None:
        super().__init__(parent, padx=24, pady=24)
        self._db_connection = DatabaseConnection()
        self._categoria_repo = CategoriaRepository(self._db_connection)
        self._presupuesto_especifico_repo = PresupuestoEspecificoRepository(self._db_connection)
        self._expense_categories = self._load_expense_categories()
        self._category_lookup = {
            f"{cat.id_categoria} - {cat.nombre}": cat.id_categoria for cat in self._expense_categories
        }

        now = datetime.now()
        self._objective_category_var = tk.StringVar()
        self._objective_year_var = tk.StringVar(value=str(now.year))
        self._objective_month_var = tk.StringVar(value=str(now.month))
        self._objective_amount_var = tk.StringVar()

        self._chart_year_var = tk.StringVar(value=str(now.year))
        self._chart_month_var = tk.StringVar(value=str(now.month))

        self._comparacion_canvas: FigureCanvasTkAgg | None = None
        self._pie_chart_canvas: FigureCanvasTkAgg | None = None
        self._comparacion_container: tk.Frame | None = None
        self._pie_container: tk.Frame | None = None
        self._objectives_tree: ttk.Treeview | None = None
        self._objectives_data: list[dict[str, Any]] = []
        self._delete_btn: tk.Button | None = None

        self._build_ui()

    def _load_expense_categories(self) -> list[Categoria]:
        categories = self._categoria_repo.list_all()
        return [cat for cat in categories if cat.tipo == "gasto"]

    def _build_ui(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        container = tk.Frame(self)
        container.pack(fill="both", expand=True)

        self._build_objective_section(container).grid(row=0, column=0, sticky="ew", pady=8)
        self._build_charts_section(container).grid(row=1, column=0, sticky="nsew", pady=8)

    def _build_objective_section(self, parent: tk.Frame) -> ttk.LabelFrame:
        labelframe = ttk.LabelFrame(parent, text="Objetivos de gasto por categoría", padding=12)
        combo = ttk.Combobox(labelframe, textvariable=self._objective_category_var, state="readonly")
        combo["values"] = list(self._category_lookup.keys())
        if combo["values"]:
            combo.current(0)
        self._build_row(labelframe, "Categoría", combo)
        self._build_row(labelframe, "Año", tk.Entry(labelframe, textvariable=self._objective_year_var))
        self._build_row(labelframe, "Mes", self._make_month_combo(labelframe, self._objective_month_var))
        self._build_row(labelframe, "Monto", tk.Entry(labelframe, textvariable=self._objective_amount_var))
        tk.Button(labelframe, text="Guardar objetivo", command=self._save_objective).grid(
            row=4, column=0, columnspan=2, pady=(8, 0)
        )
        return labelframe

    def _build_row(self, parent: tk.Frame, label: str, widget: tk.Widget) -> None:
        row = parent.grid_size()[1]
        tk.Label(parent, text=f"{label}:").grid(row=row, column=0, sticky="e", padx=(0, 6), pady=4)
        widget.grid(row=row, column=1, sticky="ew", pady=4)
        parent.columnconfigure(1, weight=1)

    def _build_charts_section(self, parent: tk.Frame) -> ttk.LabelFrame:
        labelframe = ttk.LabelFrame(parent, text="Objetivos por periodo", padding=12)
        selectors = tk.Frame(labelframe)
        selectors.pack(fill="x", pady=(0, 8))

        tk.Label(selectors, text="Año:").pack(side="left", padx=(0, 4))
        tk.Entry(selectors, textvariable=self._chart_year_var, width=6).pack(side="left")
        tk.Label(selectors, text="Mes:").pack(side="left", padx=(8, 4))
        self._make_month_combo(selectors, self._chart_month_var).pack(side="left")
        tk.Button(selectors, text="Actualizar", command=self._refresh_period_views).pack(side="right")

        list_frame = ttk.LabelFrame(labelframe, text="Objetivos del periodo", padding=(6, 6))
        list_frame.pack(fill="both", expand=True, pady=(0, 8))
        columns = ("categoria", "monto")
        self._objectives_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=5, selectmode="browse")
        for col, heading in zip(columns, ("Categoría", "Monto")):
            self._objectives_tree.heading(col, text=heading)
            self._objectives_tree.column(col, anchor="w", width=170)
        tree_scroll = ttk.Scrollbar(list_frame, orient="vertical", command=self._objectives_tree.yview)
        self._objectives_tree.configure(yscrollcommand=tree_scroll.set)
        self._objectives_tree.pack(side="left", fill="both", expand=True)
        tree_scroll.pack(side="right", fill="y")
        self._objectives_tree.bind("<<TreeviewSelect>>", self._on_objective_select)

        btn_frame = tk.Frame(labelframe)
        btn_frame.pack(fill="x", pady=(4, 8))
        self._delete_btn = tk.Button(btn_frame, text="Eliminar objetivo seleccionado", state="disabled", command=self._delete_selected_objective)
        self._delete_btn.pack(side="left")

        charts_container = tk.Frame(labelframe)
        charts_container.pack(fill="both", expand=True)
        charts_container.columnconfigure(0, weight=1)
        charts_container.columnconfigure(1, weight=1)

        pie_frame = tk.Frame(charts_container)
        pie_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        comparison_frame = tk.Frame(charts_container)
        comparison_frame.grid(row=0, column=1, sticky="nsew", padx=(8, 0))

        self._pie_container = tk.Frame(pie_frame)
        self._pie_container.pack(fill="both", expand=True)
        self._comparacion_container = tk.Frame(comparison_frame)
        self._comparacion_container.pack(fill="both", expand=True)

        self._pie_container.bind("<Configure>", lambda _: self._refresh_charts())
        self._comparacion_container.bind("<Configure>", lambda _: self._refresh_charts())

        self._refresh_period_views()
        return labelframe

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

    def _save_objective(self) -> None:
        try:
            category_key = self._objective_category_var.get()
            categoria_id = self._category_lookup.get(category_key)
            if not categoria_id:
                raise ValueError("Selecciona una categoría de gasto válida.")
            year = self._parse_int(self._objective_year_var.get().strip(), "Año")
            month = self._parse_int(self._objective_month_var.get().strip(), "Mes")
            amount = self._parse_float(self._objective_amount_var.get().strip(), "Monto")
            presupuesto = PresupuestoEspecifico(
                anio=year, mes=month, monto=amount, categoria_id=categoria_id
            )
            self._presupuesto_especifico_repo.create(presupuesto)
            messagebox.showinfo("Presupuesto específico", "Presupuesto específico guardado correctamente.")
            self._objective_amount_var.set("")
            self._refresh_period_views()
        except Exception as exc:
            messagebox.showerror("Presupuesto específico", str(exc))

    def _chart_period(self) -> tuple[int, int]:
        now = datetime.now()
        try:
            year = int(self._chart_year_var.get())
        except ValueError:
            year = now.year
        try:
            month = int(self._chart_month_var.get())
        except ValueError:
            month = now.month
        return year, month

    def _refresh_period_views(self) -> None:
        self._refresh_objective_list()
        self._refresh_charts()

    def _refresh_objective_list(self) -> None:
        if not self._objectives_tree:
            return
        year, month = self._chart_period()
        self._objectives_data = self._presupuesto_especifico_repo.list_by_month(year, month)
        for child in self._objectives_tree.get_children():
            self._objectives_tree.delete(child)
        for row in self._objectives_data:
            monto = float(row.get("monto") or 0.0)
            self._objectives_tree.insert(
                "",
                "end",
                iid=str(row.get("id_presupuesto")),
                values=(row.get("nombre") or "Sin categoría", f"${monto:,.2f}"),
            )
        self._clear_objective_selection()

    def _on_objective_select(self, event: tk.Event) -> None:
        if not self._objectives_tree or not event.widget:
            return
        selection = self._objectives_tree.selection()
        if selection and self._delete_btn:
            self._delete_btn.config(state="normal")
        elif self._delete_btn:
            self._delete_btn.config(state="disabled")

    def _clear_objective_selection(self) -> None:
        if self._objectives_tree:
            for sel in self._objectives_tree.selection():
                self._objectives_tree.selection_remove(sel)
        if self._delete_btn:
            self._delete_btn.config(state="disabled")

    def _delete_selected_objective(self) -> None:
        if not self._objectives_tree:
            return
        selection = self._objectives_tree.selection()
        if not selection:
            return
        objetivo_id = int(selection[0])
        confirm = messagebox.askyesno(
            "Eliminar objetivo",
            "¿Estás seguro de eliminar este objetivo?",
        )
        if not confirm:
            return
        try:
            self._presupuesto_especifico_repo.delete(objetivo_id)
        except Exception as exc:
            messagebox.showerror("Eliminar objetivo", str(exc))
            return
        self._refresh_period_views()

    def _refresh_charts(self) -> None:
        period_year, period_month = self._chart_period()
        if self._pie_container:
            figure = budget_pie_figure(period_year, period_month)
            self._pie_chart_canvas = self._render_figure_on_container(
                self._pie_container, figure, self._pie_chart_canvas
            )
        if self._comparacion_container:
            figure = objective_comparison_figure(period_year, period_month)
            self._comparacion_canvas = self._render_figure_on_container(
                self._comparacion_container, figure, self._comparacion_canvas
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
        # Mantiene referencia para poder refrescar/reemplazar el lienzo fácilmente.
        return canvas

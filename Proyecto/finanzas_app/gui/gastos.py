"""Panel para visualizar gastos fijos, variables y por categoría."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Callable, Optional

import tkinter as tk
from tkinter import ttk, messagebox

from ..db.connection import DatabaseConnection
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from ..logic.graficos import (
    fixed_category_stacked_figure,
    variable_annual_trend_figure,
    variable_month_pie_figure,
)
from ..repositories import CategoriaRepository, FinancialReportRepository, TransaccionRepository
from .theme import Theme


def _format_money(value: float | None) -> str:
    if value is None:
        return "Sin datos"
    return f"${value:,.2f}"


def _make_tree(frame: tk.Frame, title: str, columns: tuple[str, ...]) -> ttk.Treeview:
    # Agrupamos cada tabla en una tarjeta temática para visibilidad.
    labelframe = tk.LabelFrame(frame, text=title, padx=12, pady=12, bg=Theme.CARD_BG, fg=Theme.PRIMARY_TEXT)
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
        super().__init__(parent, padx=12, pady=12, bg=Theme.BACKGROUND)
        # La vista completa se dibuja dentro de un canvas desplazable para poder navegar el panel.
        self._canvas = tk.Canvas(self, borderwidth=0, highlightthickness=0, bg=Theme.BACKGROUND)
        self._scrollbar = ttk.Scrollbar(self, orient="vertical", command=self._canvas.yview)
        self._canvas.configure(yscrollcommand=self._scrollbar.set)
        self._canvas.pack(side="left", fill="both", expand=True)
        self._scrollbar.pack(side="right", fill="y")

        self._content_frame = ttk.Frame(self._canvas)
        self._canvas_window = self._canvas.create_window((0, 0), window=self._content_frame, anchor="nw")
        self._content_frame.bind("<Configure>", lambda e: self._canvas.configure(scrollregion=self._canvas.bbox("all")))
        self._canvas.bind("<Configure>", lambda e: self._canvas.itemconfig(self._canvas_window, width=e.width))
        self._content_frame.bind("<Enter>", lambda _: self._canvas.bind("<MouseWheel>", self._on_mousewheel))
        self._content_frame.bind("<Leave>", lambda _: self._canvas.unbind("<MouseWheel>"))
        self._db_connection = DatabaseConnection()
        self._report_repo = FinancialReportRepository(self._db_connection)
        self._categoria_repo = CategoriaRepository(self._db_connection)
        self._trans_repo = TransaccionRepository(self._db_connection)
        self._fixed_month_var = tk.StringVar(value="1")
        self._variable_month_var = tk.StringVar(value="1")
        self._category_var = tk.StringVar()
        self._global_year_var = tk.StringVar(value=str(self._current_year()))
        categories = self._categoria_repo.list_by_tipo("gasto")
        # Cacheamos nombre->id para usar en el filtro historicado.
        self._category_catalog = {cat.nombre: cat.id_categoria for cat in categories}
        self._category_var.set("Todas")

        self._fixed_chart_container: tk.Frame | None = None
        self._fixed_chart_canvas: FigureCanvasTkAgg | None = None
        self._variable_month_chart_container: tk.Frame | None = None
        self._variable_month_chart_canvas: FigureCanvasTkAgg | None = None
        self._variable_year_chart_container: tk.Frame | None = None
        self._variable_year_chart_canvas: FigureCanvasTkAgg | None = None

        # El fondo del canvas se mantiene coherente con el tema principal.
        # Encabezado contextual para explicar el propósito de este panel.
        tk.Label(
            self._content_frame,
            text="Gastos",
            font=(None, 16, "bold"),
            bg=Theme.BACKGROUND,
            fg=Theme.PRIMARY_TEXT,
        ).pack(anchor="w")
        tk.Label(
            self._content_frame,
            text="Revisa tus gastos fijos, variables y el histórico por categoría para identificar ajustes y estabilizar tu presupuesto.",
            wraplength=520,
            bg=Theme.BACKGROUND,
            fg=Theme.SECONDARY_TEXT,
        ).pack(anchor="w", pady=(0, 12))
        control_frame = tk.Frame(self._content_frame, bg=Theme.BACKGROUND)
        control_frame.pack(fill="x", pady=(0, 12))
        self._build_year_selector(control_frame)
        controls_frame = tk.Frame(control_frame, bg=Theme.BACKGROUND)
        controls_frame.pack(side="left", fill="x", expand=True, pady=(6, 0))
        self._build_controls(controls_frame, "Fijos", self._fixed_month_var, self._refresh_fixed)
        self._build_controls(controls_frame, "Variables", self._variable_month_var, self._refresh_variable)
        self._build_category_controls(controls_frame)

        body_frame = tk.Frame(self._content_frame, bg=Theme.BACKGROUND)
        body_frame.pack(fill="both", expand=True)
        body_frame.columnconfigure(0, weight=1)
        body_frame.columnconfigure(1, weight=2)

        list_frame = tk.Frame(body_frame, bg=Theme.BACKGROUND)
        list_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        charts_frame = tk.Frame(body_frame, bg=Theme.BACKGROUND)
        charts_frame.grid(row=0, column=1, sticky="nsew", padx=(6, 0))

        self._fixed_tree = _make_tree(list_frame, "Gastos fijos mensuales", ("Categoría", "Total"))
        self._variable_tree = _make_tree(list_frame, "Gastos variables mensuales", ("Categoría", "Total"))
        self._category_tree = _make_tree(list_frame, "Historial por categoría", ("Fecha", "Total", "Cantidad"))

        self._build_graphs_section(charts_frame)

        self._refresh_fixed()
        self._refresh_variable()
        self._refresh_category_history()
        self._refresh_fixed_chart()
        self._refresh_variable_month_chart()
        self._refresh_variable_year_chart()

    def _current_year(self) -> int:
        return datetime.now().year

    def _on_mousewheel(self, event: tk.Event) -> None:
        # Scroll the canvas by units of mouse wheel delta for smoother navigation.
        delta = int(-1 * (event.delta / 120)) if event.delta else 0
        self._canvas.yview_scroll(delta, "units")

    def _build_controls(
        self,
        parent: tk.Frame,
        title: str,
        month_var: tk.StringVar,
        callback: Callable[[], None],
        month_enabled: bool = True,
    ) -> None:
        frame = tk.LabelFrame(
            parent,
            text=title,
            padx=8,
            pady=6,
            bg=Theme.CARD_BG,
            fg=Theme.PRIMARY_TEXT,
        )
        frame.pack(side="left", padx=6, fill="x", expand=True)
        if month_enabled:
            tk.Label(frame, text="Mes", bg=Theme.CARD_BG, fg=Theme.PRIMARY_TEXT).grid(row=0, column=0, sticky="w")
            combo = ttk.Combobox(frame, textvariable=month_var, state="readonly", width=5)
            combo["values"] = [str(i) for i in range(1, 13)]
            combo.grid(row=1, column=0, padx=(0, 8))
        tk.Button(
            frame,
            text="Actualizar",
            command=callback,
            bg=Theme.ACTION_COLOR,
            fg="white",
            activebackground=Theme.ACTION_HOVER,
        ).grid(row=1, column=2)

    def _make_month_combo(self, parent: tk.Misc, var: tk.StringVar) -> ttk.Combobox:
        combo = ttk.Combobox(parent, textvariable=var, state="readonly", width=5)
        combo["values"] = [str(i) for i in range(1, 13)]
        combo.current(int(var.get()) - 1)
        return combo

    def _refresh_fixed(self) -> None:
        try:
            month = int(self._fixed_month_var.get())
        except ValueError:
            messagebox.showerror("Gastos fijos", "Mes debe ser numérico.")
            return
        year = self._parse_year_from_var(self._global_year_var, "Año compartido (gastos fijos)")
        if year is None:
            return
        rows = self._report_repo.monthly_fixed_expenses(year=year, month=month)
        self._populate_tree(self._fixed_tree, rows)

    def _refresh_variable(self) -> None:
        try:
            month = int(self._variable_month_var.get())
        except ValueError:
            messagebox.showerror("Gastos variables", "Mes debe ser numérico.")
            return
        year = self._parse_year_from_var(self._global_year_var, "Año compartido (gastos variables)")
        if year is None:
            return
        rows = self._report_repo.variable_expenses(year=year, month=month)
        self._populate_tree(self._variable_tree, rows)
        self._refresh_variable_month_chart()

    def _build_category_controls(self, parent: tk.Frame) -> None:
        frame = tk.LabelFrame(
            parent,
            text="Por categoría",
            padx=8,
            pady=6,
            bg=Theme.CARD_BG,
            fg=Theme.PRIMARY_TEXT,
        )
        frame.pack(side="left", padx=6, fill="x", expand=True)
        tk.Label(frame, text="Categoría", bg=Theme.CARD_BG, fg=Theme.PRIMARY_TEXT).grid(row=0, column=0, sticky="w")
        combo = ttk.Combobox(frame, textvariable=self._category_var, state="readonly")
        category_values = ["Todas"] + sorted(self._category_catalog.keys())
        combo["values"] = category_values or ["Sin categorías"]
        combo.set(self._category_var.get())
        combo.grid(row=1, column=0, padx=(0, 8))
        tk.Button(
            frame,
            text="Actualizar",
            command=self._refresh_category_history,
            bg=Theme.ACTION_COLOR,
            fg="white",
            activebackground=Theme.ACTION_HOVER,
        ).grid(row=1, column=2)
        # No tiene mes/año porque muestra el histórico completo de la categoría.

    def _build_year_selector(self, parent: tk.Frame) -> None:
        frame = tk.LabelFrame(
            parent,
            text="Año compartido",
            padx=8,
            pady=6,
            bg=Theme.CARD_BG,
            fg=Theme.PRIMARY_TEXT,
        )
        frame.pack(side="left", padx=6)
        tk.Label(frame, text="Año", bg=Theme.CARD_BG, fg=Theme.PRIMARY_TEXT).grid(row=0, column=0, sticky="w")
        tk.Entry(
            frame,
            textvariable=self._global_year_var,
            width=6,
            bg=Theme.BACKGROUND,
            fg=Theme.PRIMARY_TEXT,
        ).grid(row=1, column=0, padx=(0, 8))
        tk.Button(
            frame,
            text="Aplicar",
            command=self._refresh_all_views,
            bg=Theme.ACTION_COLOR,
            fg="white",
            activebackground=Theme.ACTION_HOVER,
        ).grid(row=1, column=1)

    def _build_graphs_section(self, parent: tk.Frame) -> None:
        section = tk.LabelFrame(
            parent,
            text="Gráficos de gastos",
            padx=12,
            pady=12,
            bg=Theme.CARD_BG,
            fg=Theme.PRIMARY_TEXT,
        )
        section.pack(fill="both", expand=True, pady=6)

        fixed_frame = tk.LabelFrame(
            section,
            text="Fijos por categoría",
            padx=8,
            pady=8,
            bg=Theme.CARD_BG,
            fg=Theme.PRIMARY_TEXT,
        )
        fixed_frame.pack(fill="x", pady=(0, 8))
        tk.Label(
            fixed_frame,
            text="Año compartido",
            bg=Theme.CARD_BG,
            fg=Theme.PRIMARY_TEXT,
        ).pack(side="left")
        tk.Button(
            fixed_frame,
            text="Actualizar",
            command=self._refresh_fixed_chart,
            bg=Theme.ACTION_COLOR,
            fg="white",
            activebackground=Theme.ACTION_HOVER,
        ).pack(side="left")
        self._fixed_chart_container = tk.Frame(section, bg=Theme.CARD_BG)
        self._fixed_chart_container.pack(fill="both", expand=True, pady=(0, 8))
        self._fixed_chart_container.bind("<Configure>", lambda _: self._refresh_fixed_chart())

        variable_pie_frame = tk.LabelFrame(
            section,
            text="Variables mensuales",
            padx=8,
            pady=8,
            bg=Theme.CARD_BG,
            fg=Theme.PRIMARY_TEXT,
        )
        variable_pie_frame.pack(fill="x", pady=(0, 8))
        self._variable_month_chart_container = tk.Frame(section, bg=Theme.CARD_BG)
        self._variable_month_chart_container.pack(fill="both", expand=True, pady=(0, 8))
        self._variable_month_chart_container.bind("<Configure>", lambda _: self._refresh_variable_month_chart())

        variable_year_frame = tk.LabelFrame(
            section,
            text="Variables anuales",
            padx=8,
            pady=8,
            bg=Theme.CARD_BG,
            fg=Theme.PRIMARY_TEXT,
        )
        variable_year_frame.pack(fill="x", pady=(0, 8))
        tk.Label(
            variable_year_frame,
            text="Año compartido",
            bg=Theme.CARD_BG,
            fg=Theme.PRIMARY_TEXT,
        ).pack(side="left")
        tk.Button(
            variable_year_frame,
            text="Actualizar",
            command=self._refresh_variable_year_chart,
            bg=Theme.ACTION_COLOR,
            fg="white",
            activebackground=Theme.ACTION_HOVER,
        ).pack(side="left")
        self._variable_year_chart_container = tk.Frame(section, bg=Theme.CARD_BG)
        self._variable_year_chart_container.pack(fill="both", expand=True)
        self._variable_year_chart_container.bind("<Configure>", lambda _: self._refresh_variable_year_chart())

    def _refresh_category_history(self) -> None:
        selected = self._category_var.get()
        year = self._parse_year_from_var(self._global_year_var, "Año compartido (historial)")
        if year is None:
            return
        if selected == "Todas":
            rows = self._trans_repo.list_variable_transactions(year)
        else:
            category_id = self._category_catalog.get(selected)
            if category_id is None:
                messagebox.showwarning("Historial por categoría", "Selecciona una categoría válida.")
                self._populate_history([])
                return
            rows = self._trans_repo.list_by_categoria(category_id, year=year)
        self._populate_history(rows)
        self._refresh_variable_year_chart()

    def _parse_year_from_var(self, var: tk.StringVar, label: str) -> Optional[int]:
        try:
            return int(var.get())
        except ValueError:
            messagebox.showerror("Entrada inválida", f"{label} debe ser un número entero.")
            return None

    def _parse_month_from_var(self, var: tk.StringVar) -> Optional[int]:
        try:
            month = int(var.get())
            if 1 <= month <= 12:
                return month
        except ValueError:  # fallthrough to error
            pass
        messagebox.showerror("Entrada inválida", "Selecciona un mes entre 1 y 12.")
        return None

    def _refresh_fixed_chart(self) -> None:
        year = self._parse_year_from_var(self._global_year_var, "Año compartido (gráfico fijos)")
        if year is None or self._fixed_chart_container is None:
            return
        figure = fixed_category_stacked_figure(year)
        self._fixed_chart_canvas = self._render_figure_on_container(
            self._fixed_chart_container, figure, self._fixed_chart_canvas
        )

    def _refresh_variable_month_chart(self) -> None:
        year = self._parse_year_from_var(self._global_year_var, "Año compartido (gráfico variables mensuales)")
        month = self._parse_month_from_var(self._variable_month_var)
        if year is None or month is None or self._variable_month_chart_container is None:
            return
        figure = variable_month_pie_figure(year, month)
        self._variable_month_chart_canvas = self._render_figure_on_container(
            self._variable_month_chart_container, figure, self._variable_month_chart_canvas
        )

    def _refresh_variable_year_chart(self) -> None:
        year = self._parse_year_from_var(self._global_year_var, "Año compartido (gráfico variables anuales)")
        if year is None or self._variable_year_chart_container is None:
            return
        category_id, label = self._selected_category_filter()
        figure = variable_annual_trend_figure(year, category_id=category_id, category_label=label)
        self._variable_year_chart_canvas = self._render_figure_on_container(
            self._variable_year_chart_container, figure, self._variable_year_chart_canvas
        )

    def _selected_category_filter(self) -> tuple[Optional[int], str]:
        selected = self._category_var.get()
        if selected == "Todas":
            return None, "Todas"
        return self._category_catalog.get(selected), selected

    def _refresh_all_views(self) -> None:
        self._refresh_fixed()
        self._refresh_variable()
        self._refresh_category_history()
        self._refresh_fixed_chart()
        self._refresh_variable_month_chart()
        self._refresh_variable_year_chart()

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

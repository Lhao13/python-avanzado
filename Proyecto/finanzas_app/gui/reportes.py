"""Panel para generar reportes financieros en PDF."""

from __future__ import annotations

from calendar import month_name
from datetime import datetime
from typing import Callable, List, Tuple

import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.figure import Figure
from matplotlib import pyplot as plt

from ..db.connection import DatabaseConnection
from ..logic.graficos import (
    annual_cumulative_savings_figure,
    annual_expense_boxplot_figure,
    annual_expense_by_category_stacked_figure,
    annual_expense_line_figure,
    monthly_daily_expense_line_figure,
    monthly_expense_heatmap_figure,
    monthly_income_vs_expense_stacked_figure,
    monthly_spending_bar_figure,
    monthly_spending_pie_figure,
)
from ..repositories import FinancialReportRepository
from .theme import Theme


def _format_money(value: float | None) -> str:
    if value is None:
        return "Sin datos"
    return f"${value:,.2f}"


def _today_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M")


class ReportesFrame(tk.Frame):
    """Sección dedicada a exportar reportes mensuales y anuales."""

    def __init__(self, parent: tk.Misc) -> None:
        super().__init__(parent, padx=12, pady=12, bg=Theme.BACKGROUND)
        self._repo = FinancialReportRepository(DatabaseConnection())
        self._monthly_year_var = tk.StringVar()
        self._monthly_month_var = tk.StringVar(value=month_name[datetime.now().month])
        self._annual_year_var = tk.StringVar()

        tk.Label(
            self,
            text="REPORTES",
            font=(None, 14, "bold"),
            bg=Theme.BACKGROUND,
            fg=Theme.PRIMARY_TEXT,
        ).pack(anchor="w")
        self._build_monthly_section()
        self._build_annual_section()
        self._refresh_available_years()

    def _build_monthly_section(self) -> None:
        section = tk.LabelFrame(
            self,
            text="Reporte mensual",
            padx=8,
            pady=8,
            bg=Theme.CARD_BG,
            fg=Theme.PRIMARY_TEXT,
        )
        section.pack(fill="x", pady=(8, 4))

        tk.Label(
            section,
            text="Exporta un PDF con indicadores, listas y gráficos del mes seleccionado.",
            bg=Theme.CARD_BG,
            fg=Theme.SECONDARY_TEXT,
        ).grid(row=0, column=0, columnspan=3, sticky="w")

        tk.Label(section, text="Año", bg=Theme.CARD_BG, fg=Theme.PRIMARY_TEXT)\
            .grid(row=1, column=0, sticky="w", pady=(6, 0))
        self._monthly_year_combo = ttk.Combobox(section, textvariable=self._monthly_year_var,
                                               state="readonly", width=10)
        self._monthly_year_combo.grid(row=1, column=1, pady=(6, 0))

        tk.Label(section, text="Mes", bg=Theme.CARD_BG, fg=Theme.PRIMARY_TEXT)\
            .grid(row=2, column=0, sticky="w")
        month_combo = ttk.Combobox(section, textvariable=self._monthly_month_var, state="readonly")
        month_combo["values"] = [month_name[i] for i in range(1, 13)]
        month_combo.grid(row=2, column=1, pady=(0, 4))

        tk.Button(
            section,
            text="Generar reporte mensual",
            command=self._generate_monthly_report,
            bg=Theme.ACTION_COLOR,
            fg="white",
            activebackground=Theme.ACTION_HOVER,
        ).grid(row=3, column=0, columnspan=2, pady=(8, 0))

    def _build_annual_section(self) -> None:
        section = tk.LabelFrame(
            self,
            text="Reporte anual",
            padx=8,
            pady=8,
            bg=Theme.CARD_BG,
            fg=Theme.PRIMARY_TEXT,
        )
        section.pack(fill="x", pady=(4, 12))

        tk.Label(
            section,
            text="Crea un archivo PDF con los indicadores globales y los gráficos del año elegido.",
            bg=Theme.CARD_BG,
            fg=Theme.SECONDARY_TEXT,
        ).grid(row=0, column=0, columnspan=2, sticky="w")

        tk.Label(section, text="Año", bg=Theme.CARD_BG, fg=Theme.PRIMARY_TEXT)\
            .grid(row=1, column=0, sticky="w", pady=(6, 0))
        self._annual_year_combo = ttk.Combobox(section, textvariable=self._annual_year_var,
                                               state="readonly", width=10)
        self._annual_year_combo.grid(row=1, column=1, pady=(6, 0))

        tk.Button(
            section,
            text="Generar reporte anual",
            command=self._generate_annual_report,
            bg=Theme.ACTION_COLOR,
            fg="white",
            activebackground=Theme.ACTION_HOVER,
        ).grid(row=2, column=0, columnspan=2, pady=(8, 0))

    def _refresh_available_years(self) -> None:
        years = self._repo.get_available_years() or [datetime.now().year]
        values = [str(year) for year in sorted(set(years))]
        latest = values[-1]
        self._monthly_year_combo["values"] = values
        self._annual_year_combo["values"] = values
        self._monthly_year_var.set(latest)
        self._annual_year_var.set(latest)

    # ---------------------------------------------------------------------
    # ------------------------ GENERACIÓN DE PDF --------------------------
    # ---------------------------------------------------------------------

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

        filename = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF", "*.pdf")],
            title="Guardar reporte mensual",
            initialfile=f"reporte_mensual_{year}_{month}.pdf",
        )
        if not filename:
            return

        try:
            self._write_monthly_pdf(filename, year, month)
        except Exception as exc:
            messagebox.showerror("Reportes", f"No se pudo generar el reporte: {exc}")
            return

        messagebox.showinfo("Reportes", f"Reporte mensual guardado en {filename}.")

    def _generate_annual_report(self) -> None:
        try:
            year = int(self._annual_year_var.get())
        except ValueError:
            messagebox.showerror("Reportes", "Selecciona un año válido para el reporte anual.")
            return

        filename = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF", "*.pdf")],
            title="Guardar reporte anual",
            initialfile=f"reporte_anual_{year}.pdf",
        )
        if not filename:
            return

        try:
            self._write_annual_pdf(filename, year)
        except Exception as exc:
            messagebox.showerror("Reportes", f"No se pudo generar el reporte: {exc}")
            return

        messagebox.showinfo("Reportes", f"Reporte anual guardado en {filename}.")

    # ---------------------------------------------------------------------
    # -------------------------- PDF MENSUAL ------------------------------
    # ---------------------------------------------------------------------

    def _write_monthly_pdf(self, path: str, year: int, month: int) -> None:
        expenses_month = self._repo.total_expenses(year, month)
        incomes_month = self._repo.total_incomes(year, month)
        savings_month = incomes_month - expenses_month
        expenses_month_rows = self._repo.expenses_by_category(year, month)
        incomes_month_rows = self._repo.incomes_by_category_for_month(year, month)
        budgets_month_rows = self._repo.budget_by_category_for_month(year, month)

        with PdfPages(path) as pdf:
            # Portada combinada
            pdf.savefig(
                self._summary_with_table_figure(
                    f"Reporte mensual {month_name[month]} {year}",
                    [
                        f"Generado: {_today_str()}",
                        f"Gastos del mes: {_format_money(expenses_month)}",
                        f"Ingresos del mes: {_format_money(incomes_month)}",
                        f"Ahorro mensual: {_format_money(savings_month)}",
                    ],
                    "Gastos por categoría",
                    ["Categoría", "Total"],
                    self._table_rows_from_dicts(expenses_month_rows, ("categoria",), (_format_money,)),
                )
            )

            # Tablas adicionales
            pdf.savefig(
                self._table_figure(
                    "Ingresos por categoría",
                    ["Categoría", "Total"],
                    self._table_rows_from_dicts(incomes_month_rows, ("categoria",), (_format_money,)),
                )
            )

            pdf.savefig(
                self._table_figure(
                    "Presupuestos específicos",
                    ["Categoría", "Monto"],
                    self._table_rows_from_dicts(budgets_month_rows, ("nombre",), (_format_money,)),
                )
            )

            # Gráficos
            figures = [
                monthly_spending_bar_figure(year, month),
                monthly_spending_pie_figure(year, month),
                monthly_daily_expense_line_figure(year, month),
                monthly_income_vs_expense_stacked_figure(year, month),
                monthly_expense_heatmap_figure(year, month),
            ]
            for figure in figures:
                pdf.savefig(figure)
                plt.close(figure)

    # ---------------------------------------------------------------------
    # --------------------------- PDF ANUAL -------------------------------
    # ---------------------------------------------------------------------

    def _write_annual_pdf(self, path: str, year: int) -> None:
        expenses_year = self._repo.total_expenses(year)
        incomes_year = self._repo.total_incomes(year)
        savings_year = incomes_year - expenses_year
        expenses_year_rows = self._repo.expenses_by_category(year)
        incomes_year_rows = self._repo.incomes_by_category(year)
        budgets_year_rows = self._repo.get_budget_by_category(year)

        with PdfPages(path) as pdf:
            pdf.savefig(
                self._summary_with_table_figure(
                    f"Reporte anual {year}",
                    [
                        f"Generado: {_today_str()}",
                        f"Gasto total anual: {_format_money(expenses_year)}",
                        f"Ingreso total anual: {_format_money(incomes_year)}",
                        f"Ahorro anual: {_format_money(savings_year)}",
                    ],
                    "Gastos por categoría",
                    ["Categoría", "Total"],
                    self._table_rows_from_dicts(expenses_year_rows, ("categoria",), (_format_money,)),
                )
            )

            pdf.savefig(
                self._table_figure(
                    "Ingresos por categoría",
                    ["Categoría", "Total"],
                    self._table_rows_from_dicts(incomes_year_rows, ("categoria",), (_format_money,)),
                )
            )

            pdf.savefig(
                self._table_figure(
                    "Presupuestos anuales",
                    ["Mes", "Categoría", "Monto"],
                    [self._format_budget_row(row) for row in budgets_year_rows],
                )
            )

            figures = [
                annual_expense_line_figure(year),
                annual_expense_by_category_stacked_figure(year),
                annual_expense_boxplot_figure(year),
                annual_cumulative_savings_figure(year),
            ]
            for figure in figures:
                pdf.savefig(figure)
                plt.close(figure)

    # ---------------------------------------------------------------------
    # ------------------------- FIGURAS / TABLAS --------------------------
    # ---------------------------------------------------------------------

    def _summary_with_table_figure(
        self,
        title: str,
        summary_lines: List[str],
        table_title: str,
        headers: List[str],
        rows: List[Tuple[str, ...]],
        max_rows: int = 18,
    ) -> Figure:

        fig = Figure(figsize=(8.5, 11))
        fig.subplots_adjust(left=0.08, right=0.92, top=0.92, bottom=0.08)

        fig.suptitle(title, fontsize=16, fontweight="bold", y=0.97)

        grid = fig.add_gridspec(2, 1, height_ratios=(0.35, 1), hspace=0.25)

        # ----- Resumen -----
        summary_ax = fig.add_subplot(grid[0])
        summary_ax.axis("off")

        y = 0.9
        for line in summary_lines:
            summary_ax.text(0, y, f"• {line}", ha="left", fontsize=10)
            y -= 0.18

        # ----- Tabla -----
        table_ax = fig.add_subplot(grid[1])
        table_ax.axis("off")
        table_ax.set_title(table_title, pad=10, fontsize=12)

        display_rows = rows[:max_rows]
        if not display_rows:
            table_ax.text(0.5, 0.5, "Sin datos", ha="center", va="center", fontsize=11, color="#666")
            return fig

        table = table_ax.table(
            cellText=display_rows,
            colLabels=headers,
            colLoc="center",
            cellLoc="center",
            loc="center",
        )

        table.auto_set_font_size(False)
        table.set_fontsize(9)
        table.scale(1, 1.25)

        if len(rows) > max_rows:
            table_ax.text(0.5, -0.05, f"... y {len(rows) - max_rows} registros más",
                          ha="center", fontsize=8)

        return fig

    def _table_figure(self, title: str, headers: List[str], rows: List[Tuple[str, ...]], max_rows: int = 24) -> Figure:
        fig = Figure(figsize=(8.5, 11))
        fig.subplots_adjust(left=0.08, right=0.92, top=0.9, bottom=0.08)

        ax = fig.subplots()
        ax.axis("off")
        ax.set_title(title, pad=10, fontsize=12)

        display_rows = rows[:max_rows]
        if not display_rows:
            ax.text(0.5, 0.5, "Sin datos", ha="center", va="center", fontsize=11, color="#666")
            return fig

        table = ax.table(
            cellText=display_rows,
            colLabels=headers,
            colLoc="center",
            cellLoc="center",
            loc="center",
        )

        table.auto_set_font_size(False)
        table.set_fontsize(9)
        table.scale(1, 1.35)

        if len(rows) > max_rows:
            ax.text(0.5, 0.03, f"... y {len(rows) - max_rows} registros más",
                    ha="center", fontsize=8)

        return fig

    # ---------------------------------------------------------------------
    # -------------------------- HELPERS ---------------------------------
    # ---------------------------------------------------------------------

    def _table_rows_from_dicts(
        self,
        rows: List[dict],
        key_fields: Tuple[str, ...],
        formatters: Tuple[Callable[[float | None], str], ...],
    ) -> List[Tuple[str, ...]]:
        result: List[Tuple[str, ...]] = []
        for row in rows:
            values: List[str] = []
            for key in key_fields:
                values.append(str(row.get(key) or "-"))
            for formatter in formatters:
                total_value = row.get("total") if "total" in row else row.get("monto")
                values.append(formatter(total_value))
            result.append(tuple(values))
        return result

    def _format_budget_row(self, row: dict) -> Tuple[str, str, str]:
        mes = row.get("mes")
        mes_label = month_name[int(mes)] if mes else "-"
        categoria = row.get("nombre") or "-"
        monto = _format_money(row.get("monto"))
        return (mes_label, categoria, monto)

    @staticmethod
    def _month_name_to_number(name: str) -> int | None:
        try:
            return list(month_name).index(name)
        except ValueError:
            return None




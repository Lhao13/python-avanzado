"""Pantalla para mostrar las predicciones de gastos mediante el modelo."""

from __future__ import annotations

from typing import Optional
import pandas as pd
import tkinter as tk
from tkinter import messagebox

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from ..logic.modelo import predict_future_expenses
from .theme import Theme


class PrediccionFrame(tk.Frame):
    """Interfaz que permite invocar el modelo de predicción y ver su gráfico."""

    def __init__(self, parent: tk.Misc) -> None:
        super().__init__(parent, padx=18, pady=18, bg=Theme.BACKGROUND)
        tk.Label(
            self,
            text="Predicción de gastos",
            font=(None, 14, "bold"),
            bg=Theme.BACKGROUND,
            fg=Theme.PRIMARY_TEXT,
        ).pack(anchor="w")
        tk.Label(
            self,
            text="Obtén una estimación de los próximos meses basada en tu historial.",
            bg=Theme.BACKGROUND,
            fg=Theme.SECONDARY_TEXT,
        ).pack(anchor="w", pady=(0, 12))

        self._status_label = tk.Label(
            self,
            text="Haz clic en el botón para generar la predicción.",
            fg=Theme.SECONDARY_TEXT,
            bg=Theme.BACKGROUND,
        )
        self._status_label.pack(anchor="w", pady=(0, 12))

        btn = tk.Button(
            self,
            text="Generar predicción",
            command=self._generate_prediction,
            bg=Theme.ACTION_COLOR,
            fg="white",
            activebackground=Theme.ACTION_HOVER,
        )
        btn.pack(anchor="w")

        # El rectángulo que contiene el gráfico se pinta con el color de tarjeta para evitar contrastes.
        self._chart_container = tk.Frame(
            self,
            bd=1,
            relief="solid",
            padx=6,
            pady=6,
            bg=Theme.CARD_BG,
        )
        self._chart_container.pack(fill="both", expand=True, pady=(12, 0))
        self._canvas: Optional[FigureCanvasTkAgg] = None
        self._total_label = tk.Label(
            self,
            text="",
            font=(None, 11, "bold"),
            bg=Theme.BACKGROUND,
            fg=Theme.PRIMARY_TEXT,
        )
        self._total_label.pack(anchor="w", pady=(8, 0))

    def _clear_chart(self) -> None:
        if self._canvas is not None:
            self._canvas.get_tk_widget().destroy()
            self._canvas = None

    def _generate_prediction(self) -> None:
        try:
            forecast, score = predict_future_expenses(months=6)
        except ValueError as exc:
            messagebox.showwarning("Predicción", str(exc))
            self._status_label.config(text=str(exc), fg="#a00")
            self._clear_chart()
            return
        except Exception as exc:
            messagebox.showerror("Predicción", f"No se pudo ejecutar el modelo: {exc}")
            self._status_label.config(text="Ocurrió un error inesperado.", fg="#a00")
            self._clear_chart()
            return

        if forecast.empty:
            self._status_label.config(text="El modelo no pudo generar predicciones.", fg="#a00")
            self._clear_chart()
            return

        self._status_label.config(text=f"Predicción generada (R² ≈ {score:.2f}).", fg="#070")
        figure = Figure(figsize=(8, 4))
        ax = figure.subplots()
        periods = forecast["period"].tolist()
        x = list(range(len(periods)))
        fixed_series = forecast["Fijo"] if "Fijo" in forecast else pd.Series([0.0] * len(periods))
        variable_series = forecast["Variable"] if "Variable" in forecast else pd.Series([0.0] * len(periods))
        fixed_values = fixed_series.tolist()
        variable_values = variable_series.tolist()
        ax.plot(x, fixed_values, marker="o", linestyle="-", color="#1f77b4", label="Gastos fijos")
        ax.plot(x, variable_values, marker="o", linestyle="--", color="#e74c3c", label="Gastos variables")
        ax.set_xticks(x)
        ax.set_xticklabels(periods, rotation=45, ha="right")
        ax.set_title("Gastos estimados para los próximos meses")
        ax.set_ylabel("Monto estimado ($)")
        ax.grid(True, alpha=0.3)
        ax.legend()
        for idx in x:
            ax.annotate(f"${fixed_values[idx]:,.0f}", (idx, fixed_values[idx]), textcoords="offset points", xytext=(0, 6), ha="center", fontsize=8)
            ax.annotate(f"${variable_values[idx]:,.0f}", (idx, variable_values[idx]), textcoords="offset points", xytext=(0, -12), ha="center", fontsize=8)

        self._clear_chart()
        self._canvas = FigureCanvasTkAgg(figure, master=self._chart_container)
        self._canvas.draw()
        self._canvas.get_tk_widget().pack(fill="both", expand=True)

        total = (fixed_series + variable_series).sum()
        self._total_label.config(text=f"Total estimado: ${total:,.2f}")

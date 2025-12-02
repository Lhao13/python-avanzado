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
            text="Usamos Random Forest porque captura relaciones no lineales y evita sobreajustar al mezclar múltiples árboles con diferentes subconjuntos de transacciones.",
            wraplength=520,
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

        self._methodology_label = tk.Label(
            self,
            text="Modelo evaluado con TimeSeriesSplit (entrenando sobre meses anteriores y validando mes a mes para evitar fuga de datos).",
            fg=Theme.SECONDARY_TEXT,
            bg=Theme.BACKGROUND,
            wraplength=520,
        )
        self._methodology_label.pack(anchor="w", pady=(0, 6))
        self._metrics_label = tk.Label(
            self,
            text="",
            fg=Theme.SECONDARY_TEXT,
            bg=Theme.BACKGROUND,
            wraplength=520,
        )
        self._metrics_label.pack(anchor="w", pady=(0, 6))

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
        tk.Label(
            self,
            text="Variables clave",
            font=(None, 12, "bold"),
            bg=Theme.BACKGROUND,
            fg=Theme.PRIMARY_TEXT,
        ).pack(anchor="w", pady=(12, 0))
        self._importance_container = tk.Frame(
            self,
            bd=1,
            relief="solid",
            padx=6,
            pady=6,
            bg=Theme.CARD_BG,
        )
        self._importance_container.pack(fill="both", expand=True, pady=(12, 0))
        self._importance_canvas: Optional[FigureCanvasTkAgg] = None
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
        self._clear_importance_chart()

    def _clear_importance_chart(self) -> None:
        if self._importance_canvas is not None:
            self._importance_canvas.get_tk_widget().destroy()
            self._importance_canvas = None

    def _generate_prediction(self) -> None:
        try:
            forecast, metrics_real, metrics_cv, importances = predict_future_expenses(months=6)
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

        self._status_label.config(text="Predicción generada (TimeSeriesSplit, sin fuga temporal).", fg="#070")
        months = len(forecast)
        accumulated_error = metrics_real["MAE"] * months
        metrics_text = (
            f"Entrenamiento real (últimos {months} meses) → MAE ${metrics_real['MAE']:,.2f} MSE ${metrics_real['MSE']:,.2f} RMSE ${metrics_real['RMSE']:,.2f}"
            f"\nValidación cruzada → MAE ${metrics_cv['CV_MAE']:,.2f} MSE ${metrics_cv['CV_MSE']:,.2f} RMSE ${metrics_cv['CV_RMSE']:,.2f}"
            f"\nError acumulado estimado en el horizonte: ${accumulated_error:,.2f}"
            "\nErrores expresados en pesos mensuales.")
        self._metrics_label.config(text=metrics_text, fg=Theme.PRIMARY_TEXT)
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

        self._render_importance_chart(importances)

    def _render_importance_chart(self, importances: pd.DataFrame) -> None:
        # Dibuja un gráfico de barras horizontales con las variables más influyentes.
        if importances.empty:
            self._clear_importance_chart()
            return
        self._clear_importance_chart()
        top_features = importances.head(8)
        figure = Figure(figsize=(6, 3))
        ax = figure.subplots()
        ax.barh(top_features["feature"], top_features["importance"], color="#2e86de")
        ax.set_xlabel("Importancia")
        ax.set_title("Variables clave del modelo")
        ax.invert_yaxis()
        ax.grid(False)
        self._importance_canvas = FigureCanvasTkAgg(figure, master=self._importance_container)
        self._importance_canvas.draw()
        self._importance_canvas.get_tk_widget().pack(fill="both", expand=True)

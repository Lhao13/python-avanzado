from __future__ import annotations

import tkinter as tk
from tkinter import PhotoImage

from .dashboard import DashboardFrame
from .gastos import GastosFrame
from .impuestos import ImpuestosFrame
from .ingresos import IngresosFrame
from .prediccion import PrediccionFrame
from .presupuestos import PresupuestosFrame
from .reportes import ReportesFrame
from .transacciones import TransactionForm
from .theme import Theme


class FinanceApp(tk.Tk):
    """Aplicación principal con menú lateral y vistas intercambiables."""

    def __init__(self) -> None:
        super().__init__()
        self.title("Finanzas Personales")
        self.geometry("1500x1200")
        self.resizable(False, False)
        self.configure(bg=Theme.BACKGROUND)
        self._set_window_icon()

        self._view_factories = {
            "Dashboard": lambda parent: DashboardFrame(parent),
            "Registrar transacción": lambda parent: TransactionForm(parent),
            "Objetivos": lambda parent: PresupuestosFrame(parent),
            "Gastos": lambda parent: GastosFrame(parent),
            "Ingresos": lambda parent: IngresosFrame(parent),
            "Impuestos": lambda parent: ImpuestosFrame(parent),
            "Predicción": lambda parent: PrediccionFrame(parent),
            "Reportes": lambda parent: ReportesFrame(parent),
        }
        self._current_view: tk.Widget | None = None
        self._logo_image: PhotoImage | None = None

        self._build_ui()

    def _build_ui(self) -> None:
        container = tk.Frame(self, bg=Theme.BACKGROUND)
        container.pack(fill="both", expand=True)

        sidebar = tk.Frame(container, width=220, bg=Theme.SIDEBAR_BG)
        sidebar.pack(side="left", fill="y")

        self._content_area = tk.Frame(container, bg=Theme.BACKGROUND)
        self._content_area.pack(side="right", fill="both", expand=True)

        logo_label = tk.Label(sidebar, bg=Theme.SIDEBAR_BG)
        try:
            logo_image = PhotoImage(file=str(Theme.LOGO_PATH))
            self._logo_image = logo_image.subsample(5, 5) # Reduce size if needed
            logo_label.configure(image=self._logo_image)
        except Exception:
            logo_label.configure(text="Finanzas 🐖", font=(None, 18, "bold"), fg="white")
        logo_label.pack(pady=(16, 4))

        tk.Label(
            sidebar,
            text="Menú",
            font=(None, 14, "bold"),
            bg=Theme.SIDEBAR_BG,
            fg="white",
        ).pack(pady=(0, 8))

        for label in self._view_factories:
            btn = tk.Button(
                sidebar,
                text=label,
                anchor="w",
                relief="flat",
                padx=12,
                pady=6,
                bg=Theme.ACTION_COLOR,
                fg="white",
                activebackground=Theme.ACTION_HOVER,
            )
            btn.pack(fill="x", pady=2)
            btn.configure(command=lambda name=label: self._show_view(name))

        self._show_view("Dashboard")

    def _show_view(self, name: str) -> None:
        if self._current_view is not None:
            self._current_view.destroy()
        factory = self._view_factories.get(name)
        if factory is None:
            return
        self._current_view = factory(self._content_area)
        self._current_view.pack(fill="both", expand=True)

    def _set_window_icon(self) -> None:
        # Usa el chancho como icono de ventana para que Windows y la barra de título lo muestren.
        try:
            icon_image = PhotoImage(file=str(Theme.LOGO_PATH))
            self.iconphoto(False, icon_image)
        except Exception:
            pass


def main() -> None:
    app = FinanceApp()
    app.mainloop()


if __name__ == "__main__":
    main()

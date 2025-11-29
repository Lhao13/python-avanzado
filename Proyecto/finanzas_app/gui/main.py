from __future__ import annotations

import tkinter as tk

from .dashboard import DashboardFrame
from .gastos import GastosFrame
from .impuestos import ImpuestosFrame
from .ingresos import IngresosFrame
from .presupuestos import PresupuestosFrame
from .reportes import ReportesFrame
from .transacciones import TransactionForm


class FinanceApp(tk.Tk):
    """Aplicación principal con menú lateral y vistas intercambiables."""

    def __init__(self) -> None:
        super().__init__()
        self.title("Finanzas Personales")
        self.geometry("1500x1200")
        self.resizable(False, False)

        self._view_factories = {
            "Dashboard": lambda parent: DashboardFrame(parent),
            "Registrar transacción": lambda parent: TransactionForm(parent),
            "Objetivos": lambda parent: PresupuestosFrame(parent),
            "Gastos": lambda parent: GastosFrame(parent),
            "Ingresos": lambda parent: IngresosFrame(parent),
            "Impuestos": lambda parent: ImpuestosFrame(parent),
            "Reportes": lambda parent: ReportesFrame(parent),
        }
        self._current_view: tk.Widget | None = None

        self._build_ui()

    def _build_ui(self) -> None:
        container = tk.Frame(self)
        container.pack(fill="both", expand=True)

        sidebar = tk.Frame(container, width=200, bg="#f0f0f0")
        sidebar.pack(side="left", fill="y")

        self._content_area = tk.Frame(container, bg="white")
        self._content_area.pack(side="right", fill="both", expand=True)

        tk.Label(sidebar, text="Menú", font=(None, 14, "bold"), bg="#f0f0f0").pack(pady=(16, 8))

        for label in self._view_factories:
            btn = tk.Button(sidebar, text=label, anchor="w", relief="flat", padx=12, pady=6)
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


def main() -> None:
    app = FinanceApp()
    app.mainloop()


if __name__ == "__main__":
    main()

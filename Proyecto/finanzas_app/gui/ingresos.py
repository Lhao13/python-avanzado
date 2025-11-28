"""Vista específica para ingresos."""

from __future__ import annotations

import tkinter as tk


class IngresosFrame(tk.Frame):
    """Vista de ingresos en desarrollo."""

    def __init__(self, parent: tk.Misc) -> None:
        super().__init__(parent, padx=24, pady=24)
        tk.Label(self, text="Movimientos de ingresos pendientes de diseño.").pack(anchor="w")

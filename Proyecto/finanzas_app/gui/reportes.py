"""Panel para reportes financieros."""

from __future__ import annotations

import tkinter as tk


class ReportesFrame(tk.Frame):
    """Vista de reportes por construir."""

    def __init__(self, parent: tk.Misc) -> None:
        super().__init__(parent, padx=24, pady=24)
        tk.Label(self, text="Reportes financieros en desarrollo.").pack(anchor="w")

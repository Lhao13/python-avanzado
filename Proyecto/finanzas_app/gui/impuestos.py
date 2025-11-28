"""Módulo responsable de impuestos y deducciones."""

from __future__ import annotations

import tkinter as tk


class ImpuestosFrame(tk.Frame):
    """Panel simple para impuestos."""

    def __init__(self, parent: tk.Misc) -> None:
        super().__init__(parent, padx=24, pady=24)
        tk.Label(self, text="Cálculo de impuestos pendiente.").pack(anchor="w")

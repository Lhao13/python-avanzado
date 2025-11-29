from __future__ import annotations

from datetime import datetime
import tkinter as tk
from tkinter import messagebox, ttk

from .db.connection import DatabaseConnection
from .models import Categoria, Transaccion
from .repositories import CategoriaRepository, TransaccionRepository


class TransactionApp(tk.Tk):
    """Ventana para registrar gastos e ingresos con categorías filtradas."""

    def __init__(self) -> None:
        super().__init__()
        self.title("Registro de transacción")
        self.geometry("720x360")
        self.resizable(False, False)

        self._db_connection = DatabaseConnection()
        self._trans_repo = TransaccionRepository(self._db_connection)
        self._categoria_repo = CategoriaRepository(self._db_connection)
        self._categories = self._categoria_repo.list_all()
        self._category_groups: dict[str, dict[str, int]] = {
            tipo: {
                f"{cat.nombre}-{cat.periodicidad}": cat.id_categoria
                for cat in self._categories
                if cat.tipo == tipo
            }
            for tipo in ("gasto", "ingreso")
        }
        self._form_vars: dict[str, dict[str, tk.StringVar]] = {}

        self._build_ui()

    def _build_ui(self) -> None:
        container = tk.Frame(self)
        container.pack(fill="both", expand=True, padx=16, pady=12)

        section_frame = tk.Frame(container)
        section_frame.pack(fill="both", expand=True)

        self._create_section(section_frame, "gasto", 0)
        self._create_section(section_frame, "ingreso", 1)

        self.status_label = tk.Label(self, text="Listo", fg="gray")
        self.status_label.pack(pady=6)

    def _create_section(self, parent: tk.Frame, tipo: str, column: int) -> None:
        title = "Gastos" if tipo == "gasto" else "Ingresos"
        frame = ttk.LabelFrame(parent, text=title, padding=(12, 8))
        frame.grid(row=0, column=column, padx=8, sticky="nsew")
        parent.grid_columnconfigure(column, weight=1)

        vars_map = {
            "amount": tk.StringVar(),
            "quantity": tk.StringVar(),
            "date": tk.StringVar(value=datetime.now().date().isoformat()),
            "description": tk.StringVar(),
            "category": tk.StringVar(),
        }
        self._form_vars[tipo] = vars_map

        padding = {"padx": 6, "pady": 4}
        tk.Label(frame, text="Monto (positivo):").grid(row=0, column=0, sticky="w", **padding)
        tk.Entry(frame, textvariable=vars_map["amount"]).grid(row=0, column=1, **padding)

        tk.Label(frame, text="Cantidad (opcional):").grid(row=1, column=0, sticky="w", **padding)
        tk.Entry(frame, textvariable=vars_map["quantity"]).grid(row=1, column=1, **padding)

        tk.Label(frame, text="Fecha (YYYY-MM-DD):").grid(row=2, column=0, sticky="w", **padding)
        tk.Entry(frame, textvariable=vars_map["date"]).grid(row=2, column=1, **padding)

        tk.Label(frame, text="Categoría:").grid(row=3, column=0, sticky="w", **padding)
        category_combo = ttk.Combobox(frame, textvariable=vars_map["category"], state="readonly")
        category_combo["values"] = list(self._category_groups.get(tipo, {}).keys())
        if category_combo["values"]:
            category_combo.current(0)
        category_combo.grid(row=3, column=1, **padding)

        tk.Label(frame, text="Descripción:").grid(row=4, column=0, sticky="w", **padding)
        tk.Entry(frame, textvariable=vars_map["description"]).grid(row=4, column=1, **padding)

        submit_btn = tk.Button(frame, text="Guardar transacción", command=lambda t=tipo: self._on_submit(t))
        submit_btn.grid(row=5, column=0, columnspan=2, pady=12)
        if not self._category_groups.get(tipo):
            messagebox.showwarning(
                "Categorías", f"No hay categorías registradas de tipo {title.lower()}; crea al menos una.",
            )
            submit_btn.config(state="disabled")

    def _on_submit(self, tipo: str) -> None:
        vars_map = self._form_vars.get(tipo)
        if not vars_map:
            return
        try:
            monto = float(vars_map["amount"].get())
        except ValueError:
            messagebox.showerror("Monto inválido", "Ingresa un monto numérico válido.")
            return
        cantidad = None
        if vars_map["quantity"].get().strip():
            try:
                cantidad = int(vars_map["quantity"].get())
            except ValueError:
                messagebox.showerror("Cantidad inválida", "La cantidad debe ser un entero.")
                return
        try:
            fecha = datetime.strptime(vars_map["date"].get().strip(), "%Y-%m-%d").date()
        except ValueError:
            messagebox.showerror("Fecha inválida", "Usa el formato YYYY-MM-DD para la fecha.")
            return
        categoria_key = vars_map["category"].get()
        categoria_id = self._category_groups.get(tipo, {}).get(categoria_key)
        if not categoria_id:
            messagebox.showerror("Categoría", "Selecciona una categoría válida.")
            return
        transaccion = Transaccion(
            monto=monto,
            cantidad=cantidad,
            fecha=fecha,
            categoria_id=categoria_id,
            description=vars_map["description"].get().strip() or None,
        )
        try:
            new_id = self._trans_repo.create(transaccion)
        except Exception as exc:  # pragma: no cover - interactivo
            messagebox.showerror("Error al guardar", str(exc))
            return
        self.status_label.configure(text=f"Transacción #{new_id} guardada", fg="green")
        self._reset_form(tipo)

    def _reset_form(self, tipo: str) -> None:
        vars_map = self._form_vars.get(tipo)
        if not vars_map:
            return
        vars_map["amount"].set("")
        vars_map["quantity"].set("")
        vars_map["description"].set("")
        vars_map["date"].set(datetime.now().date().isoformat())


def main() -> None:
    app = TransactionApp()
    app.mainloop()


if __name__ == "__main__":
    main()

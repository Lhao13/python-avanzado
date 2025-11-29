from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

import tkinter as tk
from tkinter import messagebox, ttk

from ..db.connection import DatabaseConnection
from ..models import Categoria, Transaccion
from ..repositories import CategoriaRepository, TransaccionRepository


class TransactionForm(tk.Frame):
    """Formulario reutilizable para registrar gastos e ingresos."""

    def __init__(self, parent: tk.Misc) -> None:
        super().__init__(parent)
        self._db_connection = DatabaseConnection()
        self._trans_repo = TransaccionRepository(self._db_connection)
        self._categoria_repo = CategoriaRepository(self._db_connection)
        self._categories = self._categoria_repo.list_all()
        self._category_groups: dict[str, dict[str, int]] = {
            tipo: {
                f"{cat.nombre} - {cat.periodicidad}": cat.id_categoria
                for cat in self._categories
                if cat.tipo == tipo
            }
            for tipo in ("gasto", "ingreso")
        }
        self._form_vars: dict[str, dict[str, tk.StringVar]] = {}
        self._transactions_tree: Optional[ttk.Treeview] = None
        self._selected_transaction_id: Optional[int] = None
        self._transactions_data: list[dict[str, Any]] = []
        self._edit_vars: dict[str, tk.StringVar] = {}
        self._category_display: Optional[tk.Label] = None
        self._update_btn: Optional[tk.Button] = None
        self._delete_btn: Optional[tk.Button] = None

        self._build_ui()

    def _build_ui(self) -> None:
        container = tk.Frame(self)
        container.pack(fill="both", expand=True, padx=16, pady=12)

        section_frame = tk.Frame(container)
        section_frame.pack(fill="both", expand=True)

        self._create_section(section_frame, "gasto", 0)
        self._create_section(section_frame, "ingreso", 1)

        self._build_transaction_table()

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

    def _build_transaction_table(self) -> None:
        """Construye el listado scrollable y el panel de edición debajo del formulario."""
        table_frame = ttk.LabelFrame(self, text="Transacciones registradas", padding=(12, 8))
        table_frame.pack(fill="both", expand=True, padx=16, pady=(8, 12))

        columns = (
            ("fecha", "Fecha", 110, "center"),
            ("categoria", "Categoría", 150, "w"),
            ("descripcion", "Descripción", 160, "w"),
            ("monto", "Monto", 100, "e"),
            ("cantidad", "Cantidad", 80, "center"),
        )
        self._transactions_tree = ttk.Treeview(
            table_frame,
            columns=[col[0] for col in columns],
            show="headings",
            selectmode="browse",
        )
        for key, heading, width, anchor in columns:
            self._transactions_tree.heading(key, text=heading)
            self._transactions_tree.column(key, width=width, anchor=anchor)

        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self._transactions_tree.yview)
        self._transactions_tree.configure(yscrollcommand=vsb.set)
        self._transactions_tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        self._transactions_tree.bind("<<TreeviewSelect>>", self._on_tree_select)

        edit_frame = ttk.LabelFrame(self, text="Editar / eliminar transacción", padding=(12, 8))
        edit_frame.pack(fill="x", padx=16, pady=(0, 12))

        self._edit_vars = {
            "amount": tk.StringVar(),
            "quantity": tk.StringVar(),
            "date": tk.StringVar(),
            "description": tk.StringVar(),
        }
        padding = {"padx": 6, "pady": 4}
        tk.Label(edit_frame, text="Monto:").grid(row=0, column=0, sticky="w", **padding)
        tk.Entry(edit_frame, textvariable=self._edit_vars["amount"]).grid(row=0, column=1, **padding)

        tk.Label(edit_frame, text="Cantidad:").grid(row=0, column=2, sticky="w", **padding)
        tk.Entry(edit_frame, textvariable=self._edit_vars["quantity"]).grid(row=0, column=3, **padding)

        tk.Label(edit_frame, text="Fecha (YYYY-MM-DD):").grid(row=1, column=0, sticky="w", **padding)
        tk.Entry(edit_frame, textvariable=self._edit_vars["date"]).grid(row=1, column=1, **padding)

        tk.Label(edit_frame, text="Descripción:").grid(row=1, column=2, sticky="w", **padding)
        tk.Entry(edit_frame, textvariable=self._edit_vars["description"]).grid(row=1, column=3, **padding)

        tk.Label(edit_frame, text="Categoría: ").grid(row=2, column=0, sticky="w", **padding)
        self._category_display = tk.Label(edit_frame, text="Sin selección", font=(None, 10, "bold"))
        self._category_display.grid(row=2, column=1, columnspan=3, sticky="w")

        btn_frame = tk.Frame(edit_frame)
        btn_frame.grid(row=3, column=0, columnspan=4, pady=(8, 0))
        self._update_btn = tk.Button(btn_frame, text="Actualizar", state="disabled", command=self._update_transaction)
        self._update_btn.pack(side="left", padx=4)
        self._delete_btn = tk.Button(btn_frame, text="Eliminar", state="disabled", command=self._delete_transaction)
        self._delete_btn.pack(side="left", padx=4)

        self._refresh_transactions()

    def _refresh_transactions(self) -> None:
        if not self._transactions_tree:
            return
        self._transactions_data = self._trans_repo.list_all_with_category()
        for child in self._transactions_tree.get_children():
            self._transactions_tree.delete(child)
        for row in self._transactions_data:
            fecha = row.get("fecha")
            fecha_text = fecha.isoformat() if hasattr(fecha, "isoformat") else (str(fecha) if fecha else "")
            monto = row.get("monto") or 0.0
            cantidad = row.get("cantidad")
            self._transactions_tree.insert(
                "",
                "end",
                iid=str(row.get("id_transaccion")),
                values=(
                    fecha_text,
                    row.get("categoria") or "-",
                    row.get("description") or "",
                    f"${monto:,.2f}",
                    cantidad if cantidad is not None else "",
                ),
            )
        self._clear_selection()

    def _on_tree_select(self, event: tk.Event) -> None:
        if not self._transactions_tree:
            return
        selection = self._transactions_tree.selection()
        if not selection:
            self._clear_selection()
            return
        trans_id = int(selection[0])
        transaction = next((t for t in self._transactions_data if t.get("id_transaccion") == trans_id), None)
        if not transaction:
            self._clear_selection()
            return
        self._selected_transaction_id = trans_id
        self._edit_vars["amount"].set(str(transaction.get("monto") or 0))
        cantidad = transaction.get("cantidad")
        self._edit_vars["quantity"].set(str(cantidad) if cantidad is not None else "")
        fecha = transaction.get("fecha")
        self._edit_vars["date"].set(fecha.isoformat() if hasattr(fecha, "isoformat") else "")
        self._edit_vars["description"].set(transaction.get("description") or "")
        if self._category_display:
            self._category_display.config(text=transaction.get("categoria") or "Sin categoría")
        if self._update_btn:
            self._update_btn.config(state="normal")
        if self._delete_btn:
            self._delete_btn.config(state="normal")

    def _clear_selection(self) -> None:
        self._selected_transaction_id = None
        for var in self._edit_vars.values():
            var.set("")
        if self._category_display:
            self._category_display.config(text="Sin selección")
        if self._update_btn:
            self._update_btn.config(state="disabled")
        if self._delete_btn:
            self._delete_btn.config(state="disabled")

    def _update_transaction(self) -> None:
        if not self._selected_transaction_id:
            return
        vars_map = self._edit_vars
        try:
            monto = float(vars_map["amount"].get())
        except ValueError:
            messagebox.showerror("Monto inválido", "Ingresa un monto numérico válido para la edición.")
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
        transaccion = Transaccion(
            id_transaccion=self._selected_transaction_id,
            monto=monto,
            cantidad=cantidad,
            fecha=fecha,
            description=vars_map["description"].get().strip() or None,
        )
        try:
            self._trans_repo.update(transaccion)
        except Exception as exc:  # pragma: no cover - interactivo
            messagebox.showerror("Error al actualizar", str(exc))
            return
        self.status_label.configure(text=f"Transacción #{self._selected_transaction_id} actualizada", fg="green")
        self._refresh_transactions()

    def _delete_transaction(self) -> None:
        if not self._selected_transaction_id:
            return
        confirm = messagebox.askyesno(
            "Eliminar transacción",
            "¿Deseas eliminar esta transacción? Esta acción no se puede deshacer.",
        )
        if not confirm:
            return
        try:
            self._trans_repo.delete(self._selected_transaction_id)
        except Exception as exc:  # pragma: no cover - interactivo
            messagebox.showerror("Error al eliminar", str(exc))
            return
        self.status_label.configure(text=f"Transacción #{self._selected_transaction_id} eliminada", fg="green")
        self._refresh_transactions()

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

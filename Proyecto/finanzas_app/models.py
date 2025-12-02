from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass
class Categoria:
    id_categoria: Optional[int] = None
    nombre: Optional[str] = None
    periodicidad: Optional[str] = None
    tipo: Optional[str] = None
    descripcion: Optional[str] = None


@dataclass
class Transaccion:
    id_transaccion: Optional[int] = None
    monto: float = 0.0
    cantidad: Optional[int] = None
    fecha: Optional[date] = None
    categoria_id: Optional[int] = None
    description: Optional[str] = None


@dataclass
class PresupuestoEspecifico:
    id_presupuesto: Optional[int] = None
    anio: Optional[int] = None
    mes: Optional[int] = None
    monto: Optional[float] = None
    categoria_id: Optional[int] = None
    comentario: Optional[str] = None



@dataclass
class ImpuestoAnual:
    anio: Optional[int] = None
    impuesto_pagado: Optional[float] = None

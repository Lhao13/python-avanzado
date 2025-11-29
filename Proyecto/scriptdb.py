import mysql.connector
from datetime import date, timedelta
import random

#Script para poblar la base de datos con datos aleatorios

# ============================================
#  CONEXIÓN A MYSQL
# ============================================
config = {
    "host": "localhost",
    "user": "root",
    "password": "Dante2024.",
    "database": "mydb"
}

conn = mysql.connector.connect(**config)
cursor = conn.cursor()
print("Conectado correctamente a MySQL.")


# ============================================
#  FUNCIONES DE INSERCIÓN
# ============================================
def insert_categoria(nombre, periodicidad, tipo, deducible, tipo_deduccion, descripcion):
    query = """
        INSERT INTO Categoria (nombre, periodicidad, tipo, deducible, tipo_deduccion, descripcion)
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    cursor.execute(query, (nombre, periodicidad, tipo, deducible, tipo_deduccion, descripcion))
    conn.commit()
    return cursor.lastrowid


def insert_transaccion(monto, cantidad, fecha, categoria_id, descripcion):
    query = """
        INSERT INTO Transaccion (monto, cantidad, fecha, Categoria_Id_Categoria, description)
        VALUES (%s, %s, %s, %s, %s)
    """
    cursor.execute(query, (monto, cantidad, fecha, categoria_id, descripcion))
    conn.commit()


def insert_presupuesto_especifico(anio, mes, monto, categoria_id):
    query = """
        INSERT INTO Presupuesto_especifico (anio, mes, monto, Categoria_Id_Categoria)
        VALUES (%s, %s, %s, %s)
    """
    cursor.execute(query, (anio, mes, monto, categoria_id))
    conn.commit()



def insert_impuesto_anual(anio, ingreso_total, gastos_deducibles, base_imponible, impuesto_calculado, impuesto_pagado, diferencia):
    query = """
        INSERT INTO impuesto_anual 
        (anio, ingreso_total, gastos_deducibles, base_imponible, impuesto_calculado, impuesto_pagado, diferencia)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    cursor.execute(query, (anio, ingreso_total, gastos_deducibles, base_imponible, impuesto_calculado, impuesto_pagado, diferencia))
    conn.commit()



# ============================================
#  INSERTAR CATEGORÍAS
# ============================================
print("\nInsertando categorías...")

categorias = {
    "Sueldo": ("mensual", "ingreso", 0, None, "Ingreso mensual fijo"),
    "Alquiler": ("mensual", "gasto", 0, None, "Pago de renta"),
    "Comida": ("variable", "gasto", 0, None, "Supermercado"),
    "Transporte": ("variable", "gasto", 0, None, "Movilidad variada"),
    "Ocio": ("variable", "gasto", 0, None, "Cine, bares, juegos"),
    "Servicios": ("mensual", "gasto", 0, None, "Luz, agua, internet"),
    "Salud": ("variable", "gasto", 1, "salud", "Gastos médicos deducibles"),
    "Educación": ("anual", "gasto", 1, "educacion", "Gastos educativos"),
    "Ahorro": ("mensual", "gasto", 0, None, "Dinero ahorrado"),
    "Impuesto SRI anual": ("anual", "gasto", 0, None, "Pago de impuestos anuales")
}

categoria_ids = {}
for nombre, data in categorias.items():
    categoria_ids[nombre] = insert_categoria(nombre, *data)

print("Categorías creadas:", categoria_ids)



# ============================================
#  FUNCIÓN PARA FECHAS ALEATORIAS
# ============================================
def random_date(start_year=2023, end_year=2025):
    start = date(start_year, 1, 1)
    end = date(end_year, 12, 31)
    delta = end - start
    return start + timedelta(days=random.randint(0, delta.days))



# ============================================
#  GENERACIÓN MASIVA DE TRANSACCIONES
# ============================================
print("\nInsertando transacciones aleatorias...")

descripciones = ["Pago", "Compra", "Servicio", "Gasto", "Transacción", "Registro"]

def random_description():
    return random.choice(descripciones) + " " + str(random.randint(1, 999))

# INGRESOS mensuales (24 meses aprox)
for month in range(1, 13):
    insert_transaccion(
        monto=round(random.uniform(1800, 2500), 2),
        cantidad=1,
        fecha=date(2024, month, 1),
        categoria_id=categoria_ids["Sueldo"],
        descripcion="Sueldo mensual"
    )

# GASTOS FIJOS mensuales
for month in range(1, 13):
    insert_transaccion(round(random.uniform(450, 520), 2), 1, date(2024, month, 5), categoria_ids["Alquiler"], "Renta mensual")
    insert_transaccion(round(random.uniform(60, 120), 2), 1, date(2024, month, 10), categoria_ids["Servicios"], "Servicios básicos")

# GASTOS VARIABLES (200–400 transacciones aleatorias)
for _ in range(random.randint(200, 400)):
    categoria = random.choice(["Comida", "Transporte", "Ocio"])
    insert_transaccion(
        monto=round(random.uniform(5, 80), 2),
        cantidad=1,
        fecha=random_date(),
        categoria_id=categoria_ids[categoria],
        descripcion=random_description()
    )

# GASTOS DEDUCIBLES
for _ in range(40):
    insert_transaccion(
        monto=round(random.uniform(30, 150), 2),
        cantidad=1,
        fecha=random_date(),
        categoria_id=categoria_ids["Salud"],
        descripcion="Gasto médico"
    )

# EDUCACIÓN anual
insert_transaccion(
    monto=1500.00,
    cantidad=1,
    fecha=random_date(2023, 2025),
    categoria_id=categoria_ids["Educación"],
    descripcion="Pago colegio anual"
)

# IMPUESTO ANUAL
insert_transaccion(
    monto=round(random.uniform(500, 900), 2),
    cantidad=1,
    fecha=date(2024, 3, 20),
    categoria_id=categoria_ids["Impuesto SRI anual"],
    descripcion="Pago impuesto anual"
)

print("Transacciones generadas exitosamente.")




# ============================================
#  PRESUPUESTOS ESPECÍFICOS
# ============================================
print("\nInsertando presupuestos específicos...")

for cat in ["Comida", "Transporte", "Ocio"]:
    insert_presupuesto_especifico(2024, random.randint(1, 12), random.randint(100, 300), categoria_ids[cat])

print("Presupuestos específicos insertados.")




# ============================================
#  IMPUESTO ANUAL CALCULADO
# ============================================
print("\nInsertando impuesto anual...")

insert_impuesto_anual(
    anio=2024,
    ingreso_total=26000.00,
    gastos_deducibles=1200.00,
    base_imponible=24800.00,
    impuesto_calculado=520.00,
    impuesto_pagado=600.00,
    diferencia=80.00
)

print("Impuesto anual insertado.")



# ============================================
#  CERRAR CONEXIÓN
# ============================================
cursor.close()
conn.close()

print("\n📌 DATOS ALEATORIOS GENERADOS EXITOSAMENTE 📌")



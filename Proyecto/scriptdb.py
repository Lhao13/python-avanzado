import mysql.connector
import random
from datetime import datetime, timedelta

# ----------------------------------------------------------------
# CONEXIÓN A LA BASE DE DATOS
# ----------------------------------------------------------------
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Dante2024.",
    database="mydb"
)
cursor = db.cursor()

print("Conectado a la base de datos.")

# ----------------------------------------------------------------
# CATEGORÍAS: clasificar según su tipo y periodicidad
# ----------------------------------------------------------------
cursor.execute("SELECT Id_Categoria, nombre, periodicidad, tipo FROM categoria")
categorias = cursor.fetchall()

gastos_fijos = []
gastos_variables = []
ingresos_fijos = []
ingresos_variables = []

for cat in categorias:
    id_cat, nombre, periodicidad, tipo = cat
    if tipo == "gasto":
        if periodicidad == "mensual":
            gastos_fijos.append(id_cat)
        else:
            gastos_variables.append(id_cat)
    else:
        if periodicidad == "mensual":
            ingresos_fijos.append(id_cat)
        else:
            ingresos_variables.append(id_cat)

print("Clasificación de categorías completada.")

# ----------------------------------------------------------------
# FUNCIONES PARA GENERAR MONTOS REALISTAS
# ----------------------------------------------------------------

def monto_gasto_fijo(nombre):
    """Gastos fijos casi constantes, variación mínima."""
    base = {
        "Alquiler": 450,
        "Servicios básicos": 80,
        "Internet y telefonía": 40,
        "Transporte fijo": 30,
        "Seguro de salud": 60,
        "Educación": 150,
        "Suscripciones": 20,
        "Gastos bancarios": 5,
    }
    base_monto = base.get(nombre, random.randint(30, 150))
    return round(random.uniform(base_monto * 0.95, base_monto * 1.05), 2)

def monto_gasto_variable():
    """Gastos variables pueden variar mucho."""
    return round(random.uniform(5, 300), 2)

def monto_ingreso_fijo(nombre):
    """Ingresos fijos casi constantes."""
    base = {
        "Sueldo mensual": 1200,
        "Rentas": 300,
    }
    base_monto = base.get(nombre, random.randint(800, 1500))
    return round(random.uniform(base_monto * 0.97, base_monto * 1.03), 2)

def monto_ingreso_variable():
    """Ingresos variables esporádicos pero altos."""
    return round(random.uniform(50, 600), 2)

# ----------------------------------------------------------------
# GENERAR TRANSACCIONES 2023–2025
# ----------------------------------------------------------------
print("Generando transacciones...")

start_date = datetime(2023, 1, 1)
end_date = datetime(2025, 12, 31)

total_transacciones = 1000
contador = 0

while contador < total_transacciones:

    # Fecha aleatoria entre 2023 y 2025
    delta = end_date - start_date
    fecha = start_date + timedelta(days=random.randint(0, delta.days))

    # Escoger categoría
    categoria = random.choice(categorias)
    id_cat, nombre_cat, periodicidad, tipo_cat = categoria

    # Generar monto realista según categoría
    if tipo_cat == "gasto":
        if periodicidad == "mensual":
            monto = monto_gasto_fijo(nombre_cat)
        else:
            monto = monto_gasto_variable()
    else:  # ingresos
        if periodicidad == "mensual":
            monto = monto_ingreso_fijo(nombre_cat)
        else:
            # ingresos variables son raros → insertar menos
            if random.random() < 0.75:
                continue  # saltamos para simular esporádicos
            monto = monto_ingreso_variable()

    cantidad = 1
    descripcion = f"{nombre_cat}"

    cursor.execute(
        "INSERT INTO transaccion (monto, cantidad, fecha, Categoria_Id_Categoria, description) "
        "VALUES (%s, %s, %s, %s, %s)",
        (monto, cantidad, fecha.date(), id_cat, descripcion)
    )

    contador += 1

db.commit()
print(f"Transacciones generadas: {contador}")

# ----------------------------------------------------------------
# GENERAR PRESUPUESTOS ESPECÍFICOS
# ----------------------------------------------------------------
print("Generando presupuestos específicos (4 por mes)...")

def monto_presupuesto():
    return round(random.uniform(50, 400), 2)

for anio in [2023, 2024, 2025]:
    for mes in range(1, 13):
        categorias_random = random.sample([c[0] for c in categorias], 4)

        for cat_id in categorias_random:
            cursor.execute(
                "INSERT INTO presupuesto_especifico (anio, mes, monto, Categoria_Id_Categoria) "
                "VALUES (%s, %s, %s, %s)",
                (anio, mes, monto_presupuesto(), cat_id)
            )

db.commit()
print("Presupuestos específicos generados correctamente.")

# ----------------------------------------------------------------
# FINAL
# ----------------------------------------------------------------
cursor.close()
db.close()

print("✔ Finalizado correctamente.")




#5 carreras unicas
carreras = {"Ingenieria", "Medicina", "Arquitectura", "Derecho", "Psicologia"}

#Tuplas de estudiantes (nombre, edad, carrera)
estudiantes = []

#Diccionario de calificaciones
calificaciones = {}

# Función para calcular el promedio
promedio = lambda notas: round(sum(notas) / len(notas), 2) if notas else 0

# Funciones para manejar estudiantes y calificaciones
def agregar_estudiante(nombre, edad, carrera):
    if carrera in carreras:
        estudiantes.append((nombre, edad, carrera))
        calificaciones[nombre] = []
        print(f"Estudiante {nombre} con {edad} años agregado a la carrera de {carrera}.")
    else:
        print(f"La carrera {carrera} no está disponible.")

# Función para agregar calificaciones
def agregar_calificacion(nombre, calificacion):
    if nombre in calificaciones:
        calificaciones[nombre].append(calificacion)
        print(f"Calificación {calificacion} agregada para {nombre}.")
    else:
        print(f"Estudiante {nombre} no encontrado.")

# Función para obtener el promedio de calificaciones de un estudiante
def promedio_calificaciones(nombre):
    return {nombre: promedio(calificaciones[nombre])} if nombre in calificaciones else None

# Función para obtener el promedio de calificaciones de todos los estudiantes
def promedio_calificaciones_general():
    return {nombre: promedio(notas) for nombre, notas in calificaciones.items()}

# Función para obtener estudiantes por carrera
def obtener_estudiantes_por_carrera(carrera):
    return [estU for estU in estudiantes if estU[2] == carrera]

# Función para obtener los mejores  estudiantes por promedio
def top_estudiantes_por_promedio(n=3):
    promediostemp  = {nombre: promedio(notas) for nombre, notas in calificaciones.items()}
    return sorted(promediostemp.items(), key=lambda item: item[1], reverse=True)[:n]

# Función para obtener los peores estudiantes por promedio
def peores_estudiantes_por_promedio(n=3):
    promediostemp  = {nombre: promedio(notas) for nombre, notas in calificaciones.items()}
    return sorted(promediostemp.items(), key=lambda item: item[1])[:n]

if __name__ == "__main__":
    agregar_estudiante("Ana", 20, "Ingenieria")
    agregar_estudiante("Luis", 22, "Medicina")
    agregar_estudiante("Marta", 19, "Arquitectura")
    agregar_estudiante("Carlos", 21, "Derecho")
    agregar_estudiante("Sofia", 23, "Psicologia")
    agregar_estudiante("Pedro", 24, "Medicina")

    agregar_calificacion("Ana", 95)
    agregar_calificacion("Ana", 92)
    agregar_calificacion("Luis", 88)
    agregar_calificacion("Luis", 90)
    agregar_calificacion("Marta", 85)
    agregar_calificacion("Carlos", 78)
    agregar_calificacion("Sofia", 80)
    agregar_calificacion("Pedro", 70)
    agregar_calificacion("Pedro", 75)
    agregar_calificacion("Pedro", 99)

    print("Promedios de calificaciones de Ana:", promedio_calificaciones("Ana"))

    print("Promedios generales de calificaciones:", promedio_calificaciones_general())

    print("Estudiantes en Medicina:", obtener_estudiantes_por_carrera("Medicina"))

    print("Top 3 estudiantes por promedio:", top_estudiantes_por_promedio(3))

    print("Peores 3 estudiantes por promedio:", peores_estudiantes_por_promedio(3))
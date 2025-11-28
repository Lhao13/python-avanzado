# Finanzas Persona

Proyecto en Python para insertar y consultar datos del esquema MySQL local descrito en `scripts/bd.sql`.

## Objetivo
Registrar y categorizar ingresos y egresos usando clases que reflejan las tablas `Categoria`, `Transaccion`, `Presupuesto_especifico`, `Presupueto_General` e `impuesto_anual` de la base `mydb`.

## Requisitos
- Python 3.11 o superior
- MySQL 5.7+ con la base `mydb` creada (puedes usar el script exportado desde Workbench incluido en esta descripcion)

## Instalacion
1. Crear o activar el entorno virtual:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```
2. Instalar dependencias:
   ```powershell
   pip install -r requirements.txt
   ```
3. Configurar credenciales. Define las variables de entorno `DB_USER`, `DB_PASSWORD`, `DB_DATABASE` y opcionalmente `DB_HOST`, `DB_PORT`, `DB_POOL_SIZE`, `DB_POOL_NAME`. Alternativamente copia `db_config.example.json` y asigna la ruta en `DB_CONFIG_FILE`.

## Estructura inicial
- `finanzas_app/config.py`: carga la configuracion de conexion desde variables o un JSON.
- `finanzas_app/db/connection.py`: crea un pool de conexiones a MySQL.
- `finanzas_app/models.py`: dataclasses para cada tabla.
- `finanzas_app/repositories.py`: repositorios CRUD para facilitar las inserciones y consultas.
- `finanzas_app/check_db.py`: script de verificacion que imprime la version de MySQL y el conteo de categorias.

## Ejecucion
Una vez configuradas las credenciales se puede validar la conexion con:
```powershell
python -m finanzas_app.check_db
```

## Siguiendo el plan
1. Conectar el modulo de persistencia con los scripts que plantees para cada entidad.
2. Construir clases adicionales para logica de negocio y menus CLI cuando el acceso a la BD este funcionando.

## Referencia de repositorios
- `CategoriaRepository`: crea categorías y lista todos los registros de la tabla `categoria`.
- `TransaccionRepository`: inserta una transacción y obtiene las transacciones de una categoría para analizar ingresos o gastos.
- `PresupuestoEspecificoRepository`: mantiene presupuestos mensuales por categoría.
- `PresupuestoGeneralRepository`: registra y consulta montos globales (mensuales/anuales) respetando los `CHECK` definidos en la tabla.
- `ImpuestoAnualRepository`: guarda resúmenes fiscales anuales, registra pagos/deducciones y compara impuesto calculado vs pagado.
- `FinancialReportRepository`: expone reportes compuestos (ahorro mensual/anual, presupuestos globales y por categoría, gastos fijos/variables/anuales, ingresos por categoría/mes/año, reporte anual consolidado).

## Pruebas del módulo de acceso
El script `scripts/test_repositories.py` resuelve lo siguiente:
1. Inserta categorías, transacciones, presupuestos e impuestos con datos controlados.
2. Ejecuta todas las consultas disponibles (ahorros, presupuestos, gastos, ingresos, impuestos) y muestra sus resultados.
3. Limpia automáticamente los registros insertados.

Ejecuta el script desde PowerShell:
```powershell
$env:DB_CONFIG_FILE="C:/Users/Lhao/Documents/9no semestre/python avanzado/Proyecto/db_config.json"
& "C:/Users/Lhao/Documents/9no semestre/python avanzado/Proyecto/finazasPersona/Scripts/python.exe" scripts/test_repositories.py
```

## Interfaz gráfica inicial
Puedes probar la ventana de registro usando Tkinter:

```powershell
python -m finanzas_app.gui
```

La ventana solicita monto, cantidad, fecha, categoría y descripción. Asegúrate de tener al menos una categoría en la tabla `categoria` antes de abrirla; de lo contrario el botón de guardar quedará desactivado.

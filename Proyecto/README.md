# Finanzas Persona

Proyecto en Python para insertar y consultar datos del esquema MySQL local descrito en `scripts/bd.sql`.

## Objetivo
Registrar y categorizar ingresos y egresos usando clases que reflejan las tablas `Categoria`, `Transaccion`, `Presupuesto_especifico` e `impuesto_anual` de la base `mydb`.

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
- `ImpuestoAnualRepository`: guarda resúmenes fiscales anuales, registra pagos/deducciones y compara impuesto calculado vs pagado.
- `FinancialReportRepository`: expone reportes compuestos (ahorro mensual/anual, desglose por categoría de gastos e ingresos, estado de gastos fijos/variables/anuales y reporte consolidado).

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

### Interface Gráfica/GUI

#### Estilos
- Se introdujo `finanzas_app/gui/theme.py` como descriptor central del esquema cromático (colores base, acciones y posición del logo `assets/chancho.png`).
- La barra lateral ahora usa la paleta roja con botones `Theme.ACTION_COLOR`/`Theme.ACTION_HOVER` y un logo escalado, evitando referencias a tonos aislados.
- Cada panel (`dashboard`, `gastos`, `ingresos`, `impuestos`, `presupuestos`, `prediccion`, `reportes`, `transacciones`) pinta su fondo, tarjetas y botones con `Theme.BACKGROUND`, `Theme.CARD_BG`, `Theme.PRIMARY_TEXT`, `Theme.SECONDARY_TEXT` y la familia de colores de acción para mantener consistencia visual.

#### Pantallas
- `dashboard` ahora añade tarjetas y contenedores con colores del tema y comentarios breves que aclaran la jerarquía visual.
- `gastos` combina canvas desplazables, árboles y gráficos dentro de tarjetas con botones accionables en rojo, manteniendo los contenedores y filtros en la paleta compartida.
- `ingresos`, `presupuestos` y `reportes` envuelven controles en `tk.LabelFrame` estilizados y aplican fondos/entradas/acciones temáticos, incluyendo descripciones y botones con texto blanco rojo.
- `impuestos`, `prediccion` y `transacciones` adaptan sus cuadros de entrada, gráficos y tablas (e incluso mensajes de estado) al mismo esquema cromático, para que la UI general se sienta unificada.

## Base de datos y conexión

- La configuración de conexión sigue gestionándose desde `finanzas_app/config.py` y `finanzas_app/db/connection.py`, con soporte para variables de entorno o `db_config.json`.
- `scripts/test_repositories.py` se mantiene como prueba de integración contra MySQL y no sufrió cambios; los cambios recientes sólo agregan una capa estética sobre la UI.

### Estructura de la base `mydb`

- Se usa el dump de MySQL 8.0.44 para recrear la base `mydb` en `localhost`; todas las tablas están en `utf8mb3`/`utf8mb4` y el motor es InnoDB.
- `categoria` almacena el catálogo de categorías con clave primaria compuesta (`Id_Categoria`, `nombre`, `periodicidad`, `tipo`), controla la periodicidad (`anual`, `mensual`, `variable`) y distingue gastos/ingresos; incluye descripciones para cada categoría.
- `impuesto_anual` guarda el impuesto pagado por año (numeración entera) y sólo requiere la columna `anio` como clave primaria para montar deducciones o comparaciones fiscales.
- `presupuesto_especifico` registra montos mensuales por categoría con `anio`, `mes`, `monto` y la clave foránea `Categoria_Id_Categoria` apuntando a `categoria`; cada presupuesto tiene `Id_Presupuesto` auto incremental.
- `transaccion` reúne los registros diarios con columnas clave: `monto`, `cantidad`, `fecha`, `description` y la referencia `Categoria_Id_Categoria`; cada transacción se enlaza con una categoría existente mediante la clave foránea.
- Las tablas incluyen sentencias `DROP TABLE IF EXISTS`, deshabilitan temporalmente keys durante inserciones masivas y aplican restricciones de clave foránea para preservar la integridad referencial.

## Lógica

### Gráficos
- Las figuras usadas por `dashboard`, `gastos`, `ingresos`, `presupuestos` e `impuestos` continúan bajo `finanzas_app/logic/graficos.py`. Aunque no se modificó el núcleo de los gráficos, ahora cada contenedor en la GUI los pinta sobre `Theme.CARD_BG` para suavizar el contraste.

### Modelos
- Los dataclasses en `finanzas_app/models.py` siguen representando las tablas principales y no se alteraron en esta iteración; cualquier cambio futuro al modelo solo deberá sincronizarse con sus vistas para conservar la integridad del esquema.

### Cálculos
- `finanzas_app/logic/calculos.py` mantiene las funciones que alimentan estadísticas (`dashboard`) y los filtros de reportes; la revisión reciente sólo tocó la presentación visual basada en el tema y no alteró las fórmulas o consultas.

## Cambios recientes (ultimos)
- Reportes PDF: el resumen y la tabla principal ahora se renderizan juntos en la página inicial, evitando saltos grandes y mostrando datos más densos desde el inicio.
- Predicción: la vista ahora muestra métricas reales y de validación con `TimeSeriesSplit` y grafica la importancia de características para describir la metodología.
- Presupuestos: el formulario registra comentarios y sólo muestra categorías de gastos variables, y estos comentarios también se listan en las tablas de objetivos.
- Datos de ingresos: la consulta que alimenta las tablas y PDF añade un alias consistente `categoria` para mostrar el nombre de la categoría en todos los contextos.

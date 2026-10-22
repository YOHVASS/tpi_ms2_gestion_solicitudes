# Refactorings aplicados y principios SOLID / Clean Code

Regla seguida en todos los pasos: **refactorizar con pruebas**. Antes de cada
commit se ejecutó el golden master (`tests/test_caracterizacion.py`); ningún
refactoring se integró con la prueba en rojo.

## Resumen

| ID | Técnica (catálogo de Fowler) | Smells que ataca | Commit |
|---|---|---|---|
| R-01 | **Extract Method** + Rename Variable | CS-02, CS-04, CS-07 | commit R-01 |
| R-02 | **Introduce Parameter Object** + Replace Magic Number with Symbolic Constant (enums) | CS-03, CS-05, CS-06 | commit R-02 |
| R-03 | **Move Method** + Extract Class + Replace Error Code with Exception | CS-01, CS-08, CS-09, CS-11, CS-12 | commit R-03 |
| R-04 | Replace Conditional with Polymorphism (Strategy) + tabla de despacho | CS-06, CS-10 | commit R-04 |
| (rev.) | Correcciones del code review | OBS-04, OBS-08 | commit fix(review) |

## R-01 · Extract Method (y Rename Variable)

**Problema.** El bloque de guardado JSON aparecía copiado 4 veces y la búsqueda
de una solicitud por id 2 veces. Las variables `x`, `r`, `rr`, `e` obligaban a
leer todo el método para entenderlas.

**Antes** (`estado-inicial`, repetido en `init`, `registrar`, `cambiar_estado`, `asignar`):

```python
f = open(ARCHIVO, "w", encoding="utf-8")
json.dump(self.d, f, indent=2, ensure_ascii=False)
f.close()
...
x = None
for s in self.d["solicitudes"]:
    if s["id"] == int(id):
        x = s
if x == None:
```

**Después** (commit R-01):

```python
def _guardar(self):
    with open(ARCHIVO, "w", encoding="utf-8") as archivo:
        json.dump(self.d, archivo, indent=2, ensure_ascii=False)

def _buscar_solicitud(self, id_solicitud):
    for solicitud in self.d["solicitudes"]:
        if solicitud["id"] == int(id_solicitud):
            return solicitud
    return None
```

**Efecto medido.** Complejidad promedio C (12,8) → B (6,9); advertencias de ruff 70 → 52.

## R-02 · Introduce Parameter Object (+ enums del dominio)

**Problema.** `registrar` recibía 7 parámetros posicionales, dos de ellos sin uso.
Estados y prioridades eran números mágicos con su significado en un comentario.

**Antes:**

```python
# estados: 0=pendiente 1=en proceso 2=resuelta 3=rechazada
def registrar(self, legajo, tipo, prioridad, descripcion, fecha_str, canal, observaciones):
    ...
    if tipo == "certificado":
        area = "Bedelia"
    elif tipo == "cambio_comision":
        area = "Bedelia"
    ...
```

**Después** (commit R-02):

```python
@dataclass(frozen=True)
class DatosRegistro:
    legajo: str
    tipo: str
    prioridad: str
    descripcion: str
    fecha: str | None = None

class TipoSolicitud(_EnumDeTexto):
    CERTIFICADO = "certificado"
    ...
    @property
    def area(self) -> str:
        return _AREA_POR_TIPO[self]

def registrar(self, datos: DatosRegistro): ...
```

Se aplicó lo mismo a la búsqueda: `FiltroSolicitudes` reemplaza los 4 parámetros
de `buscar`.

## R-03 · Move Method (reubicación de responsabilidad) + Extract Class

**Problema.** Las reglas de transición de estado pertenecen a la *solicitud*,
pero vivían en `Sistema`, que manipulaba `x["estado"]` desde afuera (Feature
Envy). `Sistema` además persistía, notificaba e imprimía (God Class).

**Antes:**

```python
def cambiar_estado(self, id, nuevo):          # en Sistema
    ...
    if x["estado"] == 2 or x["estado"] == 3:
        print("ERROR: la solicitud #" + str(id) + " ya esta cerrada")
        return False
    if x["estado"] == 0 and n == 2:
        print("ERROR: no se puede resolver una solicitud que no esta en proceso")
        return False
    ...
    x["estado"] = n
```

**Después** (commit R-03): la regla se mueve a la entidad dueña del dato y los
errores pasan a ser excepciones.

```python
@dataclass
class Solicitud:
    ...
    def cambiar_estado(self, nuevo: Estado) -> None:
        self._verificar_abierta()
        if self.estado == Estado.PENDIENTE and nuevo == Estado.RESUELTA:
            raise TransicionInvalida("no se puede resolver una solicitud que no esta en proceso")
        ...
        self.estado = nuevo
```

`Sistema` se dividió en clases con una sola razón de cambio:

| Clase | Responsabilidad |
|---|---|
| `Solicitud`, `Estudiante`, `Responsable` | Datos y reglas del dominio |
| `ServicioSolicitudes` | Casos de uso (orquesta) |
| `RepositorioJSON` / `RepositorioEnMemoria` | Persistencia |
| `NotificadorConsola` | Aviso al estudiante |
| `GeneradorReporte` + formatos | Reporte |
| `solicitudes/cli.py` | Entrada/salida por consola |

## R-04 · Replace Conditional with Polymorphism (Strategy) y tabla de comandos

**Antes:**

```python
if formato == "texto":
    print("=== REPORTE DE SOLICITUDES ===")
    ...
elif formato == "csv":
    print("metrica,valor")
    ...
else:
    print("ERROR: formato de reporte invalido: " + formato)
```

**Después** (commit R-04):

```python
class FormatoReporte(Protocol):
    def renderizar(self, resumen: ResumenSolicitudes) -> list[str]: ...

FORMATOS = {"texto": FormatoTexto(), "csv": FormatoCSV()}
```

Agregar un formato (por ejemplo Markdown) es crear una clase y registrarla; la
prueba `test_un_formato_nuevo_se_agrega_sin_modificar_el_generador` lo demuestra.
La cadena `if a[1] == "init" ... elif ...` de `main` se reemplazó por la tabla
`COMANDOS`, con una función pequeña por comando.

## Aplicación de SOLID

| Principio | Dónde se violaba | Qué se hizo | Dónde verlo |
|---|---|---|---|
| **SRP** | `Sistema` tenía 6 razones de cambio | Separación en dominio, servicio, repositorio, notificador, reportes y CLI | `solicitudes/` |
| **OCP** | Cadenas if/elif por tipo, prioridad, estado y formato | Enums con datos asociados; formatos como estrategias; tabla de comandos | `dominio.py`, `reportes.py`, `cli.py` |
| **LSP** | — (no había abstracciones) | `RepositorioEnMemoria` y `RepositorioJSON` cumplen el mismo contrato; una sola batería de pruebas corre sobre ambas | `tests/test_repositorio.py` |
| **ISP** | — | `ConsultaSolicitudes` (solo lectura) separada de `RepositorioSolicitudes`; el reporte depende solo de la primera | `repositorio.py`, `reportes.py` |
| **DIP** | `open()`, `datetime.now()` y `print` del email embebidos | El servicio recibe repositorio, notificador y reloj por constructor (protocolos) | `servicio.py`, `cli.py::construir_aplicacion` |

## Aplicación de Clean Code

| Práctica | Antes | Después |
|---|---|---|
| Nombres que revelan intención | `d`, `l`, `x`, `r`, `rr`, `p`, `n`, `proc` | `solicitud`, `responsable`, `encontradas`, `vencimiento`, `por_estado` |
| Funciones pequeñas | `buscar` CC 27, `cambiar_estado` CC 18 | Máximo CC 7; promedio 1,9 |
| Manejo de errores | `except: pass`, `return -1`/`False`, tracebacks | Jerarquía `ErrorDeNegocio`; un único punto que traduce a `ERROR:` y código 1 |
| Sin números mágicos | `0..3`, `1..3`, `2/5/10`, `200` | `Estado`, `Prioridad.dias_de_resolucion`, `LONGITUD_MAXIMA_DESCRIPCION` |
| DRY | Guardado JSON ×4, búsqueda por id ×2 | Un solo lugar para cada cosa |
| Límites con terceros | Formato de archivo mezclado con la lógica | El mapeo a códigos numéricos vive solo en `repositorio.py` (wrapper del formato) |
| Comentarios | Explicaban código confuso | Docstrings que explican el *porqué* |

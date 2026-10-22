# Diagnóstico de calidad: versión inicial (tag `estado-inicial`)

## 1. Calidad externa (lo que ve el usuario)

| Funcionalidad | Resultado observado | Evidencia |
|---|---|---|
| Registrar solicitud | Funciona: valida legajo, tipo, prioridad y descripción; asigna área y vencimiento | `tests/golden/salida_esperada.txt` |
| Asignar responsable | Funciona: controla que el responsable pertenezca al área | ídem |
| Cambiar estado | Funciona: respeta el flujo pendiente → en_proceso → resuelta/rechazada y notifica | ídem |
| Buscar / filtrar | Funciona con filtros combinables (estado, tipo, prioridad, legajo) | ídem |
| Reporte | Funciona en formato texto y CSV | ídem |
| Entradas mal formadas | **Falla**: traceback de Python (`estado abc resuelta`, `estado 4`, `buscar estado`) | `docs/evidencias/antes/defectos_detectados.txt` |
| Archivo de datos dañado | **Falla silenciosa**: informa 0 solicitudes sin avisar | ídem |

Conclusión: desde el usuario, el camino feliz funciona. Los problemas aparecen en
los caminos de error y, sobre todo, en la estructura interna.

## 2. Calidad interna (métricas)

| Métrica | Valor | Herramienta |
|---|---|---|
| Clases / funciones | 1 clase (`Sistema`) con 7 métodos + `main` | — |
| Líneas de código (SLOC) | 286 en un único archivo | `radon raw` |
| Complejidad ciclomática promedio | **C (12,8)** | `radon cc` |
| Método más complejo | `Sistema.buscar`: **D (27)** | `radon cc` |
| Advertencias del linter | **70** (17 números mágicos, 11 `== None`, 6 complejidad, 5 `open` sin `with`, 1 `except:` vacío) | `ruff check` |
| Pruebas automatizadas | 0 (antes de este diagnóstico) | — |

## 3. Code smells y debilidades técnicas

Prioridad = impacto en el costo del cambio × probabilidad de que esa zona cambie.

| ID | Smell | Ubicación (`app.py`) | Evidencia | Impacto / riesgo de mantenimiento | Prioridad |
|---|---|---|---|---|---|
| CS-01 | God Class / Large Class | `Sistema` (l. 12-272) | Persistencia, validación, reglas de negocio, notificación, impresión, reporte y datos de ejemplo en una clase | Cualquier cambio toca el mismo archivo; viola SRP; imposible probar partes aisladas | Alta |
| CS-02 | Long Method | `registrar` (l. 50-110, CC 17), `cambiar_estado` (CC 18), `buscar` (CC 27) | 60 líneas con 6 bloques de responsabilidad distintos | Difícil de leer y de modificar sin romper otra rama | Alta |
| CS-03 | Long Parameter List + parámetros muertos | `registrar(legajo, tipo, prioridad, descripcion, fecha_str, canal, observaciones)` (l. 50) | 7 parámetros; `canal` y `observaciones` no se usan (ruff ARG002) | Llamadas frágiles al orden; ruido que confunde | Media |
| CS-04 | Duplicated Code | Guardado JSON repetido en l. 43, 106, 148, 180; búsqueda por id repetida en `cambiar_estado` y `asignar`; chequeo "ya está cerrada" duplicado | Mismo bloque copiado 4-5 veces | Un cambio de formato de persistencia exige tocar 5 lugares (cirugía de escopeta) | Alta |
| CS-05 | Primitive Obsession + números mágicos | Estados `0..3`, prioridades `1..3`, SLA `2/5/10`, listas `["", "alta", ...]` (l. 8-9, 72-99, 210-211); entidades como `dict` | 17 PLR2004 | El significado vive en un comentario; un error de índice pasa inadvertido | Alta |
| CS-06 | Switch Statements (cadenas if/elif) | tipo→área (l. 60-69), prioridad (l. 72-80), estado (l. 120-129, 191-200), formato de reporte (l. 248-272) | 5 cadenas condicionales paralelas | Agregar un tipo, estado o formato obliga a modificar código existente (viola OCP) | Alta |
| CS-07 | Nombres poco expresivos | `d`, `l`, `x`, `r`, `rr`, `p`, `n`, `a`, `s`, `proc`; `id` oculta el builtin; `init` vs `__init__` | ruff E741 | Hay que leer todo el método para entender cada variable | Media |
| CS-08 | Manejo de errores deficiente | `except: pass` (l. 19); códigos de retorno `-1`/`False` mezclados; `r == False` en `main` | ruff E722, E712; tracebacks en `defectos_detectados.txt` | Fallas silenciosas (archivo dañado) y caídas no controladas | Alta |
| CS-09 | Dependencias rígidas a infraestructura (DIP) | Global `ARCHIVO`; `open()` directo; `datetime.now()` oculto (l. 90, 225); "email" impreso inline (l. 154) | Sin forma de inyectar repositorio, reloj ni notificador | Código no testeable de forma aislada; cambiar JSON por BD implica reescribir la clase | Alta |
| CS-10 | Mezcla de presentación y lógica | `print` dentro de las reglas de negocio; `buscar` imprime y además retorna | 41 `print` dentro de `Sistema` | No se puede reutilizar la lógica desde otra interfaz (web, API) | Media |
| CS-11 | Feature Envy / responsabilidad mal ubicada | Reglas de transición y cálculo de vencimiento de la *solicitud* viven en `Sistema` | `cambiar_estado` manipula `x["estado"]` desde afuera | La regla de negocio no está donde está el dato; se duplica al crecer | Media |
| CS-12 | Datos de ejemplo en el código + id frágil | `init` (l. 22-48); `nuevo_id = len(...) + 1` (l. 100) | Datos semilla mezclados con lógica | Si en el futuro se borran solicitudes, se repiten ids | Baja |
| CS-13 | Comentarios que compensan código poco claro | l. 1-2, 8-9, 104 ("por ahora no se usan") | Tabla de códigos en un comentario | Comentarios que se desactualizan; el código no se explica solo | Baja |

## 4. Defectos funcionales detectados

| ID | Defecto | Reproducción | Decisión |
|---|---|---|---|
| D-01 | Id no numérico provoca `ValueError` | `app.py estado abc resuelta` | Corregir: mensaje `ERROR:` y salida 1 |
| D-02 | Faltan argumentos → `IndexError` | `app.py estado 4` | Corregir: mostrar uso |
| D-03 | Filtro sin `=` → `ValueError` | `app.py buscar estado` | Corregir: mensaje de error |
| D-04 | Archivo de datos dañado se ignora en silencio | `datos.json` truncado + `app.py reporte` | Corregir: informar el error y no continuar |

Estas correcciones **mejoran** el comportamiento externo sin alterar los casos ya
aprobados en el golden master.

## 5. Plan priorizado

1. Red de seguridad: pruebas de caracterización (golden master) sobre la versión inicial.
2. Prioridad alta: CS-04, CS-05, CS-02, CS-01, CS-09, CS-08, CS-06.
3. Prioridad media: CS-03, CS-07, CS-10, CS-11.
4. Prioridad baja: CS-12, CS-13.

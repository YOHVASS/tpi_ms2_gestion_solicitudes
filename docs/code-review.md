# Code review técnico

- **Alcance:** diff `estado-inicial..etapa-pruebas` (todo el paquete `solicitudes/`, `app.py` y `tests/`).
- **Revisores:** Natalia Gutierrez, Gino Canevaro y Yohanna Díaz Monroy (revisión con checklist).
- **Herramientas de apoyo:** ruff (linter + formatter), radon (complejidad y mantenibilidad), pytest-cov (cobertura de ramas).
- **Regla de feedback:** se critica el código, no a la persona; cada observación explica el impacto y propone una acción.

## 1. Checklist aplicado

| # | Categoría | Pregunta | Resultado | Evidencia / observación |
|---|---|---|---|---|
| 1 | Lógica | ¿El código hace lo que se supone que debe hacer? | ✔ | Golden master 2/2 en verde, 38 pasos sin diferencias |
| 2 | Lógica | ¿Cubre casos de borde? | ✔ | 200/201 caracteres, día exacto de vencimiento, repositorio vacío |
| 3 | Lógica | ¿Hay condiciones que puedan fallar? | ✔ | D-01..D-06 corregidos con regresión en `test_cli.py` |
| 4 | Lógica | ¿Los errores se manejan adecuadamente? | ⚠ → ✔ | OBS-04 (escritura no atómica), corregido |
| 5 | Legibilidad | ¿Nombres de variables y funciones descriptivos? | ✔ | Sin nombres de una letra; vocabulario del dominio |
| 6 | Legibilidad | ¿Un desarrollador nuevo lo entiende sin ayuda? | ✔ | README + docstrings de módulo |
| 7 | Legibilidad | ¿Hay comentarios innecesarios? | ✔ | Solo docstrings que explican decisiones |
| 8 | Legibilidad | ¿Sigue las convenciones del equipo? | ⚠ | OBS-06 (sufijo `Error`), aceptado con justificación |
| 9 | Diseño | ¿Respeta SOLID? | ✔ | Ver `docs/refactorings.md`; OBS-03 aceptado |
| 10 | Diseño | ¿Respeta DRY? | ✔ | Sin bloques duplicados (antes: guardado ×4) |
| 11 | Diseño | ¿Está en la capa correcta? | ✔ | La CLI es la única que imprime; el dominio no conoce JSON |
| 12 | Diseño | ¿Introduce acoplamiento innecesario? | ✔ | Dependencias por protocolos; OBS-03 |
| 13 | Diseño | ¿Funciones pequeñas y complejidad acotada? | ✔ | Máx. CC 7 (umbral acordado: 8) |
| 14 | Seguridad | ¿Hay datos sensibles expuestos? | ✔ | Solo datos sintéticos (`example.edu`); OBS-05 |
| 15 | Seguridad | ¿Vulnerable a inyecciones? | ✔ | No hay SQL ni ejecución de comandos; entradas validadas contra enums |
| 16 | Seguridad | ¿Se validan correctamente los inputs? | ✔ | Id, fecha, filtros, tipo, prioridad, estado, descripción |
| 17 | Rendimiento | ¿Hay bucles o consultas ineficientes? | ⚠ | OBS-09: carga completa del archivo (aceptable en el alcance) |
| 18 | Pruebas | ¿Hay pruebas que pasen y cubran los cambios? | ✔ | 75 pruebas, 99 % de ramas |
| 19 | Estilo | ¿Linter y formatter sin advertencias? | ✔ | `ruff check` y `ruff format --check` limpios |
| 20 | Documentación | ¿README y decisiones actualizados? | ⚠ → ✔ | OBS-10: README describía la versión base, actualizado |
| 21 | Atomicidad | ¿Cada commit resuelve una sola cosa? | ✔ | Un commit por refactoring, mensaje con smells atacados |
| 22 | Datos | ¿Se mantiene la compatibilidad de los datos existentes? | ✔ | `datos.json` idéntico; prueba `test_json_persiste_con_el_formato_de_la_version_inicial` |

## 2. Observaciones y feedback

| ID | Severidad | Ubicación | Observación (feedback) | Acción | Estado |
|---|---|---|---|---|---|
| OBS-01 | Baja | `dominio.py` · `Solicitud.cambiar_estado` | Es el método más complejo (CC 7). Hoy es legible porque cada regla es una línea, pero si aparecen más estados conviene pasar al patrón State. | Registrado como mejora futura | Aceptado |
| OBS-02 | Baja | `dominio.py` · `_EnumDeTexto.mensaje_invalido` | El método abstracto lanza `NotImplementedError` y queda como única línea sin cobertura. Es intencional: obliga a cada enum a definir su mensaje. | Ninguna | Aceptado |
| OBS-03 | Baja | `cli.py` · `Aplicacion.repositorio: RepositorioJSON` | La CLI depende de la clase concreta. Es la *raíz de composición* (el único lugar que arma las dependencias), por lo que es correcto que conozca la implementación. | Ninguna | Aceptado |
| OBS-04 | **Alta** | `repositorio.py` · `RepositorioJSON._persistir` | La escritura directa con `write_text` puede dejar un `datos.json` a medio escribir si el proceso se corta, que es justamente el defecto D-04 que queríamos evitar. Propuesta: escribir a un temporal y reemplazar con `os.replace`. | Corregido + 2 pruebas | ✔ commit fix(review) |
| OBS-05 | Info | `notificaciones.py` | Se imprime el email del estudiante. Con datos reales habría que enmascararlo; en este trabajo los datos son sintéticos. | Ninguna | Aceptado |
| OBS-06 | Baja | `dominio.py` · excepciones | ruff N818 pide el sufijo inglés `Error`. En español usamos el prefijo (`ErrorDeNegocio`), que se lee más natural. | Regla ignorada en `pyproject.toml` con comentario | Aceptado |
| OBS-07 | Baja | `dominio.py` · `Solicitud.nueva` | 6 parámetros (PLR0913). Es un constructor nombrado de la entidad y todos los datos son obligatorios; agruparlos en otro objeto solo movería el problema. | `noqa` con referencia a esta observación | Aceptado |
| OBS-08 | Media | `dominio.py` · `FiltroSolicitudes.CLAVES` | Sin `ClassVar`, un lector puede pensar que `CLAVES` es un campo del dataclass. | Anotado como `ClassVar` | ✔ commit fix(review) |
| OBS-09 | Baja | `repositorio.py` | Se carga todo el archivo en memoria en cada ejecución. Para el volumen del caso (cientos de solicitudes) es suficiente; con miles convendría SQLite detrás del mismo protocolo. | Mejora futura | Aceptado |
| OBS-10 | Media | `README.md` | Describía la versión base (sin pruebas, sin estructura). Un desarrollador nuevo no sabría cómo correr la suite. | Actualizado | ✔ commit de docs |

## 3. Criterios de aceptación técnica (TAC)

| Criterio | Umbral | Resultado | ¿Cumple? |
|---|---|---|---|
| Todas las pruebas en verde | 100 % | 75/75 | ✔ |
| Comportamiento externo conservado | Golden master sin diferencias | 38/38 pasos idénticos, `datos.json` idéntico | ✔ |
| Cobertura de ramas | ≥ 80 % | 99 % | ✔ |
| Advertencias del linter | 0 | 0 (antes: 70) | ✔ |
| Complejidad ciclomática máxima por función | ≤ 8 | 7 (antes: 27) | ✔ |
| Observaciones de severidad alta abiertas | 0 | 0 | ✔ |
| Principios de diseño | SRP, OCP, DIP aplicados y justificados | Ver `docs/refactorings.md` | ✔ |
| Documentación | README, decisiones y evidencias actualizados | Ver `docs/` | ✔ |

## 4. Veredicto

**Aprobado** para integrar a `main` con el tag `estado-refactorizado`, con
OBS-01 y OBS-09 registradas como mejoras futuras.

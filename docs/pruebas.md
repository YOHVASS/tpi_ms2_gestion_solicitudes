# Estrategia de pruebas y verificación

## 1. Red de seguridad previa al refactoring: golden master

Antes de tocar el código (commit «test: pruebas de caracterización», tag `etapa-diagnostico`) se escribió
una **prueba de caracterización** que ejecuta la CLI real en 38 pasos
(`tests/escenario.py`) y guarda como "salida aprobada":

- todo lo que se imprime por pantalla,
- el código de salida de cada comando,
- el archivo `datos.json` resultante.

La misma prueba, **sin modificaciones**, se ejecutó después de cada refactoring
(R-01 a R-04). Si un cambio hubiera alterado un mensaje, un código de salida o el
formato del archivo, la prueba habría fallado.

Evidencia: `docs/evidencias/verificacion_golden_master.txt`
(2/2 en verde en `estado-inicial` y en la versión final; 38 pasos, 0 diferencias,
`datos.json` idéntico).

## 2. Pruebas unitarias de la versión refactorizada

| Suite | Qué verifica | Técnica | Casos |
|---|---|---|---|
| `test_dominio.py` | Reglas de la entidad `Solicitud`, enums, validaciones, filtros | AAA, parametrización, casos de borde (200/201 caracteres, día de vencimiento) | 30 |
| `test_servicio.py` | Casos de uso | Fake (repositorio en memoria), stub (reloj fijo), mock (notificador), escenario Dado/Cuando/Entonces | 13 |
| `test_repositorio.py` | Contrato del repositorio sobre las 2 implementaciones (LSP), formato JSON compatible, archivo dañado, escritura atómica | Pruebas de contrato parametrizadas, monkeypatch | 10 |
| `test_reportes.py` | Cálculo del resumen, formatos, extensión con formato nuevo (OCP) | Estrategia inyectada | 6 |
| `test_cli.py` | Regresión de los defectos D-01 a D-06 y flujo feliz en proceso | Salida capturada, reloj inyectado | 14 |
| `test_caracterizacion.py` | Comportamiento externo completo | Golden master | 2 |
| **Total** | | | **75** |

## 3. Casos de prueba representativos

| ID | Caso | Entrada | Resultado esperado | Antes | Después |
|---|---|---|---|---|---|
| CP-01 | Registrar solicitud válida | `registrar 1001 certificado alta "Constancia..." 2026-10-01` | `OK: solicitud #4 registrada (area: Bedelia, vence: 2026-10-03)` | ✔ | ✔ |
| CP-02 | Legajo inexistente | `registrar 9999 ...` | `ERROR: el legajo 9999 no existe`, salida 1 | ✔ | ✔ |
| CP-03 | Responsable de otra área | `asignar 4 R2` | `ERROR: Jorge Paz no pertenece al area Bedelia` | ✔ | ✔ |
| CP-04 | Pasar a en_proceso sin responsable | `estado 5 en_proceso` | `ERROR: la solicitud #5 no tiene responsable asignado` | ✔ | ✔ |
| CP-05 | Resolver desde pendiente | `estado 4 resuelta` | `ERROR: no se puede resolver...` | ✔ | ✔ |
| CP-06 | Cambio válido notifica | `estado 4 en_proceso` | Línea `[EMAIL a ...]` + `OK: ...` | ✔ | ✔ |
| CP-07 | Modificar solicitud cerrada | `estado 4 rechazada` | `ERROR: la solicitud #4 ya esta cerrada` | ✔ | ✔ |
| CP-08 | Filtros combinados | `buscar legajo=1001 estado=resuelta` | #1 y #4 | ✔ | ✔ |
| CP-09 | Reporte CSV | `reporte csv` | 10 líneas `metrica,valor` | ✔ | ✔ |
| CP-10 | Id no numérico (D-01) | `estado abc resuelta` | `ERROR: id de solicitud invalido: abc` | ✘ traceback | ✔ |
| CP-11 | Faltan argumentos (D-02) | `estado 4` | `uso: python app.py estado ID ESTADO` | ✘ traceback | ✔ |
| CP-12 | Filtro sin `=` (D-03) | `buscar estado` | `ERROR: filtro invalido: estado (use clave=valor)` | ✘ traceback | ✔ |
| CP-13 | Archivo dañado (D-04) | `datos.json` truncado + `reporte` | `ERROR: no se pudo leer datos.json ...` | ✘ informa 0 | ✔ |
| CP-14 | Valor de filtro inválido (D-05) | `buscar estado=archivada` | `ERROR: estado invalido: archivada` | ✘ devuelve todo | ✔ |
| CP-15 | Fecha inválida (D-06) | `registrar ... 01/10/2026` | `ERROR: fecha invalida: ...` | ✘ traceback | ✔ |

## 4. Cobertura

Cobertura de sentencias y ramas: **99 %** (389 sentencias, 50 ramas; la única
línea sin cubrir es el `raise NotImplementedError` del método abstracto
`_EnumDeTexto.mensaje_invalido`). Detalle en
`docs/evidencias/despues/pytest_resultados.txt`.

## 5. Automatización

- `.pre-commit-config.yaml`: formatter + linter + pruebas antes de cada commit.
- `.github/workflows/ci.yml`: en cada push o pull request ejecuta ruff, verifica
  formato y corre las pruebas con umbral de cobertura de ramas del 80 %.

## 6. Cómo reproducir

```bash
pip install -r requirements-dev.txt
pytest --cov=solicitudes --cov-branch          # versión final
git checkout estado-inicial -- app.py          # (opcional) probar la base
```

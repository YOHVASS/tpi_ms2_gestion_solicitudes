# Gestión de Solicitudes Académicas

Trabajo Práctico Integrador de **Metodología de Sistemas II** (Tecnicatura
Universitaria en Programación a Distancia, UTN).

Sistema de consola para registrar solicitudes de estudiantes (certificados,
cambios de comisión, equivalencias y reclamos de nota), derivarlas al área
correspondiente, asignar un responsable, seguir su estado y generar reportes.

El objetivo del trabajo **no es agregar funcionalidad**, sino diagnosticar y
mejorar la calidad interna de una versión inicial con problemas reales,
conservando su comportamiento externo.

## Versiones (tags)

| Tag | Contenido |
|---|---|
| `estado-inicial` | Versión base: una sola clase de 286 líneas, sin pruebas |
| `etapa-diagnostico` | Golden master + diagnóstico de 13 code smells y 6 defectos |
| `etapa-refactoring` | Refactorings R-01..R-04 (SOLID y Clean Code) |
| `etapa-pruebas` | 73 pruebas unitarias/contrato/regresión + CI |
| `etapa-docs` | Code review, decisiones técnicas y documentación |
| `estado-refactorizado` | Versión final |

## Requisitos e instalación

- Python 3.10 o superior (sin dependencias en tiempo de ejecución).

```bash
git clone <url-del-repositorio>
cd gestion-solicitudes
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt                 # solo para pruebas y análisis
```

## Uso

```bash
python app.py init                                             # carga datos sintéticos de ejemplo
python app.py registrar 1001 certificado alta "Constancia de examen"   # fecha = hoy
python app.py registrar 1002 equivalencia baja "Equivalencia BD" 2026-10-01
python app.py asignar 4 R1
python app.py estado 4 en_proceso                              # notifica al estudiante
python app.py estado 4 resuelta
python app.py buscar estado=pendiente prioridad=alta           # filtros combinables
python app.py reporte                                          # o: reporte csv
```

| Dato | Valores válidos |
|---|---|
| Tipo | `certificado`, `cambio_comision` (Bedelía) · `equivalencia` (Dpto. Académico) · `reclamo_nota` (Docencia) |
| Prioridad | `alta` (2 días) · `media` (5 días) · `baja` (10 días) |
| Estado | `pendiente` → `en_proceso` → `resuelta` / `rechazada` (también `pendiente` → `rechazada`) |
| Filtros | `estado=`, `tipo=`, `prioridad=`, `legajo=` |

## Funcionalidades

1. Registrar solicitud (valida estudiante, tipo, prioridad, descripción y fecha; calcula área y vencimiento).
2. Asignar responsable (debe pertenecer al área de la solicitud).
3. Cambiar estado con reglas de transición y notificación al estudiante.
4. Buscar y filtrar solicitudes.
5. Reporte por estado, área y vencidas, en texto o CSV.

## Arquitectura (versión final)

```
app.py                      punto de entrada
solicitudes/
├── cli.py                  presentación: tabla de comandos, única capa que imprime
├── servicio.py             casos de uso (recibe dependencias inyectadas)
├── dominio.py              entidades, enums y reglas de negocio
├── repositorio.py          protocolos + implementaciones JSON y en memoria
├── notificaciones.py       protocolo Notificador + implementación por consola
├── reportes.py             resumen + formatos (Strategy)
└── semilla.py              datos sintéticos
tests/                      75 pruebas (golden master, unitarias, contrato, regresión)
docs/                       diagnóstico, refactorings, pruebas, code review, ADRs, evidencias
```

## Calidad: antes y después

| Métrica | `estado-inicial` | `estado-refactorizado` |
|---|---|---|
| Advertencias de ruff | 70 | 0 |
| Complejidad ciclomática máxima | 27 (D) | 7 (B) |
| Complejidad promedio | 12,8 (C) | 1,9 (A) |
| Pruebas automatizadas | 0 | 75 |
| Cobertura de ramas | — | 99 % |
| Defectos conocidos | 6 | 0 |

## Pruebas y análisis

```bash
pytest                                       # 75 pruebas
pytest --cov=solicitudes --cov-branch        # cobertura
ruff check . && ruff format --check .        # linter y formato
radon cc -s -a solicitudes                   # complejidad
```

## Documentación

- [Diagnóstico](docs/diagnostico.md) · [Refactorings y SOLID](docs/refactorings.md) · [Pruebas](docs/pruebas.md)
- [Code review](docs/code-review.md) · [Decisiones (ADR)](docs/decisiones/) · [Evidencias](docs/evidencias/)
- [Uso de IA](docs/uso-ia.md) · [Guion del video](docs/guion-video.md)

## Tecnologías

Python 3 (biblioteca estándar: `dataclasses`, `enum`, `typing.Protocol`, `json`, `pathlib`),
pytest + pytest-cov, ruff, radon, pre-commit, GitHub Actions.

## Autora

Yohanna Díaz Monroy · Comisión 7 · 2026. Los datos del sistema son sintéticos.

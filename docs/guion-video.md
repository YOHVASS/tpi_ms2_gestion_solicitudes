# Guion del video de defensa (10 a 15 minutos)

Requisitos de la consigna: cámara encendida, rostro visible, nombre completo,
**voz propia** (no se admiten voces generadas por IA). Pantalla compartida con
la presentación, el repositorio y la terminal.

| Min. | Bloque | Qué mostrar | Qué decir (ideas, no leer) |
|---|---|---|---|
| 0:00 | Presentación | Cámara + portada | Nombre completo, comisión, materia, por qué entrega individual |
| 0:45 | Problema y sistema base | Diapositiva del caso + `git checkout estado-inicial` + `python app.py reporte` | Qué hace el sistema, actores, que *funciona* |
| 2:00 | Calidad externa vs. interna | Tabla de métricas antes | "Funciona, pero..." CC 27, 70 advertencias, 1 clase con 6 responsabilidades, 0 pruebas |
| 3:30 | Code smells | Abrir `app.py` base en 2-3 smells (God Class, guardado ×4, números mágicos, `except: pass`) | Impacto en el costo del cambio y prioridad |
| 5:00 | Red de seguridad | `tests/escenario.py` y correr el golden master | Por qué primero pruebas: refactorizar = cambiar estructura sin cambiar comportamiento |
| 6:00 | Refactorings | `git log --oneline` y el diff de cada R | Extract Method, Introduce Parameter Object, Move Method, Strategy; qué smell resolvió cada uno |
| 8:30 | SOLID | Diagrama de capas | SRP (separación), OCP (formato nuevo sin tocar código), DIP (protocolos + reloj inyectado), LSP (misma prueba para 2 repositorios), ISP |
| 10:00 | Pruebas y evidencias | `pytest --cov=solicitudes --cov-branch` + `verificacion_golden_master.txt` | 75 pruebas, 99 % ramas, 38 pasos idénticos; defectos D-01..D-06 corregidos |
| 11:30 | Code review | `docs/code-review.md` | Checklist, OBS-04 (alta) y cómo se corrigió, criterios de aceptación |
| 12:30 | Conclusiones | Diapositiva final | Aprendizajes, límites, mejoras futuras (State, SQLite, argparse) |


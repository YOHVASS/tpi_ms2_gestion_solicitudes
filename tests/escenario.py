"""Escenario de caracterización (golden master) del comportamiento externo.

Cada paso es una invocación real de la CLI. La salida estándar, el código de
salida y el archivo datos.json resultante forman el "contrato observable" que
el refactoring no puede romper.
"""

PASOS = [
    ["init"],
    # registrar: camino feliz para los 4 tipos y las 3 prioridades
    ["registrar", "1001", "certificado", "alta", "Constancia de examen final", "2026-10-01"],
    ["registrar", "1002", "cambio_comision", "media", "Cambio a comisión 7", "2026-10-02"],
    ["registrar", "1003", "equivalencia", "baja", "  Equivalencia de Base de Datos  ", "2026-10-03"],
    ["registrar", "1001", "reclamo_nota", "alta", "Reclamo nota TP integrador", "2099-05-01"],
    # registrar: errores de validación
    ["registrar", "9999", "certificado", "alta", "Legajo inexistente", "2026-10-01"],
    ["registrar", "1001", "beca", "alta", "Tipo inexistente", "2026-10-01"],
    ["registrar", "1001", "certificado", "urgente", "Prioridad inexistente", "2026-10-01"],
    ["registrar", "1001", "certificado", "alta", "   ", "2026-10-01"],
    ["registrar", "1001", "certificado", "alta", "x" * 201, "2026-10-01"],
    ["registrar", "1001", "certificado"],
    # asignar
    ["asignar", "4", "R1"],
    ["asignar", "4", "R2"],
    ["asignar", "4", "R9"],
    ["asignar", "99", "R1"],
    ["asignar", "1", "R1"],
    ["asignar", "6", "R2"],
    # cambiar estado: reglas de transición
    ["estado", "5", "en_proceso"],
    ["estado", "4", "resuelta"],
    ["estado", "4", "en_proceso"],
    ["estado", "4", "en_proceso"],
    ["estado", "4", "pendiente"],
    ["estado", "4", "archivada"],
    ["estado", "4", "resuelta"],
    ["estado", "4", "rechazada"],
    ["estado", "99", "resuelta"],
    ["estado", "3", "rechazada"],
    # buscar / filtrar
    ["buscar"],
    ["buscar", "estado=pendiente"],
    ["buscar", "tipo=certificado"],
    ["buscar", "prioridad=alta"],
    ["buscar", "legajo=1001", "estado=resuelta"],
    ["buscar", "estado=rechazada", "tipo=equivalencia"],
    # reportes
    ["reporte"],
    ["reporte", "texto"],
    ["reporte", "csv"],
    ["reporte", "pdf"],
    # comando inválido
    ["borrar", "1"],
]

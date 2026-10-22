"""Datos sintéticos de ejemplo (no corresponden a personas reales)."""

DATOS_EJEMPLO = {
    "estudiantes": [
        {"legajo": "1001", "nombre": "Ana Lopez", "email": "ana.lopez@example.edu", "carrera": "TUP"},
        {"legajo": "1002", "nombre": "Bruno Diaz", "email": "bruno.diaz@example.edu", "carrera": "TUP"},
        {"legajo": "1003", "nombre": "Carla Gomez", "email": "carla.gomez@example.edu", "carrera": "TUPaD"},
    ],
    "responsables": [
        {"id": "R1", "nombre": "Marta Ruiz", "area": "Bedelia"},
        {"id": "R2", "nombre": "Jorge Paz", "area": "Departamento Academico"},
        {"id": "R3", "nombre": "Lucia Sosa", "area": "Docencia"},
    ],
    "solicitudes": [
        {
            "id": 1,
            "legajo": "1001",
            "tipo": "certificado",
            "prioridad": 2,
            "descripcion": "Certificado de alumno regular",
            "estado": 2,
            "area": "Bedelia",
            "responsable": "R1",
            "fecha": "2020-03-01",
            "vence": "2020-03-06",
        },
        {
            "id": 2,
            "legajo": "1002",
            "tipo": "equivalencia",
            "prioridad": 1,
            "descripcion": "Equivalencia de Programacion I",
            "estado": 1,
            "area": "Departamento Academico",
            "responsable": "R2",
            "fecha": "2020-03-02",
            "vence": "2020-03-04",
        },
        {
            "id": 3,
            "legajo": "1003",
            "tipo": "reclamo_nota",
            "prioridad": 3,
            "descripcion": "Revision de nota del parcial 1",
            "estado": 0,
            "area": "Docencia",
            "responsable": None,
            "fecha": "2099-01-10",
            "vence": "2099-01-20",
        },
    ],
}

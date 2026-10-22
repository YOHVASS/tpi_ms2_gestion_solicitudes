"""Regresión de los defectos D-01..D-06 detectados en la versión inicial.

Se ejecuta la CLI en proceso, con la salida capturada en una lista y un reloj fijo.
"""

import pytest

from solicitudes.cli import main
from tests.conftest import HOY


@pytest.fixture
def ejecutar(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    def _ejecutar(*argumentos):
        salida = []
        codigo = main(list(argumentos), salida=salida.append, hoy=lambda: HOY)
        return codigo, salida

    _ejecutar("init")
    return _ejecutar


@pytest.mark.parametrize(
    ("argumentos", "mensaje"),
    [
        (("estado", "abc", "resuelta"), "ERROR: id de solicitud invalido: abc"),  # D-01
        (("asignar", "x1", "R1"), "ERROR: id de solicitud invalido: x1"),  # D-01
        (("estado", "4"), "uso: python app.py estado ID ESTADO"),  # D-02
        (("asignar", "4"), "uso: python app.py asignar ID RESPONSABLE"),  # D-02
        (("buscar", "estado"), "ERROR: filtro invalido: estado (use clave=valor)"),  # D-03
        (("buscar", "estado=archivada"), "ERROR: estado invalido: archivada"),  # D-05
        (("buscar", "color=rojo"), "ERROR: filtro desconocido: color (use estado, tipo, prioridad o legajo)"),
        (
            ("registrar", "1001", "certificado", "alta", "x", "01/10/2026"),
            "ERROR: fecha invalida: 01/10/2026 (use AAAA-MM-DD)",
        ),  # D-06
    ],
)
def test_entradas_mal_formadas_se_informan_sin_traceback(ejecutar, argumentos, mensaje):
    codigo, salida = ejecutar(*argumentos)
    assert codigo == 1
    assert salida == [mensaje]


def test_archivo_danado_se_informa(ejecutar, tmp_path):  # D-04
    (tmp_path / "datos.json").write_text('{"estudiantes": [', encoding="utf-8")
    codigo, salida = ejecutar("reporte")
    assert codigo == 1
    assert salida[0].startswith("ERROR: no se pudo leer datos.json")


def test_init_regenera_un_archivo_danado(ejecutar, tmp_path):
    (tmp_path / "datos.json").write_text("basura", encoding="utf-8")
    assert ejecutar("init") == (0, ["OK: datos de ejemplo cargados"])
    assert ejecutar("buscar", "estado=pendiente")[1] == [
        "#3 | 1003 | reclamo_nota | baja | pendiente | - | Revision de nota del parcial 1"
    ]


def test_registrar_sin_fecha_usa_el_reloj(ejecutar):
    codigo, salida = ejecutar("registrar", "1001", "certificado", "alta", "Constancia")
    assert codigo == 0
    assert salida == ["OK: solicitud #4 registrada (area: Bedelia, vence: 2026-10-24)"]


def test_sin_argumentos_muestra_el_uso(ejecutar):
    assert ejecutar() == (1, ["uso: python app.py [init|registrar|estado|asignar|buscar|reporte] ..."])


def test_flujo_feliz_completo_en_proceso(ejecutar):
    assert ejecutar("asignar", "3", "R3") == (0, ["OK: solicitud #3 asignada a Lucia Sosa"])
    assert ejecutar("estado", "3", "en_proceso") == (
        0,
        [
            "[EMAIL a carla.gomez@example.edu] Su solicitud #3 cambio a estado: en_proceso",
            "OK: solicitud #3 ahora esta en_proceso",
        ],
    )
    assert ejecutar("buscar", "estado=rechazada") == (0, ["No se encontraron solicitudes"])
    codigo, salida = ejecutar("reporte", "csv")
    assert codigo == 0
    assert "en_proceso,2" in salida


def test_comando_desconocido(ejecutar):
    assert ejecutar("borrar", "1") == (1, ["ERROR: comando desconocido borrar"])

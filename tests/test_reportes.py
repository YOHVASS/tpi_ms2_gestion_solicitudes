"""Cálculo del resumen y formatos de salida del reporte."""

from datetime import date

import pytest

from solicitudes.dominio import ErrorValidacion, Estado
from solicitudes.reportes import FormatoCSV, FormatoTexto, GeneradorReporte, ResumenSolicitudes


def test_resumen_cuenta_por_estado_area_y_vencidas(repositorio):
    resumen = ResumenSolicitudes.calcular(repositorio.listar_solicitudes(), hoy=date(2026, 10, 22))
    assert resumen.total == 3
    assert resumen.por_estado == {
        Estado.PENDIENTE: 1,
        Estado.EN_PROCESO: 1,
        Estado.RESUELTA: 1,
        Estado.RECHAZADA: 0,
    }
    assert resumen.vencidas == 1  # la #2 venció en 2020; la #3 vence en 2099
    assert list(resumen.por_area) == ["Bedelia", "Departamento Academico", "Docencia"]


def test_las_vencidas_dependen_del_dia_inyectado(repositorio):
    resumen = ResumenSolicitudes.calcular(repositorio.listar_solicitudes(), hoy=date(2099, 2, 1))
    assert resumen.vencidas == 2


def test_resumen_de_repositorio_vacio():
    resumen = ResumenSolicitudes.calcular([], hoy=date(2026, 10, 22))
    assert resumen.total == 0
    assert FormatoTexto().renderizar(resumen)[-1] == "Por area:"


def test_formato_csv(repositorio):
    lineas = GeneradorReporte(repositorio).generar("csv", date(2026, 10, 22))
    assert lineas[:3] == ["metrica,valor", "total,3", "pendientes,1"]
    assert "vencidas,1" in lineas


def test_formato_desconocido(repositorio):
    with pytest.raises(ErrorValidacion, match="formato de reporte invalido: pdf"):
        GeneradorReporte(repositorio).generar("pdf", date(2026, 10, 22))


def test_un_formato_nuevo_se_agrega_sin_modificar_el_generador(repositorio):
    """OCP: se extiende el comportamiento registrando una estrategia nueva."""

    class FormatoMarkdown:
        def renderizar(self, resumen):
            return [f"| total | {resumen.total} |"]

    generador = GeneradorReporte(
        repositorio, {"texto": FormatoTexto(), "csv": FormatoCSV(), "md": FormatoMarkdown()}
    )
    assert generador.generar("md", date(2026, 10, 22)) == ["| total | 3 |"]

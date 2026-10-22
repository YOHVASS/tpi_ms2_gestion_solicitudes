"""Casos de uso con dobles de prueba: repositorio en memoria (fake),
reloj fijo (stub) y notificador simulado (mock)."""

from datetime import date
from unittest.mock import Mock

import pytest

from solicitudes.dominio import (
    DatosRegistro,
    ErrorValidacion,
    Estado,
    FiltroSolicitudes,
    NoEncontrado,
    TransicionInvalida,
)
from solicitudes.servicio import ServicioSolicitudes
from tests.conftest import HOY


@pytest.fixture
def notificador():
    return Mock()


@pytest.fixture
def servicio(repositorio, notificador):
    return ServicioSolicitudes(repositorio, notificador, hoy=lambda: HOY)


def test_registrar_usa_la_fecha_del_reloj_inyectado(servicio, repositorio):
    solicitud = servicio.registrar(DatosRegistro("1002", "certificado", "alta", "  Constancia  "))
    assert solicitud.id == 4
    assert solicitud.fecha == HOY
    assert solicitud.vence == date(2026, 10, 24)
    assert solicitud.descripcion == "Constancia"
    assert repositorio.obtener_solicitud(4) is solicitud


def test_registrar_respeta_el_orden_de_validacion(servicio):
    # el legajo se valida antes que el tipo, igual que en la versión inicial
    with pytest.raises(ErrorValidacion, match="el legajo 9999 no existe"):
        servicio.registrar(DatosRegistro("9999", "beca", "urgente", ""))


def test_registrar_con_fecha_invalida_informa_el_formato(servicio):
    with pytest.raises(ErrorValidacion, match="fecha invalida: 2026-13-01"):
        servicio.registrar(DatosRegistro("1001", "certificado", "alta", "x", fecha="2026-13-01"))


def test_cambiar_estado_guarda_y_notifica_una_sola_vez(servicio, repositorio, notificador):
    """Dado una solicitud pendiente con responsable,
    cuando se la pasa a en_proceso,
    entonces queda en_proceso y se notifica al estudiante."""
    servicio.asignar(3, "R3")

    solicitud = servicio.cambiar_estado(3, "en_proceso")

    assert solicitud.estado == Estado.EN_PROCESO
    estudiante = repositorio.obtener_estudiante("1003")
    notificador.notificar_cambio_de_estado.assert_called_once_with(estudiante, solicitud)


def test_una_transicion_invalida_no_notifica(servicio, notificador):
    with pytest.raises(TransicionInvalida):
        servicio.cambiar_estado(1, "rechazada")  # la #1 ya está resuelta
    notificador.notificar_cambio_de_estado.assert_not_called()


@pytest.mark.parametrize(
    ("id_solicitud", "id_responsable", "mensaje"),
    [(99, "R1", "no existe la solicitud #99"), (3, "R9", "no existe el responsable R9")],
)
def test_asignar_con_referencias_inexistentes(servicio, id_solicitud, id_responsable, mensaje):
    with pytest.raises(NoEncontrado, match=mensaje):
        servicio.asignar(id_solicitud, id_responsable)


def test_asignar_devuelve_solicitud_y_responsable(servicio):
    solicitud, responsable = servicio.asignar(3, "R3")
    assert solicitud.responsable_id == "R3"
    assert responsable.nombre == "Lucia Sosa"


@pytest.mark.parametrize(
    ("criterios", "ids_esperados"),
    [
        ({}, [1, 2, 3]),
        ({"estado": "pendiente"}, [3]),
        ({"prioridad": "alta"}, [2]),
        ({"tipo": "certificado", "legajo": "1001"}, [1]),
        ({"estado": "rechazada"}, []),
    ],
)
def test_buscar_con_filtros(servicio, criterios, ids_esperados):
    encontradas = servicio.buscar(FiltroSolicitudes.desde_texto(criterios))
    assert [s.id for s in encontradas] == ids_esperados

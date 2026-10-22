"""Reglas de negocio de la entidad Solicitud y de los enums del dominio."""

from datetime import date

import pytest

from solicitudes.dominio import (
    LONGITUD_MAXIMA_DESCRIPCION,
    ErrorValidacion,
    Estado,
    FiltroSolicitudes,
    Prioridad,
    Responsable,
    Solicitud,
    TipoSolicitud,
    TransicionInvalida,
    validar_descripcion,
)

BEDELIA = Responsable("R1", "Marta Ruiz", "Bedelia")
DOCENCIA = Responsable("R3", "Lucia Sosa", "Docencia")


def nueva_solicitud(prioridad=Prioridad.MEDIA, fecha=date(2026, 10, 1)):
    return Solicitud.nueva(10, "1001", TipoSolicitud.CERTIFICADO, prioridad, "Constancia", fecha)


@pytest.mark.parametrize(
    ("prioridad", "vencimiento_esperado"),
    [
        (Prioridad.ALTA, date(2026, 10, 3)),
        (Prioridad.MEDIA, date(2026, 10, 6)),
        (Prioridad.BAJA, date(2026, 10, 11)),
    ],
)
def test_vencimiento_depende_de_la_prioridad(prioridad, vencimiento_esperado):
    assert nueva_solicitud(prioridad).vence == vencimiento_esperado


@pytest.mark.parametrize(
    ("tipo", "area"),
    [
        (TipoSolicitud.CERTIFICADO, "Bedelia"),
        (TipoSolicitud.CAMBIO_COMISION, "Bedelia"),
        (TipoSolicitud.EQUIVALENCIA, "Departamento Academico"),
        (TipoSolicitud.RECLAMO_NOTA, "Docencia"),
    ],
)
def test_cada_tipo_se_deriva_a_su_area(tipo, area):
    assert tipo.area == area


def test_una_solicitud_nueva_empieza_pendiente_y_sin_responsable():
    solicitud = nueva_solicitud()
    assert solicitud.estado == Estado.PENDIENTE
    assert solicitud.responsable_id is None
    assert solicitud.area == "Bedelia"


def test_flujo_completo_pendiente_en_proceso_resuelta():
    solicitud = nueva_solicitud()
    solicitud.asignar(BEDELIA)
    solicitud.cambiar_estado(Estado.EN_PROCESO)
    solicitud.cambiar_estado(Estado.RESUELTA)
    assert solicitud.cerrada


def test_se_puede_rechazar_directamente_desde_pendiente():
    solicitud = nueva_solicitud()
    solicitud.cambiar_estado(Estado.RECHAZADA)
    assert solicitud.estado == Estado.RECHAZADA


@pytest.mark.parametrize(
    ("con_responsable", "previos", "destino", "mensaje"),
    [
        (True, [], Estado.RESUELTA, "no se puede resolver una solicitud que no esta en proceso"),
        (False, [], Estado.EN_PROCESO, "la solicitud #10 no tiene responsable asignado"),
        (True, [], Estado.PENDIENTE, "la solicitud ya esta en ese estado"),
        (True, [Estado.EN_PROCESO], Estado.PENDIENTE, "no se puede volver a pendiente"),
        (True, [Estado.EN_PROCESO, Estado.RESUELTA], Estado.RECHAZADA, "la solicitud #10 ya esta cerrada"),
    ],
)
def test_transiciones_invalidas(con_responsable, previos, destino, mensaje):
    # Arrange
    solicitud = nueva_solicitud()
    if con_responsable:
        solicitud.asignar(BEDELIA)
    for estado in previos:
        solicitud.cambiar_estado(estado)
    # Act / Assert
    with pytest.raises(TransicionInvalida, match=mensaje):
        solicitud.cambiar_estado(destino)


def test_no_se_puede_asignar_un_responsable_de_otra_area():
    with pytest.raises(ErrorValidacion, match="Lucia Sosa no pertenece al area Bedelia"):
        nueva_solicitud().asignar(DOCENCIA)


def test_no_se_puede_asignar_una_solicitud_cerrada():
    solicitud = nueva_solicitud()
    solicitud.cambiar_estado(Estado.RECHAZADA)
    with pytest.raises(TransicionInvalida, match="ya esta cerrada"):
        solicitud.asignar(BEDELIA)


@pytest.mark.parametrize(
    ("hoy", "vencida"),
    [(date(2026, 10, 6), False), (date(2026, 10, 7), True)],  # vence el 2026-10-06 (borde)
)
def test_vencimiento_en_el_borde(hoy, vencida):
    assert nueva_solicitud().esta_vencida(hoy) is vencida


def test_una_solicitud_cerrada_nunca_esta_vencida():
    solicitud = nueva_solicitud()
    solicitud.cambiar_estado(Estado.RECHAZADA)
    assert not solicitud.esta_vencida(date(2030, 1, 1))


@pytest.mark.parametrize(
    ("descripcion", "mensaje"),
    [(None, "obligatoria"), ("", "obligatoria"), ("   ", "obligatoria"), ("x" * 201, "supera los 200")],
)
def test_descripciones_invalidas(descripcion, mensaje):
    with pytest.raises(ErrorValidacion, match=mensaje):
        validar_descripcion(descripcion)


def test_descripcion_en_el_limite_es_valida_y_se_normaliza():
    assert validar_descripcion(" " + "x" * (LONGITUD_MAXIMA_DESCRIPCION - 1)) == "x" * 199


@pytest.mark.parametrize(
    ("enum", "texto", "mensaje"),
    [
        (Estado, "archivada", "estado invalido: archivada"),
        (Prioridad, "urgente", "prioridad invalida: urgente"),
        (TipoSolicitud, "beca", "tipo de solicitud invalido: beca"),
    ],
)
def test_textos_desconocidos_se_rechazan_con_mensaje_claro(enum, texto, mensaje):
    with pytest.raises(ErrorValidacion, match=mensaje):
        enum.desde_texto(texto)


def test_filtro_combina_criterios():
    filtro = FiltroSolicitudes.desde_texto({"estado": "pendiente", "legajo": "1001"})
    assert filtro.admite(nueva_solicitud())
    assert not FiltroSolicitudes.desde_texto({"legajo": "1002"}).admite(nueva_solicitud())


def test_filtro_con_clave_desconocida_se_rechaza():
    with pytest.raises(ErrorValidacion, match="filtro desconocido: color"):
        FiltroSolicitudes.desde_texto({"color": "rojo"})

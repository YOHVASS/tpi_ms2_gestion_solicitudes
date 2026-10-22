"""Vocabulario del dominio: estados, prioridades, tipos y objetos parámetro."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from enum import Enum

LONGITUD_MAXIMA_DESCRIPCION = 200


class ErrorDeNegocio(Exception):
    """Error esperado del dominio; su mensaje se muestra tal cual al usuario."""


class ErrorValidacion(ErrorDeNegocio):
    """El dato ingresado no cumple las reglas del dominio."""


class _EnumDeTexto(Enum):
    """Enum cuyo valor es el texto que escribe el usuario en la CLI."""

    @classmethod
    def mensaje_invalido(cls) -> str:
        raise NotImplementedError

    @classmethod
    def desde_texto(cls, texto: str):
        for miembro in cls:
            if miembro.value == texto:
                return miembro
        raise ErrorValidacion(f"{cls.mensaje_invalido()}: {texto}")


class Estado(_EnumDeTexto):
    PENDIENTE = "pendiente"
    EN_PROCESO = "en_proceso"
    RESUELTA = "resuelta"
    RECHAZADA = "rechazada"

    @classmethod
    def mensaje_invalido(cls) -> str:
        return "estado invalido"

    @property
    def es_final(self) -> bool:
        return self in (Estado.RESUELTA, Estado.RECHAZADA)


class Prioridad(_EnumDeTexto):
    ALTA = "alta"
    MEDIA = "media"
    BAJA = "baja"

    @classmethod
    def mensaje_invalido(cls) -> str:
        return "prioridad invalida"

    @property
    def dias_de_resolucion(self) -> int:
        return _DIAS_DE_RESOLUCION[self]

    def calcular_vencimiento(self, fecha: date) -> date:
        return fecha + timedelta(days=self.dias_de_resolucion)


class TipoSolicitud(_EnumDeTexto):
    CERTIFICADO = "certificado"
    CAMBIO_COMISION = "cambio_comision"
    EQUIVALENCIA = "equivalencia"
    RECLAMO_NOTA = "reclamo_nota"

    @classmethod
    def mensaje_invalido(cls) -> str:
        return "tipo de solicitud invalido"

    @property
    def area(self) -> str:
        return _AREA_POR_TIPO[self]


_DIAS_DE_RESOLUCION = {Prioridad.ALTA: 2, Prioridad.MEDIA: 5, Prioridad.BAJA: 10}

_AREA_POR_TIPO = {
    TipoSolicitud.CERTIFICADO: "Bedelia",
    TipoSolicitud.CAMBIO_COMISION: "Bedelia",
    TipoSolicitud.EQUIVALENCIA: "Departamento Academico",
    TipoSolicitud.RECLAMO_NOTA: "Docencia",
}


def validar_descripcion(descripcion: str | None) -> str:
    """Devuelve la descripción normalizada o lanza ErrorValidacion."""
    if descripcion is None or not descripcion.strip():
        raise ErrorValidacion("la descripcion es obligatoria")
    if len(descripcion) > LONGITUD_MAXIMA_DESCRIPCION:
        raise ErrorValidacion(f"la descripcion supera los {LONGITUD_MAXIMA_DESCRIPCION} caracteres")
    return descripcion.strip()


@dataclass(frozen=True)
class DatosRegistro:
    """Introduce Parameter Object: datos de entrada para registrar una solicitud."""

    legajo: str
    tipo: str
    prioridad: str
    descripcion: str
    fecha: str | None = None


@dataclass(frozen=True)
class FiltroSolicitudes:
    """Introduce Parameter Object: criterios combinables de búsqueda."""

    estado: str | None = None
    tipo: str | None = None
    prioridad: str | None = None
    legajo: str | None = None

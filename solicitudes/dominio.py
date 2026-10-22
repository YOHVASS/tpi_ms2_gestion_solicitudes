"""Vocabulario del dominio: estados, prioridades, tipos y objetos parámetro."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from enum import Enum
from typing import ClassVar

LONGITUD_MAXIMA_DESCRIPCION = 200


class ErrorDeNegocio(Exception):
    """Error esperado del dominio; su mensaje se muestra tal cual al usuario."""


class ErrorValidacion(ErrorDeNegocio):
    """El dato ingresado no cumple las reglas del dominio."""


class NoEncontrado(ErrorDeNegocio):
    """La entidad buscada no existe."""


class TransicionInvalida(ErrorDeNegocio):
    """La operación no está permitida en el estado actual de la solicitud."""


class ErrorDeDatos(ErrorDeNegocio):
    """El almacenamiento existe pero no se puede interpretar."""


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


def parsear_fecha(texto: str) -> date:
    try:
        return date.fromisoformat(texto)
    except ValueError:
        raise ErrorValidacion(f"fecha invalida: {texto} (use AAAA-MM-DD)") from None


@dataclass(frozen=True)
class FiltroSolicitudes:
    """Introduce Parameter Object: criterios combinables de búsqueda (ya validados)."""

    estado: Estado | None = None
    tipo: TipoSolicitud | None = None
    prioridad: Prioridad | None = None
    legajo: str | None = None

    CLAVES: ClassVar[tuple[str, ...]] = ("estado", "tipo", "prioridad", "legajo")

    @classmethod
    def desde_texto(cls, criterios: dict[str, str]) -> FiltroSolicitudes:
        desconocidas = set(criterios) - set(cls.CLAVES)
        if desconocidas:
            clave = sorted(desconocidas)[0]
            raise ErrorValidacion(f"filtro desconocido: {clave} (use estado, tipo, prioridad o legajo)")
        return cls(
            estado=_opcional(Estado, criterios.get("estado")),
            tipo=_opcional(TipoSolicitud, criterios.get("tipo")),
            prioridad=_opcional(Prioridad, criterios.get("prioridad")),
            legajo=criterios.get("legajo"),
        )

    def admite(self, solicitud: Solicitud) -> bool:
        criterios = (
            (self.estado, solicitud.estado),
            (self.tipo, solicitud.tipo),
            (self.prioridad, solicitud.prioridad),
            (self.legajo, solicitud.legajo),
        )
        return all(buscado is None or buscado == valor for buscado, valor in criterios)


def _opcional(enum_de_texto: type[_EnumDeTexto], texto: str | None):
    return None if texto is None else enum_de_texto.desde_texto(texto)


@dataclass(frozen=True)
class Estudiante:
    legajo: str
    nombre: str
    email: str
    carrera: str


@dataclass(frozen=True)
class Responsable:
    id: str
    nombre: str
    area: str


@dataclass
class Solicitud:
    """Entidad central. Concentra sus propias reglas de negocio (Move Method)."""

    id: int
    legajo: str
    tipo: TipoSolicitud
    prioridad: Prioridad
    descripcion: str
    estado: Estado
    area: str
    responsable_id: str | None
    fecha: date
    vence: date

    @classmethod
    def nueva(  # noqa: PLR0913, PLR0917 - constructor nombrado de la entidad (ver docs/code-review.md, OBS-07)
        cls,
        id_solicitud: int,
        legajo: str,
        tipo: TipoSolicitud,
        prioridad: Prioridad,
        descripcion: str,
        fecha: date,
    ) -> Solicitud:
        return cls(
            id=id_solicitud,
            legajo=legajo,
            tipo=tipo,
            prioridad=prioridad,
            descripcion=descripcion,
            estado=Estado.PENDIENTE,
            area=tipo.area,
            responsable_id=None,
            fecha=fecha,
            vence=prioridad.calcular_vencimiento(fecha),
        )

    @property
    def cerrada(self) -> bool:
        return self.estado.es_final

    def esta_vencida(self, hoy: date) -> bool:
        return not self.cerrada and self.vence < hoy

    def asignar(self, responsable: Responsable) -> None:
        self._verificar_abierta()
        if responsable.area != self.area:
            raise ErrorValidacion(f"{responsable.nombre} no pertenece al area {self.area}")
        self.responsable_id = responsable.id

    def cambiar_estado(self, nuevo: Estado) -> None:
        self._verificar_abierta()
        if self.estado == Estado.PENDIENTE and nuevo == Estado.RESUELTA:
            raise TransicionInvalida("no se puede resolver una solicitud que no esta en proceso")
        if nuevo == Estado.EN_PROCESO and self.responsable_id is None:
            raise TransicionInvalida(f"la solicitud #{self.id} no tiene responsable asignado")
        if nuevo == self.estado:
            raise TransicionInvalida("la solicitud ya esta en ese estado")
        if nuevo == Estado.PENDIENTE:
            raise TransicionInvalida("no se puede volver a pendiente")
        self.estado = nuevo

    def _verificar_abierta(self) -> None:
        if self.cerrada:
            raise TransicionInvalida(f"la solicitud #{self.id} ya esta cerrada")

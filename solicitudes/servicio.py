"""Casos de uso del sistema (capa de aplicación).

Orquesta dominio, repositorio y notificador. No imprime nada: devuelve
entidades o lanza ErrorDeNegocio (Replace Error Code with Exception).
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import date

from solicitudes.dominio import (
    DatosRegistro,
    ErrorValidacion,
    Estado,
    FiltroSolicitudes,
    NoEncontrado,
    Prioridad,
    Responsable,
    Solicitud,
    TipoSolicitud,
    validar_descripcion,
)
from solicitudes.notificaciones import Notificador
from solicitudes.repositorio import RepositorioSolicitudes


class ServicioSolicitudes:
    def __init__(
        self,
        repositorio: RepositorioSolicitudes,
        notificador: Notificador,
        hoy: Callable[[], date] = date.today,
    ) -> None:
        self._repositorio = repositorio
        self._notificador = notificador
        self._hoy = hoy

    def registrar(self, datos: DatosRegistro) -> Solicitud:
        if self._repositorio.obtener_estudiante(datos.legajo) is None:
            raise ErrorValidacion(f"el legajo {datos.legajo} no existe")
        tipo = TipoSolicitud.desde_texto(datos.tipo)
        prioridad = Prioridad.desde_texto(datos.prioridad)
        descripcion = validar_descripcion(datos.descripcion)
        fecha = self._hoy() if datos.fecha is None else date.fromisoformat(datos.fecha)
        solicitud = Solicitud.nueva(self._repositorio.proximo_id(), datos.legajo, tipo, prioridad,
                                    descripcion, fecha)
        self._repositorio.agregar_solicitud(solicitud)
        return solicitud

    def asignar(self, id_solicitud: int, id_responsable: str) -> Responsable:
        solicitud = self._obtener_solicitud(id_solicitud)
        responsable = self._repositorio.obtener_responsable(id_responsable)
        if responsable is None:
            raise NoEncontrado(f"no existe el responsable {id_responsable}")
        solicitud.asignar(responsable)
        self._repositorio.guardar_solicitud(solicitud)
        return responsable

    def cambiar_estado(self, id_solicitud: int, texto_estado: str) -> Solicitud:
        solicitud = self._obtener_solicitud(id_solicitud)
        solicitud.cambiar_estado(Estado.desde_texto(texto_estado))
        self._repositorio.guardar_solicitud(solicitud)
        estudiante = self._repositorio.obtener_estudiante(solicitud.legajo)
        self._notificador.notificar_cambio_de_estado(estudiante, solicitud)
        return solicitud

    def buscar(self, filtro: FiltroSolicitudes) -> list[Solicitud]:
        return [s for s in self._repositorio.listar_solicitudes() if _cumple(s, filtro)]

    def _obtener_solicitud(self, id_solicitud: int) -> Solicitud:
        solicitud = self._repositorio.obtener_solicitud(id_solicitud)
        if solicitud is None:
            raise NoEncontrado(f"no existe la solicitud #{id_solicitud}")
        return solicitud


def _cumple(solicitud: Solicitud, filtro: FiltroSolicitudes) -> bool:
    criterios = (
        (filtro.estado, solicitud.estado.value, {e.value for e in Estado}),
        (filtro.tipo, solicitud.tipo.value, None),
        (filtro.prioridad, solicitud.prioridad.value, {p.value for p in Prioridad}),
        (filtro.legajo, solicitud.legajo, None),
    )
    for buscado, valor, valores_validos in criterios:
        if buscado is None:
            continue
        if valores_validos is not None and buscado not in valores_validos:
            continue  # comportamiento heredado: un valor desconocido no filtra
        if buscado != valor:
            return False
    return True

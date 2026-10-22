"""Notificaciones al estudiante (DIP: el servicio depende del protocolo)."""

from __future__ import annotations

from typing import Protocol

from solicitudes.dominio import Estudiante, Solicitud


class Notificador(Protocol):
    def notificar_cambio_de_estado(self, estudiante: Estudiante, solicitud: Solicitud) -> None: ...


class NotificadorConsola:
    """Simula el envío de un email mostrándolo por consola."""

    def __init__(self, salida=print) -> None:
        self._salida = salida

    def notificar_cambio_de_estado(self, estudiante: Estudiante, solicitud: Solicitud) -> None:
        self._salida(
            f"[EMAIL a {estudiante.email}] Su solicitud #{solicitud.id} "
            f"cambio a estado: {solicitud.estado.value}"
        )

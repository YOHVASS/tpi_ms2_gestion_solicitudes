"""Reporte de solicitudes.

El cálculo (ResumenSolicitudes) está separado de la presentación. Cada formato
es una estrategia (Replace Conditional with Polymorphism): agregar un formato
nuevo es agregar una clase y registrarla, sin modificar las existentes (OCP).
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import date
from typing import Protocol

from solicitudes.dominio import ErrorValidacion, Estado, Solicitud
from solicitudes.repositorio import ConsultaSolicitudes


@dataclass(frozen=True)
class ResumenSolicitudes:
    total: int
    por_estado: dict[Estado, int]
    vencidas: int
    por_area: dict[str, int]

    @classmethod
    def calcular(cls, solicitudes: list[Solicitud], hoy: date) -> ResumenSolicitudes:
        conteo_estados = Counter(s.estado for s in solicitudes)
        return cls(
            total=len(solicitudes),
            por_estado={estado: conteo_estados[estado] for estado in Estado},
            vencidas=sum(1 for s in solicitudes if s.esta_vencida(hoy)),
            por_area=dict(sorted(Counter(s.area for s in solicitudes).items())),
        )


class FormatoReporte(Protocol):
    def renderizar(self, resumen: ResumenSolicitudes) -> list[str]: ...


class FormatoTexto:
    def renderizar(self, resumen: ResumenSolicitudes) -> list[str]:
        lineas = [
            "=== REPORTE DE SOLICITUDES ===",
            f"Total: {resumen.total}",
            f"Pendientes: {resumen.por_estado[Estado.PENDIENTE]}",
            f"En proceso: {resumen.por_estado[Estado.EN_PROCESO]}",
            f"Resueltas: {resumen.por_estado[Estado.RESUELTA]}",
            f"Rechazadas: {resumen.por_estado[Estado.RECHAZADA]}",
            f"Vencidas sin cerrar: {resumen.vencidas}",
            "Por area:",
        ]
        lineas += [f"  {area}: {cantidad}" for area, cantidad in resumen.por_area.items()]
        return lineas


class FormatoCSV:
    METRICA_POR_ESTADO = {
        Estado.PENDIENTE: "pendientes",
        Estado.EN_PROCESO: "en_proceso",
        Estado.RESUELTA: "resueltas",
        Estado.RECHAZADA: "rechazadas",
    }

    def renderizar(self, resumen: ResumenSolicitudes) -> list[str]:
        lineas = ["metrica,valor", f"total,{resumen.total}"]
        lineas += [
            f"{metrica},{resumen.por_estado[estado]}" for estado, metrica in self.METRICA_POR_ESTADO.items()
        ]
        lineas.append(f"vencidas,{resumen.vencidas}")
        lineas += [f"area:{area},{cantidad}" for area, cantidad in resumen.por_area.items()]
        return lineas


FORMATOS: dict[str, FormatoReporte] = {"texto": FormatoTexto(), "csv": FormatoCSV()}


class GeneradorReporte:
    def __init__(self, consulta: ConsultaSolicitudes, formatos: dict[str, FormatoReporte] | None = None):
        self._consulta = consulta
        self._formatos = FORMATOS if formatos is None else formatos

    def generar(self, nombre_formato: str, hoy: date) -> list[str]:
        formato = self._formatos.get(nombre_formato)
        if formato is None:
            raise ErrorValidacion(f"formato de reporte invalido: {nombre_formato}")
        resumen = ResumenSolicitudes.calcular(self._consulta.listar_solicitudes(), hoy)
        return formato.renderizar(resumen)

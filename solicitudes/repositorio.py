"""Persistencia de solicitudes (Extract Class + DIP).

El servicio depende de los protocolos; las implementaciones concretas son
intercambiables (LSP): RepositorioJSON en producción y RepositorioEnMemoria
en las pruebas. ConsultaSolicitudes es la interfaz mínima de solo lectura
que necesitan los reportes (ISP).
"""

from __future__ import annotations

import json
import os
from datetime import date
from pathlib import Path
from typing import Protocol

from solicitudes.dominio import (
    ErrorDeDatos,
    Estado,
    Estudiante,
    Prioridad,
    Responsable,
    Solicitud,
    TipoSolicitud,
)

# Códigos con los que la versión inicial guardaba estados y prioridades.
# Se conservan para que los datos.json existentes sigan siendo compatibles.
CODIGO_ESTADO = {Estado.PENDIENTE: 0, Estado.EN_PROCESO: 1, Estado.RESUELTA: 2, Estado.RECHAZADA: 3}
CODIGO_PRIORIDAD = {Prioridad.ALTA: 1, Prioridad.MEDIA: 2, Prioridad.BAJA: 3}
_ESTADO_POR_CODIGO = {codigo: estado for estado, codigo in CODIGO_ESTADO.items()}
_PRIORIDAD_POR_CODIGO = {codigo: prioridad for prioridad, codigo in CODIGO_PRIORIDAD.items()}


class ConsultaSolicitudes(Protocol):
    """Operaciones de solo lectura (las únicas que necesita un reporte)."""

    def listar_solicitudes(self) -> list[Solicitud]: ...

    def obtener_responsable(self, id_responsable: str | None) -> Responsable | None: ...


class RepositorioSolicitudes(ConsultaSolicitudes, Protocol):
    """Operaciones completas que usa el servicio de aplicación."""

    def obtener_estudiante(self, legajo: str) -> Estudiante | None: ...

    def obtener_solicitud(self, id_solicitud: int) -> Solicitud | None: ...

    def proximo_id(self) -> int: ...

    def agregar_solicitud(self, solicitud: Solicitud) -> None: ...

    def guardar_solicitud(self, solicitud: Solicitud) -> None: ...


class RepositorioEnMemoria:
    """Implementación en memoria; base de la versión JSON y doble de prueba."""

    def __init__(self, datos: dict | None = None) -> None:
        self._cargar_desde_diccionario(datos or {})

    # --- consultas ---
    def listar_solicitudes(self) -> list[Solicitud]:
        return list(self._solicitudes.values())

    def obtener_responsable(self, id_responsable: str | None) -> Responsable | None:
        return self._responsables.get(id_responsable)

    def obtener_estudiante(self, legajo: str) -> Estudiante | None:
        return self._estudiantes.get(legajo)

    def obtener_solicitud(self, id_solicitud: int) -> Solicitud | None:
        return self._solicitudes.get(id_solicitud)

    def proximo_id(self) -> int:
        return max(self._solicitudes, default=0) + 1

    # --- comandos ---
    def agregar_solicitud(self, solicitud: Solicitud) -> None:
        self._solicitudes[solicitud.id] = solicitud
        self._persistir()

    def guardar_solicitud(self, solicitud: Solicitud) -> None:
        self._solicitudes[solicitud.id] = solicitud
        self._persistir()

    def inicializar(self, datos: dict) -> None:
        self._cargar_desde_diccionario(datos)
        self._persistir()

    # --- detalles internos ---
    def _persistir(self) -> None:
        """En memoria no hay nada que escribir."""

    def _cargar_desde_diccionario(self, datos: dict) -> None:
        self._estudiantes = {e["legajo"]: Estudiante(**e) for e in datos.get("estudiantes", [])}
        self._responsables = {r["id"]: Responsable(**r) for r in datos.get("responsables", [])}
        self._solicitudes = {s["id"]: _solicitud_desde_dict(s) for s in datos.get("solicitudes", [])}

    def _a_diccionario(self) -> dict:
        return {
            "estudiantes": [vars(e) for e in self._estudiantes.values()],
            "responsables": [vars(r) for r in self._responsables.values()],
            "solicitudes": [_solicitud_a_dict(s) for s in self._solicitudes.values()],
        }


class RepositorioJSON(RepositorioEnMemoria):
    """Persiste en un archivo JSON con el mismo formato que la versión inicial."""

    def __init__(self, ruta: Path, *, cargar: bool = True) -> None:
        self._ruta = Path(ruta)
        super().__init__(self._leer_archivo() if cargar else {})

    def _leer_archivo(self) -> dict:
        if not self._ruta.exists():
            return {}
        try:
            return json.loads(self._ruta.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise ErrorDeDatos(
                f"no se pudo leer {self._ruta.name} ({error.__class__.__name__}). "
                "Revise el archivo o regenerelo con 'python app.py init'"
            ) from error

    def _persistir(self) -> None:
        # Escritura atómica: si el proceso se interrumpe, el archivo anterior queda intacto.
        contenido = json.dumps(self._a_diccionario(), indent=2, ensure_ascii=False)
        temporal = self._ruta.with_name(self._ruta.name + ".tmp")
        temporal.write_text(contenido, encoding="utf-8")
        os.replace(temporal, self._ruta)


def _solicitud_desde_dict(datos: dict) -> Solicitud:
    return Solicitud(
        id=datos["id"],
        legajo=datos["legajo"],
        tipo=TipoSolicitud(datos["tipo"]),
        prioridad=_PRIORIDAD_POR_CODIGO[datos["prioridad"]],
        descripcion=datos["descripcion"],
        estado=_ESTADO_POR_CODIGO[datos["estado"]],
        area=datos["area"],
        responsable_id=datos["responsable"],
        fecha=date.fromisoformat(datos["fecha"]),
        vence=date.fromisoformat(datos["vence"]),
    )


def _solicitud_a_dict(solicitud: Solicitud) -> dict:
    return {
        "id": solicitud.id,
        "legajo": solicitud.legajo,
        "tipo": solicitud.tipo.value,
        "prioridad": CODIGO_PRIORIDAD[solicitud.prioridad],
        "descripcion": solicitud.descripcion,
        "estado": CODIGO_ESTADO[solicitud.estado],
        "area": solicitud.area,
        "responsable": solicitud.responsable_id,
        "fecha": solicitud.fecha.isoformat(),
        "vence": solicitud.vence.isoformat(),
    }

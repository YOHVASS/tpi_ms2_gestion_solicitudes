"""Interfaz de línea de comandos (capa de presentación).

Es la única capa que conoce sys.argv y la consola. Cada comando es una función
pequeña registrada en COMANDOS (tabla de despacho en lugar de if/elif).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from solicitudes.dominio import (
    DatosRegistro,
    ErrorDeNegocio,
    ErrorValidacion,
    FiltroSolicitudes,
    Solicitud,
)
from solicitudes.notificaciones import NotificadorConsola
from solicitudes.reportes import GeneradorReporte
from solicitudes.repositorio import ConsultaSolicitudes, RepositorioJSON
from solicitudes.semilla import DATOS_EJEMPLO
from solicitudes.servicio import ServicioSolicitudes

ARCHIVO_DATOS = Path("datos.json")
USO_GENERAL = "uso: python app.py [init|registrar|estado|asignar|buscar|reporte] ..."
EXITO, FALLA = 0, 1

Salida = Callable[[str], None]


@dataclass
class Aplicacion:
    """Dependencias ya construidas que comparten los comandos."""

    repositorio: RepositorioJSON
    servicio: ServicioSolicitudes
    hoy: Callable[[], date]
    salida: Salida


@dataclass(frozen=True)
class Comando:
    ejecutar: Callable[[Aplicacion, list[str]], None]
    argumentos_minimos: int
    uso: str


def _parsear_id(texto: str) -> int:
    if not texto.isdigit():
        raise ErrorValidacion(f"id de solicitud invalido: {texto}")
    return int(texto)


def _parsear_filtros(argumentos: list[str]) -> FiltroSolicitudes:
    criterios = {}
    for argumento in argumentos:
        clave, separador, valor = argumento.partition("=")
        if not separador:
            raise ErrorValidacion(f"filtro invalido: {argumento} (use clave=valor)")
        criterios[clave] = valor
    return FiltroSolicitudes.desde_texto(criterios)


def formatear_fila(solicitud: Solicitud, consulta: ConsultaSolicitudes) -> str:
    responsable = consulta.obtener_responsable(solicitud.responsable_id)
    columnas = [
        f"#{solicitud.id}",
        solicitud.legajo,
        solicitud.tipo.value,
        solicitud.prioridad.value,
        solicitud.estado.value,
        responsable.nombre if responsable else "-",
        solicitud.descripcion,
    ]
    return " | ".join(columnas)


# ---------------------------------------------------------------- comandos


def comando_init(app: Aplicacion, _argumentos: list[str]) -> None:
    app.repositorio.inicializar(DATOS_EJEMPLO)
    app.salida("OK: datos de ejemplo cargados")


def comando_registrar(app: Aplicacion, argumentos: list[str]) -> None:
    legajo, tipo, prioridad, descripcion, *resto = argumentos
    datos = DatosRegistro(legajo, tipo, prioridad, descripcion, fecha=resto[0] if resto else None)
    solicitud = app.servicio.registrar(datos)
    app.salida(f"OK: solicitud #{solicitud.id} registrada (area: {solicitud.area}, vence: {solicitud.vence})")


def comando_estado(app: Aplicacion, argumentos: list[str]) -> None:
    solicitud = app.servicio.cambiar_estado(_parsear_id(argumentos[0]), argumentos[1])
    app.salida(f"OK: solicitud #{solicitud.id} ahora esta {solicitud.estado.value}")


def comando_asignar(app: Aplicacion, argumentos: list[str]) -> None:
    solicitud, responsable = app.servicio.asignar(_parsear_id(argumentos[0]), argumentos[1])
    app.salida(f"OK: solicitud #{solicitud.id} asignada a {responsable.nombre}")


def comando_buscar(app: Aplicacion, argumentos: list[str]) -> None:
    encontradas = app.servicio.buscar(_parsear_filtros(argumentos))
    if not encontradas:
        app.salida("No se encontraron solicitudes")
    for solicitud in encontradas:
        app.salida(formatear_fila(solicitud, app.repositorio))


def comando_reporte(app: Aplicacion, argumentos: list[str]) -> None:
    formato = argumentos[0] if argumentos else "texto"
    for linea in GeneradorReporte(app.repositorio).generar(formato, app.hoy()):
        app.salida(linea)


COMANDOS: dict[str, Comando] = {
    "init": Comando(comando_init, 0, "uso: python app.py init"),
    "registrar": Comando(
        comando_registrar, 4, "uso: python app.py registrar LEGAJO TIPO PRIORIDAD DESCRIPCION [FECHA]"
    ),
    "estado": Comando(comando_estado, 2, "uso: python app.py estado ID ESTADO"),
    "asignar": Comando(comando_asignar, 2, "uso: python app.py asignar ID RESPONSABLE"),
    "buscar": Comando(comando_buscar, 0, "uso: python app.py buscar [clave=valor ...]"),
    "reporte": Comando(comando_reporte, 0, "uso: python app.py reporte [texto|csv]"),
}


# ------------------------------------------------------------ punto de entrada


def construir_aplicacion(nombre_comando: str, salida: Salida, hoy: Callable[[], date]) -> Aplicacion:
    # init regenera el archivo, por eso no necesita (ni debe) leer uno dañado
    repositorio = RepositorioJSON(ARCHIVO_DATOS, cargar=nombre_comando != "init")
    servicio = ServicioSolicitudes(repositorio, NotificadorConsola(salida), hoy)
    return Aplicacion(repositorio, servicio, hoy, salida)


def main(argumentos: list[str], salida: Salida = print, hoy: Callable[[], date] = date.today) -> int:
    if not argumentos:
        salida(USO_GENERAL)
        return FALLA
    nombre, parametros = argumentos[0], argumentos[1:]
    try:
        comando = COMANDOS.get(nombre)
        if comando is None:
            raise ErrorValidacion(f"comando desconocido {nombre}")
        if len(parametros) < comando.argumentos_minimos:
            salida(comando.uso)
            return FALLA
        comando.ejecutar(construir_aplicacion(nombre, salida, hoy), parametros)
    except ErrorDeNegocio as error:
        salida(f"ERROR: {error}")
        return FALLA
    return EXITO

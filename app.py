"""Sistema de Gestión de Solicitudes Académicas: interfaz de línea de comandos."""

import sys
from datetime import date
from pathlib import Path

from solicitudes.dominio import DatosRegistro, ErrorDeNegocio, Estado, FiltroSolicitudes
from solicitudes.notificaciones import NotificadorConsola
from solicitudes.repositorio import RepositorioJSON
from solicitudes.semilla import DATOS_EJEMPLO
from solicitudes.servicio import ServicioSolicitudes

ARCHIVO_DATOS = Path("datos.json")
USO_GENERAL = "uso: python app.py [init|registrar|estado|asignar|buscar|reporte] ..."
USO_REGISTRAR = "uso: python app.py registrar LEGAJO TIPO PRIORIDAD DESCRIPCION [FECHA]"


def formatear_fila(solicitud, repositorio):
    responsable = repositorio.obtener_responsable(solicitud.responsable_id)
    nombre_responsable = responsable.nombre if responsable else "-"
    return " | ".join([f"#{solicitud.id}", solicitud.legajo, solicitud.tipo.value, solicitud.prioridad.value,
                       solicitud.estado.value, nombre_responsable, solicitud.descripcion])


def reporte(repositorio, formato):
    hoy = date.today()
    solicitudes = repositorio.listar_solicitudes()
    por_estado = {estado: sum(1 for s in solicitudes if s.estado == estado) for estado in Estado}
    vencidas = sum(1 for s in solicitudes if s.esta_vencida(hoy))
    por_area = {}
    for solicitud in solicitudes:
        por_area[solicitud.area] = por_area.get(solicitud.area, 0) + 1
    if formato == "texto":
        print("=== REPORTE DE SOLICITUDES ===")
        print(f"Total: {len(solicitudes)}")
        print(f"Pendientes: {por_estado[Estado.PENDIENTE]}")
        print(f"En proceso: {por_estado[Estado.EN_PROCESO]}")
        print(f"Resueltas: {por_estado[Estado.RESUELTA]}")
        print(f"Rechazadas: {por_estado[Estado.RECHAZADA]}")
        print(f"Vencidas sin cerrar: {vencidas}")
        print("Por area:")
        for area in sorted(por_area):
            print(f"  {area}: {por_area[area]}")
    elif formato == "csv":
        print("metrica,valor")
        print(f"total,{len(solicitudes)}")
        print(f"pendientes,{por_estado[Estado.PENDIENTE]}")
        print(f"en_proceso,{por_estado[Estado.EN_PROCESO]}")
        print(f"resueltas,{por_estado[Estado.RESUELTA]}")
        print(f"rechazadas,{por_estado[Estado.RECHAZADA]}")
        print(f"vencidas,{vencidas}")
        for area in sorted(por_area):
            print(f"area:{area},{por_area[area]}")
    else:
        raise ErrorDeNegocio(f"formato de reporte invalido: {formato}")


def ejecutar(argumentos, repositorio, servicio):
    comando = argumentos[0]
    if comando == "init":
        repositorio.inicializar(DATOS_EJEMPLO)
        print("OK: datos de ejemplo cargados")
    elif comando == "registrar":
        if len(argumentos) < 5:
            print(USO_REGISTRAR)
            return 1
        fecha = argumentos[5] if len(argumentos) > 5 else None
        solicitud = servicio.registrar(DatosRegistro(*argumentos[1:5], fecha=fecha))
        print(f"OK: solicitud #{solicitud.id} registrada (area: {solicitud.area}, vence: {solicitud.vence})")
    elif comando == "estado":
        solicitud = servicio.cambiar_estado(int(argumentos[1]), argumentos[2])
        print(f"OK: solicitud #{solicitud.id} ahora esta {solicitud.estado.value}")
    elif comando == "asignar":
        responsable = servicio.asignar(int(argumentos[1]), argumentos[2])
        print(f"OK: solicitud #{argumentos[1]} asignada a {responsable.nombre}")
    elif comando == "buscar":
        filtros = dict(argumento.split("=") for argumento in argumentos[1:])
        encontradas = servicio.buscar(FiltroSolicitudes(**filtros))
        if not encontradas:
            print("No se encontraron solicitudes")
        for solicitud in encontradas:
            print(formatear_fila(solicitud, repositorio))
    elif comando == "reporte":
        reporte(repositorio, argumentos[1] if len(argumentos) > 1 else "texto")
    else:
        raise ErrorDeNegocio(f"comando desconocido {comando}")
    return 0


def main(argumentos):
    if not argumentos:
        print(USO_GENERAL)
        return 1
    repositorio = RepositorioJSON(ARCHIVO_DATOS)
    servicio = ServicioSolicitudes(repositorio, NotificadorConsola())
    try:
        return ejecutar(argumentos, repositorio, servicio)
    except ErrorDeNegocio as error:
        print(f"ERROR: {error}")
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

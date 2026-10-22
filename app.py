# Sistema de Gestion de Solicitudes Academicas
# version 1 - hecho rapido para la demo
import json
import sys
from datetime import date

from solicitudes.dominio import (
    DatosRegistro,
    ErrorValidacion,
    Estado,
    FiltroSolicitudes,
    Prioridad,
    TipoSolicitud,
    validar_descripcion,
)

ARCHIVO = "datos.json"

# Codigos con los que se persisten estados y prioridades en datos.json
CODIGO_ESTADO = {Estado.PENDIENTE: 0, Estado.EN_PROCESO: 1, Estado.RESUELTA: 2, Estado.RECHAZADA: 3}
ESTADO_POR_CODIGO = {codigo: estado for estado, codigo in CODIGO_ESTADO.items()}
CODIGO_PRIORIDAD = {Prioridad.ALTA: 1, Prioridad.MEDIA: 2, Prioridad.BAJA: 3}
PRIORIDAD_POR_CODIGO = {codigo: prioridad for prioridad, codigo in CODIGO_PRIORIDAD.items()}


class Sistema:
    def __init__(self):
        self.d = {"estudiantes": [], "responsables": [], "solicitudes": []}
        try:
            f = open(ARCHIVO, "r", encoding="utf-8")
            self.d = json.load(f)
            f.close()
        except:
            pass  # si no hay archivo arrancamos vacio

    def _guardar(self):
        with open(ARCHIVO, "w", encoding="utf-8") as archivo:
            json.dump(self.d, archivo, indent=2, ensure_ascii=False)

    def _buscar_solicitud(self, id_solicitud):
        for solicitud in self.d["solicitudes"]:
            if solicitud["id"] == int(id_solicitud):
                return solicitud
        return None

    def _buscar_estudiante(self, legajo):
        for estudiante in self.d["estudiantes"]:
            if estudiante["legajo"] == legajo:
                return estudiante
        return None

    def _buscar_responsable(self, id_responsable):
        for responsable in self.d["responsables"]:
            if responsable["id"] == id_responsable:
                return responsable
        return None

    @staticmethod
    def _esta_cerrada(solicitud):
        return ESTADO_POR_CODIGO[solicitud["estado"]].es_final

    def init(self):
        self.d = {
            "estudiantes": [
                {"legajo": "1001", "nombre": "Ana Lopez", "email": "ana.lopez@example.edu", "carrera": "TUP"},
                {"legajo": "1002", "nombre": "Bruno Diaz", "email": "bruno.diaz@example.edu", "carrera": "TUP"},
                {"legajo": "1003", "nombre": "Carla Gomez", "email": "carla.gomez@example.edu", "carrera": "TUPaD"},
            ],
            "responsables": [
                {"id": "R1", "nombre": "Marta Ruiz", "area": "Bedelia"},
                {"id": "R2", "nombre": "Jorge Paz", "area": "Departamento Academico"},
                {"id": "R3", "nombre": "Lucia Sosa", "area": "Docencia"},
            ],
            "solicitudes": [
                {"id": 1, "legajo": "1001", "tipo": "certificado", "prioridad": 2, "descripcion": "Certificado de alumno regular",
                 "estado": 2, "area": "Bedelia", "responsable": "R1", "fecha": "2020-03-01", "vence": "2020-03-06"},
                {"id": 2, "legajo": "1002", "tipo": "equivalencia", "prioridad": 1, "descripcion": "Equivalencia de Programacion I",
                 "estado": 1, "area": "Departamento Academico", "responsable": "R2", "fecha": "2020-03-02", "vence": "2020-03-04"},
                {"id": 3, "legajo": "1003", "tipo": "reclamo_nota", "prioridad": 3, "descripcion": "Revision de nota del parcial 1",
                 "estado": 0, "area": "Docencia", "responsable": None, "fecha": "2099-01-10", "vence": "2099-01-20"},
            ],
        }
        self._guardar()
        print("OK: datos de ejemplo cargados")
        return True

    def registrar(self, datos: DatosRegistro):
        try:
            if self._buscar_estudiante(datos.legajo) is None:
                raise ErrorValidacion("el legajo " + datos.legajo + " no existe")
            tipo = TipoSolicitud.desde_texto(datos.tipo)
            prioridad = Prioridad.desde_texto(datos.prioridad)
            descripcion = validar_descripcion(datos.descripcion)
        except ErrorValidacion as error:
            print("ERROR: " + str(error))
            return -1
        fecha = date.today() if datos.fecha is None else date.fromisoformat(datos.fecha)
        vencimiento = prioridad.calcular_vencimiento(fecha)
        nuevo_id = len(self.d["solicitudes"]) + 1
        solicitud = {"id": nuevo_id, "legajo": datos.legajo, "tipo": tipo.value,
                     "prioridad": CODIGO_PRIORIDAD[prioridad], "descripcion": descripcion,
                     "estado": CODIGO_ESTADO[Estado.PENDIENTE], "area": tipo.area, "responsable": None,
                     "fecha": fecha.isoformat(), "vence": vencimiento.isoformat()}
        self.d["solicitudes"].append(solicitud)
        self._guardar()
        print("OK: solicitud #" + str(nuevo_id) + " registrada (area: " + tipo.area
              + ", vence: " + solicitud["vence"] + ")")
        return nuevo_id

    def cambiar_estado(self, id_solicitud, texto_estado):
        solicitud = self._buscar_solicitud(id_solicitud)
        if solicitud is None:
            print("ERROR: no existe la solicitud #" + str(id_solicitud))
            return False
        try:
            nuevo = Estado.desde_texto(texto_estado)
        except ErrorValidacion as error:
            print("ERROR: " + str(error))
            return False
        actual = ESTADO_POR_CODIGO[solicitud["estado"]]
        # reglas de transicion
        if actual.es_final:
            print("ERROR: la solicitud #" + str(id_solicitud) + " ya esta cerrada")
            return False
        if actual == Estado.PENDIENTE and nuevo == Estado.RESUELTA:
            print("ERROR: no se puede resolver una solicitud que no esta en proceso")
            return False
        if nuevo == Estado.EN_PROCESO and solicitud["responsable"] is None:
            print("ERROR: la solicitud #" + str(id_solicitud) + " no tiene responsable asignado")
            return False
        if nuevo == actual:
            print("ERROR: la solicitud ya esta en ese estado")
            return False
        if nuevo == Estado.PENDIENTE:
            print("ERROR: no se puede volver a pendiente")
            return False
        solicitud["estado"] = CODIGO_ESTADO[nuevo]
        self._guardar()
        # notificar al estudiante
        estudiante = self._buscar_estudiante(solicitud["legajo"])
        print("[EMAIL a " + estudiante["email"] + "] Su solicitud #" + str(solicitud["id"])
              + " cambio a estado: " + nuevo.value)
        print("OK: solicitud #" + str(solicitud["id"]) + " ahora esta " + nuevo.value)
        return True

    def asignar(self, id, resp_id):
        solicitud = self._buscar_solicitud(id)
        if solicitud is None:
            print("ERROR: no existe la solicitud #" + str(id))
            return False
        responsable = self._buscar_responsable(resp_id)
        if responsable is None:
            print("ERROR: no existe el responsable " + resp_id)
            return False
        if self._esta_cerrada(solicitud):
            print("ERROR: la solicitud #" + str(id) + " ya esta cerrada")
            return False
        if responsable["area"] != solicitud["area"]:
            print("ERROR: " + responsable["nombre"] + " no pertenece al area " + solicitud["area"])
            return False
        solicitud["responsable"] = resp_id
        self._guardar()
        print("OK: solicitud #" + str(solicitud["id"]) + " asignada a " + responsable["nombre"])
        return True

    @staticmethod
    def _cumple_filtro(solicitud, filtro: FiltroSolicitudes):
        estado = ESTADO_POR_CODIGO[solicitud["estado"]].value
        prioridad = PRIORIDAD_POR_CODIGO[solicitud["prioridad"]].value
        criterios = (
            (filtro.estado, estado, {e.value for e in Estado}),
            (filtro.tipo, solicitud["tipo"], None),
            (filtro.prioridad, prioridad, {p.value for p in Prioridad}),
            (filtro.legajo, solicitud["legajo"], None),
        )
        for buscado, valor, valores_validos in criterios:
            if buscado is None:
                continue
            if valores_validos is not None and buscado not in valores_validos:
                continue  # comportamiento heredado: un valor desconocido no filtra
            if buscado != valor:
                return False
        return True

    def buscar(self, filtro: FiltroSolicitudes):
        encontradas = [s for s in self.d["solicitudes"] if self._cumple_filtro(s, filtro)]
        if not encontradas:
            print("No se encontraron solicitudes")
        for solicitud in encontradas:
            estado = ESTADO_POR_CODIGO[solicitud["estado"]].value
            prioridad = PRIORIDAD_POR_CODIGO[solicitud["prioridad"]].value
            responsable = self._buscar_responsable(solicitud["responsable"])
            nombre_responsable = responsable["nombre"] if responsable else "-"
            print(" | ".join(["#" + str(solicitud["id"]), solicitud["legajo"], solicitud["tipo"], prioridad,
                              estado, nombre_responsable, solicitud["descripcion"]]))
        return encontradas

    def reporte(self, formato):
        hoy = date.today().isoformat()
        total = len(self.d["solicitudes"])
        pend = 0
        proc = 0
        res = 0
        rech = 0
        venc = 0
        por_area = {}
        for s in self.d["solicitudes"]:
            if s["estado"] == 0:
                pend = pend + 1
            if s["estado"] == 1:
                proc = proc + 1
            if s["estado"] == 2:
                res = res + 1
            if s["estado"] == 3:
                rech = rech + 1
            if s["estado"] in (0, 1) and s["vence"] < hoy:
                venc = venc + 1
            if s["area"] in por_area:
                por_area[s["area"]] = por_area[s["area"]] + 1
            else:
                por_area[s["area"]] = 1
        if formato == "texto":
            print("=== REPORTE DE SOLICITUDES ===")
            print("Total: " + str(total))
            print("Pendientes: " + str(pend))
            print("En proceso: " + str(proc))
            print("Resueltas: " + str(res))
            print("Rechazadas: " + str(rech))
            print("Vencidas sin cerrar: " + str(venc))
            print("Por area:")
            for a in sorted(por_area):
                print("  " + a + ": " + str(por_area[a]))
        elif formato == "csv":
            print("metrica,valor")
            print("total," + str(total))
            print("pendientes," + str(pend))
            print("en_proceso," + str(proc))
            print("resueltas," + str(res))
            print("rechazadas," + str(rech))
            print("vencidas," + str(venc))
            for a in sorted(por_area):
                print("area:" + a + "," + str(por_area[a]))
        else:
            print("ERROR: formato de reporte invalido: " + formato)
            return False
        return True


def main():
    a = sys.argv
    s = Sistema()
    if len(a) < 2:
        print("uso: python app.py [init|registrar|estado|asignar|buscar|reporte] ...")
        sys.exit(1)
    if a[1] == "init":
        r = s.init()
    elif a[1] == "registrar":
        if len(a) < 6:
            print("uso: python app.py registrar LEGAJO TIPO PRIORIDAD DESCRIPCION [FECHA]")
            sys.exit(1)
        f = None
        if len(a) > 6:
            f = a[6]
        r = s.registrar(DatosRegistro(legajo=a[2], tipo=a[3], prioridad=a[4], descripcion=a[5], fecha=f))
    elif a[1] == "estado":
        r = s.cambiar_estado(a[2], a[3])
    elif a[1] == "asignar":
        r = s.asignar(a[2], a[3])
    elif a[1] == "buscar":
        filtros = {"estado": None, "tipo": None, "prioridad": None, "legajo": None}
        for x in a[2:]:
            k, v = x.split("=")
            filtros[k] = v
        r = s.buscar(FiltroSolicitudes(filtros["estado"], filtros["tipo"], filtros["prioridad"], filtros["legajo"]))
    elif a[1] == "reporte":
        fmt = "texto"
        if len(a) > 2:
            fmt = a[2]
        r = s.reporte(fmt)
    else:
        print("ERROR: comando desconocido " + a[1])
        sys.exit(1)
    if r == -1 or r == False:
        sys.exit(1)


if __name__ == "__main__":
    main()

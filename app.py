# Sistema de Gestion de Solicitudes Academicas
# version 1 - hecho rapido para la demo
import json, os, sys
from datetime import datetime, timedelta

ARCHIVO = "datos.json"

# estados: 0=pendiente 1=en proceso 2=resuelta 3=rechazada
# prioridad: 1=alta 2=media 3=baja


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
        return solicitud["estado"] in (2, 3)

    @staticmethod
    def _validar_descripcion(descripcion):
        if descripcion is None or len(descripcion.strip()) == 0:
            return "la descripcion es obligatoria"
        if len(descripcion) > 200:
            return "la descripcion supera los 200 caracteres"
        return None

    @staticmethod
    def _calcular_vencimiento(fecha, prioridad):
        if prioridad == 1:
            return fecha + timedelta(days=2)
        if prioridad == 2:
            return fecha + timedelta(days=5)
        return fecha + timedelta(days=10)

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

    # registra una solicitud nueva
    def registrar(self, legajo, tipo, prioridad, descripcion, fecha_str, canal, observaciones):
        # validar estudiante
        if self._buscar_estudiante(legajo) is None:
            print("ERROR: el legajo " + legajo + " no existe")
            return -1
        # validar tipo y calcular area
        if tipo == "certificado":
            area = "Bedelia"
        elif tipo == "cambio_comision":
            area = "Bedelia"
        elif tipo == "equivalencia":
            area = "Departamento Academico"
        elif tipo == "reclamo_nota":
            area = "Docencia"
        else:
            print("ERROR: tipo de solicitud invalido: " + tipo)
            return -1
        # validar prioridad
        if prioridad == "alta":
            p = 1
        elif prioridad == "media":
            p = 2
        elif prioridad == "baja":
            p = 3
        else:
            print("ERROR: prioridad invalida: " + prioridad)
            return -1
        # validar descripcion
        error = self._validar_descripcion(descripcion)
        if error is not None:
            print("ERROR: " + error)
            return -1
        # fecha
        if fecha_str is None:
            fecha = datetime.now()
        else:
            fecha = datetime.strptime(fecha_str, "%Y-%m-%d")
        # calcular vencimiento segun prioridad
        vence = self._calcular_vencimiento(fecha, p)
        nuevo_id = len(self.d["solicitudes"]) + 1
        s = {"id": nuevo_id, "legajo": legajo, "tipo": tipo, "prioridad": p, "descripcion": descripcion.strip(),
             "estado": 0, "area": area, "responsable": None, "fecha": fecha.strftime("%Y-%m-%d"),
             "vence": vence.strftime("%Y-%m-%d")}
        # canal y observaciones por ahora no se usan
        self.d["solicitudes"].append(s)
        self._guardar()
        print("OK: solicitud #" + str(nuevo_id) + " registrada (area: " + area + ", vence: " + s["vence"] + ")")
        return nuevo_id

    def cambiar_estado(self, id, nuevo):
        solicitud = self._buscar_solicitud(id)
        if solicitud is None:
            print("ERROR: no existe la solicitud #" + str(id))
            return False
        if nuevo == "pendiente":
            n = 0
        elif nuevo == "en_proceso":
            n = 1
        elif nuevo == "resuelta":
            n = 2
        elif nuevo == "rechazada":
            n = 3
        else:
            print("ERROR: estado invalido: " + nuevo)
            return False
        # reglas de transicion
        if self._esta_cerrada(solicitud):
            print("ERROR: la solicitud #" + str(id) + " ya esta cerrada")
            return False
        if solicitud["estado"] == 0 and n == 2:
            print("ERROR: no se puede resolver una solicitud que no esta en proceso")
            return False
        if n == 1 and solicitud["responsable"] is None:
            print("ERROR: la solicitud #" + str(id) + " no tiene responsable asignado")
            return False
        if n == solicitud["estado"]:
            print("ERROR: la solicitud ya esta en ese estado")
            return False
        if n == 0:
            print("ERROR: no se puede volver a pendiente")
            return False
        solicitud["estado"] = n
        self._guardar()
        # notificar al estudiante
        estudiante = self._buscar_estudiante(solicitud["legajo"])
        print("[EMAIL a " + estudiante["email"] + "] Su solicitud #" + str(solicitud["id"])
              + " cambio a estado: " + nuevo)
        print("OK: solicitud #" + str(solicitud["id"]) + " ahora esta " + nuevo)
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

    def buscar(self, estado, tipo, prioridad, legajo):
        l = []
        for s in self.d["solicitudes"]:
            ok = True
            if estado != None:
                if estado == "pendiente" and s["estado"] != 0:
                    ok = False
                if estado == "en_proceso" and s["estado"] != 1:
                    ok = False
                if estado == "resuelta" and s["estado"] != 2:
                    ok = False
                if estado == "rechazada" and s["estado"] != 3:
                    ok = False
            if tipo != None and s["tipo"] != tipo:
                ok = False
            if prioridad != None:
                if prioridad == "alta" and s["prioridad"] != 1:
                    ok = False
                if prioridad == "media" and s["prioridad"] != 2:
                    ok = False
                if prioridad == "baja" and s["prioridad"] != 3:
                    ok = False
            if legajo != None and s["legajo"] != legajo:
                ok = False
            if ok:
                l.append(s)
        if len(l) == 0:
            print("No se encontraron solicitudes")
        for s in l:
            est = ["pendiente", "en_proceso", "resuelta", "rechazada"][s["estado"]]
            pr = ["", "alta", "media", "baja"][s["prioridad"]]
            responsable = self._buscar_responsable(s["responsable"])
            resp = responsable["nombre"] if responsable else "-"
            print("#" + str(s["id"]) + " | " + s["legajo"] + " | " + s["tipo"] + " | " + pr + " | " + est + " | " + resp + " | " + s["descripcion"])
        return l

    def reporte(self, formato):
        hoy = datetime.now().strftime("%Y-%m-%d")
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
        r = s.registrar(a[2], a[3], a[4], a[5], f, "web", "")
    elif a[1] == "estado":
        r = s.cambiar_estado(a[2], a[3])
    elif a[1] == "asignar":
        r = s.asignar(a[2], a[3])
    elif a[1] == "buscar":
        filtros = {"estado": None, "tipo": None, "prioridad": None, "legajo": None}
        for x in a[2:]:
            k, v = x.split("=")
            filtros[k] = v
        r = s.buscar(filtros["estado"], filtros["tipo"], filtros["prioridad"], filtros["legajo"])
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

"""Pruebas de contrato del repositorio.

La misma batería se ejecuta sobre las dos implementaciones: si ambas la pasan,
son sustituibles entre sí (LSP) y el servicio puede depender de la abstracción.
"""

import copy
import json

import pytest

from solicitudes.dominio import ErrorDeDatos, Estado, Prioridad, Solicitud, TipoSolicitud
from solicitudes.repositorio import RepositorioEnMemoria, RepositorioJSON
from solicitudes.semilla import DATOS_EJEMPLO
from tests.conftest import HOY


@pytest.fixture(params=["memoria", "json"])
def repo(request, tmp_path):
    if request.param == "memoria":
        return RepositorioEnMemoria(copy.deepcopy(DATOS_EJEMPLO))
    repositorio = RepositorioJSON(tmp_path / "datos.json", cargar=False)
    repositorio.inicializar(copy.deepcopy(DATOS_EJEMPLO))
    return repositorio


def test_contrato_consultas(repo):
    assert [s.id for s in repo.listar_solicitudes()] == [1, 2, 3]
    assert repo.obtener_estudiante("1001").nombre == "Ana Lopez"
    assert repo.obtener_responsable("R2").area == "Departamento Academico"
    assert repo.obtener_responsable(None) is None
    assert repo.obtener_solicitud(99) is None


def test_contrato_alta_y_modificacion(repo):
    solicitud = Solicitud.nueva(
        repo.proximo_id(), "1002", TipoSolicitud.EQUIVALENCIA, Prioridad.BAJA, "x", HOY
    )
    repo.agregar_solicitud(solicitud)
    solicitud.cambiar_estado(Estado.RECHAZADA)
    repo.guardar_solicitud(solicitud)
    assert repo.obtener_solicitud(4).estado == Estado.RECHAZADA
    assert repo.proximo_id() == 5


def test_json_persiste_con_el_formato_de_la_version_inicial(tmp_path):
    ruta = tmp_path / "datos.json"
    RepositorioJSON(ruta, cargar=False).inicializar(copy.deepcopy(DATOS_EJEMPLO))
    assert json.loads(ruta.read_text(encoding="utf-8")) == DATOS_EJEMPLO


def test_json_relee_lo_que_escribio(tmp_path):
    ruta = tmp_path / "datos.json"
    escritor = RepositorioJSON(ruta, cargar=False)
    escritor.inicializar(copy.deepcopy(DATOS_EJEMPLO))
    escritor.guardar_solicitud(escritor.obtener_solicitud(3))
    assert RepositorioJSON(ruta).obtener_solicitud(3) == escritor.obtener_solicitud(3)


def test_archivo_inexistente_equivale_a_repositorio_vacio(tmp_path):
    assert RepositorioJSON(tmp_path / "no-existe.json").listar_solicitudes() == []


def test_archivo_danado_se_informa_en_lugar_de_silenciarse(tmp_path):
    ruta = tmp_path / "datos.json"
    ruta.write_text('{"estudiantes": [', encoding="utf-8")
    with pytest.raises(ErrorDeDatos, match="no se pudo leer datos.json"):
        RepositorioJSON(ruta)


def test_la_escritura_es_atomica_y_no_deja_temporales(tmp_path, monkeypatch):
    ruta = tmp_path / "datos.json"
    repositorio = RepositorioJSON(ruta, cargar=False)
    repositorio.inicializar(copy.deepcopy(DATOS_EJEMPLO))
    contenido_original = ruta.read_text(encoding="utf-8")

    def corte_de_luz(*_args):
        raise OSError("disco desconectado")

    monkeypatch.setattr("solicitudes.repositorio.os.replace", corte_de_luz)
    with pytest.raises(OSError):
        repositorio.guardar_solicitud(repositorio.obtener_solicitud(3))
    assert ruta.read_text(encoding="utf-8") == contenido_original  # el archivo bueno sigue intacto


def test_no_quedan_archivos_temporales(tmp_path):
    RepositorioJSON(tmp_path / "datos.json", cargar=False).inicializar(copy.deepcopy(DATOS_EJEMPLO))
    assert [p.name for p in tmp_path.iterdir()] == ["datos.json"]

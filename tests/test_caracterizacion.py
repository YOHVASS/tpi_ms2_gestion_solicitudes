"""Prueba de caracterización (golden master).

Ejecuta el escenario completo contra la CLI en un directorio temporal y compara
la salida con la aprobada a partir de la versión inicial (tag `estado-inicial`).
Se ejecuta SIN cambios contra ambas versiones: si pasa, el comportamiento
externo se conservó.

Para regenerar la salida aprobada (solo sobre la versión inicial):
    APROBAR_GOLDEN=1 pytest tests/test_caracterizacion.py
"""

import json
import os
import subprocess
import sys
from pathlib import Path

from tests.escenario import PASOS

RAIZ = Path(__file__).resolve().parent.parent
GOLDEN = Path(__file__).resolve().parent / "golden"


def _ejecutar_escenario(directorio: Path) -> str:
    bloques = []
    for paso in PASOS:
        proceso = subprocess.run(
            [sys.executable, str(RAIZ / "app.py"), *paso],
            cwd=directorio,
            capture_output=True,
            text=True,
            check=False,
        )
        bloques.append(f"$ app.py {' '.join(paso)}\n{proceso.stdout}[exit={proceso.returncode}]\n")
    return "\n".join(bloques)


def test_salida_de_la_cli_coincide_con_golden_master(tmp_path):
    salida = _ejecutar_escenario(tmp_path)
    datos = json.loads((tmp_path / "datos.json").read_text(encoding="utf-8"))

    if os.environ.get("APROBAR_GOLDEN"):
        (GOLDEN / "salida_esperada.txt").write_text(salida, encoding="utf-8")
        (GOLDEN / "datos_esperados.json").write_text(
            json.dumps(datos, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    esperado = (GOLDEN / "salida_esperada.txt").read_text(encoding="utf-8")
    assert salida == esperado


def test_archivo_de_datos_conserva_formato_y_contenido(tmp_path):
    _ejecutar_escenario(tmp_path)
    datos = json.loads((tmp_path / "datos.json").read_text(encoding="utf-8"))
    esperados = json.loads((GOLDEN / "datos_esperados.json").read_text(encoding="utf-8"))
    assert datos == esperados

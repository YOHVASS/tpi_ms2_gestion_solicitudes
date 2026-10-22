import copy
from datetime import date

import pytest

from solicitudes.repositorio import RepositorioEnMemoria
from solicitudes.semilla import DATOS_EJEMPLO

HOY = date(2026, 10, 22)


@pytest.fixture
def repositorio():
    return RepositorioEnMemoria(copy.deepcopy(DATOS_EJEMPLO))

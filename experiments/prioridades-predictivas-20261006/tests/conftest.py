"""Temporales propios con ACL heredada dentro de la fase de Windows."""
from pathlib import Path
from uuid import uuid4
import pytest


@pytest.fixture(autouse=True, scope='session')
def numerical_threads():
    from threadpoolctl import threadpool_limits
    with threadpool_limits(limits=2):
        yield


@pytest.fixture
def tmp_path():
    # pytest 9 crea temporales con permisos privados incompatibles con el sandbox.
    # Conservar ACL heredada; no cambiar permisos ni usar temporales de otro proceso.
    folder = Path(__file__).resolve().parents[1] / 'tmp' / f'test-{uuid4().hex}'
    folder.mkdir(parents=True)
    return folder

"""Temporales con permisos heredados: compatibles con el sandbox de Windows."""
from pathlib import Path
import uuid
import pytest

@pytest.fixture
def tmp_path():
    path=Path(__file__).resolve().parents[1]/'tmp'/('test-'+uuid.uuid4().hex)
    path.mkdir(parents=True)
    return path

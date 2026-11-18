import os
import pytest
from src.app_posventa.config import settings

# Forzar DEV_MODE=true para la ejecución de pruebas unitarias en local y CI/CD
os.environ["DEV_MODE"] = "true"
settings.dev_mode = True

@pytest.fixture(autouse=True)
def enable_test_mode(monkeypatch):
    """
    Fixture autouse que garantiza que settings.dev_mode sea True en todos los tests,
    incluso si el runner de CI/CD no define variables de entorno en .env.
    """
    monkeypatch.setenv("DEV_MODE", "true")
    settings.dev_mode = True
    yield

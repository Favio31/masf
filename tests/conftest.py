"""Fixtures compartidos para la suite de tests (cache y fetcher).
Usa la API de Genspark: FetchCache, get_default_cache(), reset_default_cache().
"""
import sys
from pathlib import Path
import pytest
sys.path.insert(0, str(Path(__file__).parent.parent))

@pytest.fixture(autouse=True)
def isolated_cache(tmp_path, monkeypatch):
    """Redirige el cache default a tmp_path (los tests NUNCA tocan el disco real)."""
    from core import cache as cache_module
    target = tmp_path / "cache"
    monkeypatch.setenv("MASF_CACHE_DIR", str(target))
    cache_module.reset_default_cache()
    yield target
    cache_module.reset_default_cache()

@pytest.fixture
def cache_dir(isolated_cache):
    """Ruta aislada del cache para el test en curso."""
    return isolated_cache

@pytest.fixture
def fetch_result_factory():
    """Fabrica de resultados de fetch_source con content_hash real."""
    import hashlib
    def _make(content: str = "Contenido de prueba " * 20, method: str = "requests"):
        return {
            "content": content,
            "content_hash": hashlib.sha256(content.encode("utf-8")).hexdigest(),
            "retrieved_at": "2026-10-10T00:00:00+00:00",
            "source_url": "https://sportdharma.com/test",
            "method": method,
        }
    return _make

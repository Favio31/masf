"""Fixtures compartidos para la suite de tests (cache y fetcher).
isolated_cache (autouse): TODOS los tests, incluidos los preexistentes
del fetcher, quedan aislados del filesystem real: CACHE_DIR apunta a
tmp_path y las metricas se resetean antes y despues de cada test.
cache_dir: alias explicito para los tests que necesitan la ruta.
fetch_result_factory: fabrica de resultados fetch_source validos.
"""
import sys
from pathlib import Path
import pytest
sys.path.insert(0, str(Path(__file__).parent.parent))
@pytest.fixture(autouse=True)
def isolated_cache(tmp_path, monkeypatch):
    from core import cache
    target = tmp_path / "cache"
    monkeypatch.setattr(cache, "CACHE_DIR", target)
    cache.reset_metrics()
    yield target
    cache.reset_metrics()
@pytest.fixture
def cache_dir(isolated_cache):
    return isolated_cache
@pytest.fixture
def fetch_result_factory():
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

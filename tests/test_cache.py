"""Tests para core/cache.py y su integracion con core/fetcher.py.
Sin red: requests.get y fetch_with_playwright siempre estan mockeados.
El tiempo se controla con un reloj falso (nada de sleep).
"""
import hashlib
import json
import logging
from unittest.mock import MagicMock, patch
import pytest
from core import cache as cache_module
from core.cache import key_for_url, get_cached, store, invalidate, purge_expired, cache_size, metrics, reset_metrics
from core.fetcher import fetch_source
URL = "https://sportdharma.com/articulo"
def make_result(content: str = "Contenido de prueba " * 20, url: str = URL, method: str = "requests") -> dict:
    return {
        "content": content,
        "content_hash": hashlib.sha256(content.encode("utf-8")).hexdigest(),
        "retrieved_at": "2026-10-10T00:00:00+00:00",
        "source_url": url,
        "method": method,
    }
class TestKeyForUrl:
    def test_clave_es_sha256_hex(self):
        url = "https://sportdharma.com/articulo"
        esperado = hashlib.sha256(url.encode("utf-8")).hexdigest()
        assert key_for_url(url) == esperado
    def test_clave_determinista(self):
        assert key_for_url("https://a.com") == key_for_url("https://a.com")
        assert key_for_url("https://a.com/x") != key_for_url("https://a.com/y")
    def test_path_traversal_neutralizado(self):
        url = "https://sportdharma.com/../../etc/passwd"
        path = cache_module._entry_path(key_for_url(url))
        assert path.name.endswith(".json")
        assert set(path.stem) <= set("0123456789abcdef")
        assert "/" not in path.name and "\\" not in path.name
class TestHitMiss:
    def test_miss_si_cache_vacio(self, cache_dir):
        assert get_cached("https://sportdharma.com/a") is None
        assert metrics()["misses"] == 1
    def test_hit_tras_store(self, cache_dir, fetch_result_factory):
        url = "https://sportdharma.com/a"
        resultado = fetch_result_factory()
        assert store(url, resultado) is True
        assert get_cached(url) == resultado
        assert metrics()["hits"] == 1
    def test_resultado_cacheado_es_copia_independiente(self, cache_dir, fetch_result_factory):
        url = "https://sportdharma.com/a"
        store(url, fetch_result_factory())
        copia = get_cached(url)
        copia["content"] = "alterado"
        assert get_cached(url)["content"] != "alterado"
    def test_urls_distintas_no_colisionan(self, cache_dir, fetch_result_factory):
        store("https://sportdharma.com/a", fetch_result_factory("AAA " * 30))
        store("https://sportdharma.com/b", fetch_result_factory("BBB " * 30))
        assert get_cached("https://sportdharma.com/a")["content"] == "AAA " * 30
        assert get_cached("https://sportdharma.com/b")["content"] == "BBB " * 30
class TestTTL:
    def test_ttl_1_seguro_expira(self, cache_dir, fetch_result_factory):
        url = "https://sportdharma.com/ttl"
        t0 = 1_000_000.0
        store(url, fetch_result_factory(), ttl=1, now=t0)
        assert get_cached(url, ttl=1, now=t0 + 0.9) is not None
        assert get_cached(url, ttl=1, now=t0 + 1.0) is None
        assert get_cached(url, ttl=1, now=t0 + 1.1) is None
    def test_ttl_default_24h_no_expira_antes(self, cache_dir, fetch_result_factory):
        url = "https://sportdharma.com/def"
        t0 = 1_000_000.0
        store(url, fetch_result_factory(), now=t0)
        assert get_cached(url, now=t0 + 23 * 3600) is not None
        assert get_cached(url, now=t0 + 24 * 3600 + 1) is None
    def test_ttl_cero_expira_siempre(self, cache_dir, fetch_result_factory):
        url = "https://sportdharma.com/cero"
        t0 = 1_000_000.0
        store(url, fetch_result_factory(), now=t0)
        assert get_cached(url, ttl=0, now=t0) is None
    def test_entrada_expirada_se_elimina_del_disco(self, cache_dir, fetch_result_factory):
        url = "https://sportdharma.com/exp"
        t0 = 1_000_000.0
        store(url, fetch_result_factory(), now=t0)
        get_cached(url, now=t0 + 999_999)
        assert list(cache_dir.glob("*.json")) == []
class TestInvalidacionPorHash:
    def test_cambio_de_hash_se_detecta(self, cache_dir, fetch_result_factory):
        url = "https://sportdharma.com/change"
        store(url, fetch_result_factory("Version 1 " * 30))
        store(url, fetch_result_factory("Version 2 " * 30))
        m = metrics()
        assert m["content_changes"] == 1
        assert get_cached(url)["content"] == "Version 2 " * 30
    def test_mismo_hash_no_cuenta_cambio(self, cache_dir, fetch_result_factory):
        url = "https://sportdharma.com/same"
        store(url, fetch_result_factory())
        store(url, fetch_result_factory())
        assert metrics()["content_changes"] == 0
    def test_invalidate_manual(self, cache_dir, fetch_result_factory):
        url = "https://sportdharma.com/inv"
        store(url, fetch_result_factory())
        assert invalidate(url) is True
        assert get_cached(url) is None
        assert invalidate(url) is False
    def test_entrada_corrupta_se_descarta(self, cache_dir, fetch_result_factory):
        url = "https://sportdharma.com/corrupt"
        store(url, fetch_result_factory())
        path = cache_module._entry_path(key_for_url(url))
        path.write_text("{json roto", encoding="utf-8")
        assert get_cached(url) is None
        assert metrics()["evictions"] >= 1
        assert not path.exists()
class TestEscritura:
    def test_no_guarda_resultados_con_error(self, cache_dir):
        assert store("https://sportdharma.com/err", {"error": "Respuesta muy grande"}) is False
        assert cache_size() == 0
    def test_escritura_atomica_sin_tmp_residuales(self, cache_dir, fetch_result_factory):
        store("https://sportdharma.com/atomic", fetch_result_factory())
        assert [p.name for p in cache_dir.glob("*.tmp")] == []
    def test_url_se_persiste_para_auditoria(self, cache_dir, fetch_result_factory):
        url = "https://sportdharma.com/meta"
        store(url, fetch_result_factory())
        path = cache_module._entry_path(key_for_url(url))
        entry = json.loads(path.read_text(encoding="utf-8"))
        assert entry["url"] == url
        assert entry["content_hash"] == fetch_result_factory()["content_hash"]
class TestMetricas:
    def test_hit_rate_miss_rate(self, cache_dir, fetch_result_factory):
        url = "https://sportdharma.com/rate"
        get_cached(url)
        get_cached(url)
        store(url, fetch_result_factory())
        get_cached(url)
        get_cached(url)
        m = metrics()
        assert m["hits"] == 2 and m["misses"] == 2
        assert m["hit_rate"] == 0.5 and m["miss_rate"] == 0.5
        assert m["writes"] == 1
    def test_hit_rate_90_en_segunda_ejecucion(self, cache_dir, fetch_result_factory):
        urls = [f"https://sportdharma.com/p{i}" for i in range(10)]
        for u in urls:
            store(u, fetch_result_factory())
        reset_metrics()
        for _ in range(2):
            for u in urls:
                get_cached(u)
        assert metrics()["hit_rate"] > 0.9
    def test_size_cuenta_entradas(self, cache_dir, fetch_result_factory):
        assert cache_size() == 0
        for i in range(3):
            store(f"https://sportdharma.com/s{i}", fetch_result_factory())
        assert metrics()["size"] == 3
    def test_reset_metrics(self, cache_dir, fetch_result_factory):
        store("https://sportdharma.com/r", fetch_result_factory())
        get_cached("https://sportdharma.com/r")
        reset_metrics()
        m = metrics()
        assert m["hits"] == 0 and m["misses"] == 0 and m["writes"] == 0
class TestPurgeYRobustez:
    def test_purge_expired_borra_solo_expiradas(self, cache_dir, fetch_result_factory):
        t0 = 1_000_000.0
        store("https://sportdharma.com/old", fetch_result_factory("OLD " * 30), now=t0)
        store("https://sportdharma.com/new", fetch_result_factory("NEW " * 30), now=t0 + 170)
        purged = purge_expired(ttl=50, now=t0 + 200)
        assert purged == 1
        assert get_cached("https://sportdharma.com/old") is None
        assert get_cached("https://sportdharma.com/new", now=t0 + 200) is not None
    def test_store_tolera_cache_dir_inexistente(self, tmp_path, monkeypatch, fetch_result_factory):
        from core import cache
        monkeypatch.setattr(cache, "CACHE_DIR", tmp_path / "aun" / "inexistente")
        reset_metrics()
        assert store("https://sportdharma.com/deep", fetch_result_factory()) is True
class TestIntegracionFetcher:
    @pytest.fixture
    def fetcher(self):
        from core import fetcher
        return fetcher
    @pytest.fixture
    def mock_get(self, monkeypatch, fetch_result_factory):
        from unittest.mock import MagicMock
        import requests as requests_lib
        llamadas = {"n": 0}
        def _fake_get(*args, **kwargs):
            llamadas["n"] += 1
            resp = MagicMock()
            resp.text = "Contenido suficiente para pasar el umbral " * 20
            resp.status_code = 200
            resp.raise_for_status = MagicMock()
            return resp
        monkeypatch.setattr(requests_lib, "get", _fake_get)
        return llamadas
    def test_segunda_llamada_es_hit_sin_request(self, cache_dir, fetcher, mock_get, fetch_result_factory):
        url = "https://sportdharma.com/int"
        r1 = fetcher.fetch_source(url)
        assert r1["method"] == "requests"
        for _ in range(19):
            r2 = fetcher.fetch_source(url)
            assert r2["content"] == r1["content"]
            assert r2["content_hash"] == r1["content_hash"]
        assert mock_get["n"] == 1
        m = metrics()
        assert m["hits"] == 19 and m["misses"] == 1
        assert m["hit_rate"] > 0.9
    def test_use_cache_false_bypasea_cache(self, cache_dir, fetcher, mock_get, fetch_result_factory):
        url = "https://sportdharma.com/nocache"
        fetcher.fetch_source(url, use_cache=False)
        fetcher.fetch_source(url, use_cache=False)
        assert mock_get["n"] == 2
        assert cache_size() == 0
    def test_flag_default_es_true(self, cache_dir, fetcher, mock_get):
        import inspect
        sig = inspect.signature(fetcher.fetch_source)
        assert sig.parameters["use_cache"].default is True
    def test_api_de_fetch_source_no_cambia(self, fetcher):
        claves_contrato = {"content", "content_hash", "retrieved_at", "source_url", "method"}
        claves_error = {"error"}
        r = fetcher.fetch_source("https://dominio-malicioso.com/x")
        assert set(r.keys()) == claves_error
    def test_allowlist_se_aplica_antes_del_cache(self, cache_dir, fetcher, mock_get, fetch_result_factory):
        url_mala = "https://evil.com/contenido"
        store(url_mala, fetch_result_factory())
        r = fetcher.fetch_source(url_mala)
        assert "error" in r
        assert mock_get["n"] == 0
    def test_fallo_de_cache_no_rompe_el_fetch(self, cache_dir, fetcher, mock_get, fetch_result_factory, monkeypatch):
        from core import cache as cache_mod
        def _boom(*a, **k):
            raise OSError("disco lleno")
        monkeypatch.setattr(cache_mod, "store", _boom)
        r = fetcher.fetch_source("https://sportdharma.com/fail")
        assert "error" not in r
        assert r["method"] == "requests"
    def test_contenido_cambiado_actualiza_cache(self, cache_dir, fetcher, monkeypatch, fetch_result_factory):
        import requests as requests_lib
        from unittest.mock import MagicMock
        version = {"v": 1}
        def _fake_get(*args, **kwargs):
            resp = MagicMock()
            resp.text = f"Version {version['v']} del sitio con contenido largo " * 20
            resp.status_code = 200
            resp.raise_for_status = MagicMock()
            return resp
        monkeypatch.setattr(requests_lib, "get", _fake_get)
        url = "https://sportdharma.com/dyn"
        r1 = fetcher.fetch_source(url)
        version["v"] = 2
        r2 = fetcher.fetch_source(url)
        assert r2["content_hash"] == r1["content_hash"]
        invalidate(url)
        r3 = fetcher.fetch_source(url)
        assert r3["content_hash"] != r1["content_hash"]
        assert get_cached(url)["content_hash"] == r3["content_hash"]

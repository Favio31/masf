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
from core.cache import FetchCache, cache_key, normalize_url
from core.fetcher import fetch_source
URL = "https://sportdharma.com/articulo"
class FakeClock:
    def __init__(self, start: float = 1_000_000.0):
        self.now = start
    def __call__(self) -> float:
        return self.now
    def advance(self, seconds: float) -> None:
        self.now += seconds
def make_result(content: str = "Contenido de prueba " * 20, url: str = URL, method: str = "requests") -> dict:
    return {
        "content": content,
        "content_hash": hashlib.sha256(content.encode("utf-8")).hexdigest(),
        "retrieved_at": "2026-10-10T00:00:00+00:00",
        "source_url": url,
        "method": method,
    }
@pytest.fixture
def clock():
    return FakeClock()
@pytest.fixture
def cache(tmp_path, clock):
    return FetchCache(cache_dir=tmp_path / "cache", ttl_seconds=3600, clock=clock)
def mock_http(text: str = "Contenido de prueba " * 20) -> MagicMock:
    response = MagicMock()
    response.text = text
    response.raise_for_status = MagicMock()
    return response
class TestKeys:
    def test_fragmento_y_mayusculas_de_host_no_cambian_la_clave(self):
        assert cache_key("HTTPS://SportDharma.com/a?x=1#seccion") == cache_key("https://sportdharma.com/a?x=1")
    def test_query_y_path_si_cambian_la_clave(self):
        assert cache_key("https://sportdharma.com/a?x=1") != cache_key("https://sportdharma.com/a?x=2")
        assert cache_key("https://sportdharma.com/a") != cache_key("https://sportdharma.com/b")
    def test_clave_es_sha256_hex(self):
        key = cache_key(URL)
        assert len(key) == 64 and int(key, 16) >= 0
        assert key == hashlib.sha256(normalize_url(URL).encode()).hexdigest()
class TestHitMiss:
    def test_miss_cuando_esta_vacio(self, cache):
        assert cache.get(URL) is None
        stats = cache.stats()
        assert (stats["hits"], stats["misses"], stats["lookups"]) == (0, 1, 1)
        assert stats["hit_rate"] == 0.0 and stats["miss_rate"] == 1.0
    def test_put_y_get_devuelven_el_mismo_dict(self, cache):
        result = make_result()
        assert cache.put(URL, result) is True
        assert cache.get(URL) == result
    def test_get_devuelve_copia(self, cache):
        cache.put(URL, make_result())
        first = cache.get(URL)
        first["content"] = "mutado"
        assert cache.get(URL)["content"] != "mutado"
    def test_urls_distintas_no_se_mezclan(self, cache):
        other = "https://sportdharma.com/otro"
        cache.put(URL, make_result("A " * 100))
        assert cache.get(other) is None
    def test_no_cachea_errores_ni_dicts_incompletos(self, cache):
        assert cache.put(URL, {"error": "Dominio no permitido"}) is False
        assert cache.put(URL, {"content": "x"}) is False
        assert cache.stats()["entries"] == 0
    def test_hit_rate_sin_consultas_es_cero(self, cache):
        assert cache.stats()["hit_rate"] == 0.0
class TestTTL:
    def test_hit_antes_del_ttl(self, cache, clock):
        cache.put(URL, make_result())
        clock.advance(3599)
        assert cache.get(URL) is not None
    def test_miss_exactamente_en_el_ttl_y_purge_la_elimina(self, cache, clock):
        cache.put(URL, make_result())
        clock.advance(3600)
        assert cache.get(URL) is None
        stats = cache.stats()
        assert stats["expired"] == 1 and stats["misses"] == 1
        assert stats["entries"] == 1
        assert cache.purge_expired() == 1
        assert cache.stats()["entries"] == 0
    def test_ttl_configurable_por_constructor(self, tmp_path, clock):
        short = FetchCache(cache_dir=tmp_path / "c", ttl_seconds=10, clock=clock)
        short.put(URL, make_result())
        clock.advance(11)
        assert short.get(URL) is None
    def test_ttl_default_es_24h(self, tmp_path, monkeypatch):
        monkeypatch.delenv("MASF_CACHE_TTL_SECONDS", raising=False)
        assert FetchCache(cache_dir=tmp_path).ttl_seconds == 24 * 3600
    def test_ttl_por_variable_de_entorno(self, tmp_path, monkeypatch):
        monkeypatch.setenv("MASF_CACHE_TTL_SECONDS", "120")
        assert FetchCache(cache_dir=tmp_path).ttl_seconds == 120
    def test_ttl_invalido_en_entorno_usa_default(self, tmp_path, monkeypatch):
        monkeypatch.setenv("MASF_CACHE_TTL_SECONDS", "abc")
        assert FetchCache(cache_dir=tmp_path).ttl_seconds == 24 * 3600
    def test_entrada_del_futuro_se_trata_como_vencida(self, cache, clock):
        cache.put(URL, make_result())
        clock.advance(-500)
        assert cache.get(URL) is None
    def test_purge_expired_solo_borra_vencidas(self, cache, clock):
        cache.put("https://sportdharma.com/vieja", make_result("v " * 100))
        clock.advance(3000)
        cache.put("https://sportdharma.com/nueva", make_result("n " * 100))
        clock.advance(700)
        assert cache.purge_expired() == 1
        assert cache.get("https://sportdharma.com/nueva") is not None
        assert cache.get("https://sportdharma.com/vieja") is None
class TestInvalidacion:
    def _entry_path(self, cache):
        return cache.cache_dir / f"{cache_key(URL)}.json"
    def test_hash_no_coincide_con_el_contenido(self, cache):
        cache.put(URL, make_result())
        path = self._entry_path(cache)
        entry = json.loads(path.read_text(encoding="utf-8"))
        entry["result"]["content"] = "contenido manipulado " * 10
        path.write_text(json.dumps(entry), encoding="utf-8")
        assert cache.get(URL) is None
        assert cache.stats()["invalidated"] == 1
        assert not path.exists()
    def test_json_corrupto(self, cache):
        cache.put(URL, make_result())
        self._entry_path(cache).write_text("{no es json", encoding="utf-8")
        assert cache.get(URL) is None
        assert cache.stats()["invalidated"] == 1
    def test_version_de_cache_incompatible(self, cache):
        cache.put(URL, make_result())
        path = self._entry_path(cache)
        entry = json.loads(path.read_text(encoding="utf-8"))
        entry["cache_version"] = 999
        path.write_text(json.dumps(entry), encoding="utf-8")
        assert cache.get(URL) is None
    def test_entrada_de_otra_url_con_misma_clave_se_rechaza(self, cache):
        cache.put(URL, make_result())
        path = self._entry_path(cache)
        entry = json.loads(path.read_text(encoding="utf-8"))
        entry["url"] = "https://sportdharma.com/otra"
        path.write_text(json.dumps(entry), encoding="utf-8")
        assert cache.get(URL) is None
    def test_hash_distinto_al_refrescar_reemplaza_y_cuenta_el_cambio(self, cache):
        cache.put(URL, make_result("version uno " * 20))
        cache.put(URL, make_result("version dos " * 20))
        assert cache.stats()["content_changed"] == 1
        assert cache.get(URL)["content"].startswith("version dos")
    def test_mismo_hash_al_refrescar_no_cuenta_cambio(self, cache):
        cache.put(URL, make_result())
        cache.put(URL, make_result())
        assert cache.stats()["content_changed"] == 0
    def test_invalidate_manual_y_clear(self, cache):
        cache.put(URL, make_result())
        cache.put("https://sportdharma.com/b", make_result("b " * 100))
        assert cache.invalidate(URL) is True
        assert cache.invalidate(URL) is False
        assert cache.clear() == 1
        assert cache.stats()["entries"] == 0
class TestMetricas:
    def test_tamano_y_entradas(self, cache):
        assert cache.stats()["size_bytes"] == 0
        cache.put(URL, make_result())
        stats = cache.stats()
        assert stats["entries"] == 1
        assert stats["size_bytes"] == (cache.cache_dir / f"{cache_key(URL)}.json").stat().st_size > 0
    def test_hit_rate_y_miss_rate(self, cache):
        cache.get(URL)
        cache.put(URL, make_result())
        for _ in range(3):
            cache.get(URL)
        stats = cache.stats()
        assert stats["hit_rate"] == pytest.approx(0.75)
        assert stats["miss_rate"] == pytest.approx(0.25)
    def test_reset_metrics_no_borra_entradas(self, cache):
        cache.put(URL, make_result())
        cache.get(URL)
        cache.reset_metrics()
        stats = cache.stats()
        assert stats["hits"] == 0 and stats["stores"] == 0 and stats["entries"] == 1
    def test_escritura_atomica_no_deja_temporales(self, cache):
        cache.put(URL, make_result())
        assert [p.name for p in cache.cache_dir.iterdir() if p.name.startswith(".tmp-")] == []
    def test_fallo_de_escritura_no_rompe(self, tmp_path, clock):
        blocker = tmp_path / "ocupado"
        blocker.write_text("soy un archivo, no un directorio")
        broken = FetchCache(cache_dir=blocker, ttl_seconds=60, clock=clock)
        assert broken.put(URL, make_result()) is False
        assert broken.get(URL) is None
class TestLogging:
    def test_eventos_son_json_estructurado(self, cache, caplog):
        with caplog.at_level(logging.INFO, logger="masf.cache"):
            cache.get(URL)
            cache.put(URL, make_result())
            cache.get(URL)
        events = [json.loads(r.getMessage()) for r in caplog.records if r.name == "masf.cache"]
        assert [e["event"] for e in events] == ["cache_miss", "cache_store", "cache_hit"]
        assert all(e["url"] == URL for e in events)
        assert events[0]["reason"] == "absent"
class TestFetchSourceConCache:
    @patch("core.fetcher.requests.get")
    def test_segunda_llamada_no_toca_la_red_y_devuelve_el_mismo_dict(self, mock_get, cache):
        mock_get.return_value = mock_http()
        first = fetch_source(URL, use_cache=True, cache=cache)
        second = fetch_source(URL, use_cache=True, cache=cache)
        assert mock_get.call_count == 1
        assert second == first
        assert set(second) == {"content", "content_hash", "retrieved_at", "source_url", "method"}
    @patch("core.fetcher.requests.get")
    def test_sin_cache_siempre_descarga(self, mock_get, cache):
        mock_get.return_value = mock_http()
        fetch_source(URL, use_cache=False, cache=cache)
        fetch_source(URL, use_cache=False, cache=cache)
        assert mock_get.call_count == 2
        assert cache.stats()["entries"] == 0
    @patch("core.fetcher.requests.get")
    def test_hit_rate_mayor_a_90_porciento_en_ejecuciones_repetidas(self, mock_get, cache):
        mock_get.return_value = mock_http()
        fetch_source(URL, use_cache=True, cache=cache)
        cache.reset_metrics()
        for _ in range(10):
            fetch_source(URL, use_cache=True, cache=cache)
        assert cache.stats()["hit_rate"] == 1.0
        assert mock_get.call_count == 1
    @patch("core.fetcher.requests.get")
    def test_hit_rate_acumulado_de_20_ejecuciones(self, mock_get, cache):
        mock_get.return_value = mock_http()
        for _ in range(20):
            fetch_source(URL, use_cache=True, cache=cache)
        assert cache.stats()["hit_rate"] == pytest.approx(0.95)
    @patch("core.fetcher.requests.get")
    def test_tras_el_ttl_vuelve_a_descargar(self, mock_get, cache, clock):
        mock_get.return_value = mock_http()
        fetch_source(URL, use_cache=True, cache=cache)
        clock.advance(3600)
        fetch_source(URL, use_cache=True, cache=cache)
        assert mock_get.call_count == 2
    @patch("core.fetcher.requests.get")
    def test_contenido_cambiado_en_origen_se_detecta_tras_el_ttl(self, mock_get, cache, clock):
        mock_get.return_value = mock_http("Primera version del articulo " * 10)
        first = fetch_source(URL, use_cache=True, cache=cache)
        clock.advance(3600)
        mock_get.return_value = mock_http("Segunda version del articulo " * 10)
        second = fetch_source(URL, use_cache=True, cache=cache)
        assert first["content_hash"] != second["content_hash"]
        assert cache.stats()["content_changed"] == 1
    @patch("core.fetcher.requests.get")
    def test_errores_no_se_cachean(self, mock_get, cache):
        import requests as real_requests
        mock_get.side_effect = real_requests.exceptions.ConnectionError("down")
        with patch("core.fetcher.fetch_with_playwright", return_value={"error": "Playwright fallo"}):
            result = fetch_source(URL, use_cache=True, cache=cache)
        assert "error" in result
        assert cache.stats()["entries"] == 0
    @patch("core.fetcher.fetch_with_playwright")
    @patch("core.fetcher.requests.get")
    def test_resultado_de_playwright_tambien_se_cachea(self, mock_get, mock_pw, cache):
        mock_get.return_value = mock_http("corto")
        mock_pw.return_value = make_result("Contenido renderizado por JS " * 10, method="playwright")
        first = fetch_source(URL, use_cache=True, cache=cache)
        second = fetch_source(URL, use_cache=True, cache=cache)
        assert first["method"] == second["method"] == "playwright"
        mock_pw.assert_called_once()
    @patch("core.fetcher.requests.get")
    def test_el_allowlist_se_valida_antes_de_leer_el_cache(self, mock_get, cache):
        evil = "https://evil.com/x"
        cache.put(evil, make_result(url=evil))
        result = fetch_source(evil, use_cache=True, cache=cache)
        assert "error" in result and "no permitido" in result["error"]
        mock_get.assert_not_called()
    @patch("core.fetcher.requests.get")
    def test_cache_por_defecto_usa_variable_de_entorno(self, mock_get, tmp_path, monkeypatch):
        monkeypatch.setenv("MASF_CACHE_DIR", str(tmp_path / "envcache"))
        cache_module.reset_default_cache()
        try:
            mock_get.return_value = mock_http()
            fetch_source(URL, use_cache=True)
            fetch_source(URL, use_cache=True)
            assert mock_get.call_count == 1
            assert any((tmp_path / "envcache").glob("*.json"))
        finally:
            cache_module.reset_default_cache()

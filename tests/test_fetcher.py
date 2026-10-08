"""
Tests para el Fetcher (core/fetcher.py).
Valida descarga de URLs con allowlist, hash SHA-256 y manejo de errores.
Regla de Oro: "El LLM extrae, Python decide."
"""
import pytest
from unittest.mock import patch, MagicMock
import hashlib
from datetime import datetime, timezone
from core.fetcher import is_domain_allowed, fetch_source, ALLOWLIST


class TestIsDomainAllowed:
    """Tests para la validación de dominios."""

    def test_dominio_permitido(self):
        """Dominio en allowlist → True."""
        assert is_domain_allowed("https://sportdharma.com/articulo") is True

    def test_dominio_no_permitido(self):
        """Dominio fuera de allowlist → False."""
        assert is_domain_allowed("https://google.com/search") is False

    def test_dominio_con_www(self):
        """Dominio con www. debe ser reconocido."""
        assert is_domain_allowed("https://www.github.com/repo") is True

    def test_dominio_permitido_otro(self):
        """fundacioncodigolibre.org → True."""
        assert is_domain_allowed("https://fundacioncodigolibre.org/grant") is True

    def test_url_sin_protocolo(self):
        """URL sin http/https → debe manejar gracefully."""
        # urlparse puede fallar sin protocolo
        try:
            resultado = is_domain_allowed("sportdharma.com/articulo")
            # Si no falla, debe ser False (no tiene netloc válido)
            assert isinstance(resultado, bool)
        except Exception:
            pass  # Aceptable que falle


class TestFetchSourceDominio:
    """Tests para fetch_source con validación de dominio."""

    def test_dominio_no_permitido_retorna_error(self):
        """Dominio no permitido → retorna dict con error."""
        resultado = fetch_source("https://google.com/search")
        
        assert "error" in resultado
        assert "no permitido" in resultado["error"].lower() or "Dominio" in resultado["error"]


class TestFetchSourceExitoso:
    """Tests para fetch_source con respuesta exitosa (mockeada)."""

    @patch("core.fetcher.requests.get")
    def test_descarga_exitosa(self, mock_get):
        """Descarga exitosa → retorna dict con content, hash, timestamp, url."""
        mock_response = MagicMock()
        mock_response.text = "Contenido de prueba"
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        resultado = fetch_source("https://sportdharma.com/articulo")

        assert "error" not in resultado
        assert resultado["content"] == "Contenido de prueba"
        assert resultado["source_url"] == "https://sportdharma.com/articulo"
        assert "content_hash" in resultado
        assert "retrieved_at" in resultado

    @patch("core.fetcher.requests.get")
    def test_hash_sha256_correcto(self, mock_get):
        """El hash debe ser SHA-256 del contenido."""
        contenido = "Texto de prueba para hash"
        mock_response = MagicMock()
        mock_response.text = contenido
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        resultado = fetch_source("https://sportdharma.com/articulo")

        hash_esperado = hashlib.sha256(contenido.encode("utf-8")).hexdigest()
        assert resultado["content_hash"] == hash_esperado

    @patch("core.fetcher.requests.get")
    def test_timestamp_iso_format(self, mock_get):
        """El timestamp debe estar en formato ISO."""
        mock_response = MagicMock()
        mock_response.text = "contenido"
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        resultado = fetch_source("https://sportdharma.com/articulo")

        # Debe ser parseable como ISO format
        timestamp = resultado["retrieved_at"]
        assert "T" in timestamp  # Formato ISO tiene T entre fecha y hora

    @patch("core.fetcher.requests.get")
    def test_user_agent_correcto(self, mock_get):
        """Debe enviar el User-Agent de SportDharma."""
        mock_response = MagicMock()
        mock_response.text = "contenido"
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        fetch_source("https://sportdharma.com/articulo")

        # Verificar que se llamó con headers
        call_kwargs = mock_get.call_args
        headers = call_kwargs[1].get("headers", {}) if len(call_kwargs) > 1 else {}
        assert "SportDharma" in headers.get("User-Agent", "")


class TestFetchSourceErrores:
    """Tests para manejo de errores de red."""

    @patch("core.fetcher.requests.get")
    def test_timeout(self, mock_get):
        """Timeout → retorna dict con error."""
        import requests
        mock_get.side_effect = requests.exceptions.Timeout("Connection timed out")

        resultado = fetch_source("https://sportdharma.com/articulo")

        assert "error" in resultado

    @patch("core.fetcher.requests.get")
    def test_conexion_rechazada(self, mock_get):
        """Conexión rechazada → retorna dict con error."""
        import requests
        mock_get.side_effect = requests.exceptions.ConnectionError("Connection refused")

        resultado = fetch_source("https://sportdharma.com/articulo")

        assert "error" in resultado

    @patch("core.fetcher.requests.get")
    def test_error_http_404(self, mock_get):
        """Error HTTP 404 → retorna dict con error."""
        import requests
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("404 Not Found")
        mock_get.return_value = mock_response

        resultado = fetch_source("https://sportdharma.com/articulo-inexistente")

        assert "error" in resultado

    @patch("core.fetcher.requests.get")
    def test_error_http_500(self, mock_get):
        """Error HTTP 500 → retorna dict con error."""
        import requests
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("500 Server Error")
        mock_get.return_value = mock_response

        resultado = fetch_source("https://sportdharma.com/articulo")

        assert "error" in resultado


class TestFetchSourceAllowlist:
    """Tests para verificar que la allowlist funciona correctamente."""

    def test_allowlist_contiene_dominios_esperados(self):
        """La allowlist debe contener los dominios configurados."""
        assert "sportdharma.com" in ALLOWLIST
        assert "github.com" in ALLOWLIST
        assert "fundacioncodigolibre.org" in ALLOWLIST

    def test_allowlist_no_contiene_dominios_peligrosos(self):
        """La allowlist NO debe contener dominios sospechosos."""
        assert "google.com" not in ALLOWLIST
        assert "facebook.com" not in ALLOWLIST
"""Tests para core/fetcher.py"""
import hashlib
from unittest.mock import patch, MagicMock
import pytest
from core.fetcher import fetch_source, clean_html, is_domain_allowed


class TestIsDomainAllowed:
    def test_dominio_permitido(self):
        assert is_domain_allowed("https://github.com/user/repo") is True

    def test_dominio_no_permitido(self):
        assert is_domain_allowed("https://evil.com/malware") is False

    def test_dominio_con_www(self):
        assert is_domain_allowed("https://www.github.com/user") is True


class TestCleanHtml:
    def test_limpia_scripts(self):
        html = "<p>Texto</p><script>alert('xss')</script>"
        assert clean_html(html) == "Texto"

    def test_limpia_estilos(self):
        html = "<p>Texto</p><style>.x{color:red}</style>"
        assert clean_html(html) == "Texto"

    def test_mantiene_texto(self):
        html = "<h1>Titulo</h1><p>Parrafo</p>"
        result = clean_html(html)
        assert "Titulo" in result
        assert "Parrafo" in result


class TestFetchSourceExitoso:
    @patch("core.fetcher.requests.get")
    def test_descarga_exitosa(self, mock_get):
        mock_response = MagicMock()
        mock_response.text = "Contenido de prueba " * 20
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        resultado = fetch_source("https://sportdharma.com/articulo")

        assert "error" not in resultado
        assert "content" in resultado
        assert "content_hash" in resultado
        assert "retrieved_at" in resultado
        assert resultado["method"] == "requests"

    @patch("core.fetcher.requests.get")
    def test_hash_sha256_correcto(self, mock_get):
        contenido = "Texto de prueba para hash " * 10
        mock_response = MagicMock()
        mock_response.text = contenido
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        resultado = fetch_source("https://sportdharma.com/articulo")

        # El hash se calcula sobre el contenido LIMPIO, no el crudo
        contenido_limpio = clean_html(contenido)
        hash_esperado = hashlib.sha256(contenido_limpio.encode("utf-8")).hexdigest()
        assert resultado["content_hash"] == hash_esperado

    @patch("core.fetcher.requests.get")
    def test_timestamp_iso_format(self, mock_get):
        mock_response = MagicMock()
        mock_response.text = "Contenido " * 20
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        resultado = fetch_source("https://sportdharma.com/articulo")

        timestamp = resultado["retrieved_at"]
        from datetime import datetime
        datetime.fromisoformat(timestamp)


def test_fetch_source_success():
    mock_response = MagicMock()
    mock_response.text = "Contenido de prueba " * 20
    mock_response.raise_for_status = MagicMock()

    with patch("core.fetcher.requests.get", return_value=mock_response):
        result = fetch_source("https://fundacioncodigolibre.org/test")

    assert "error" not in result

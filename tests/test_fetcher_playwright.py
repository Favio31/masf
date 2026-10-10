"""Tests para el fallback a Playwright en core/fetcher.py"""
from unittest.mock import patch, MagicMock
from core.fetcher import fetch_source


class TestPlaywrightFallback:
    """Tests que verifican que Playwright se activa correctamente."""

    @patch("core.fetcher.fetch_with_playwright")
    @patch("core.fetcher.requests.get")
    def test_playwright_activado_por_contenido_corto(self, mock_get, mock_playwright):
        """Si requests devuelve contenido < 150 chars, se activa Playwright."""
        mock_response = MagicMock()
        mock_response.text = "Contenido corto"  # < 150 chars
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        mock_playwright.return_value = {
            "content": "Contenido renderizado por JS",
            "content_hash": "abc123",
            "retrieved_at": "2026-01-01T00:00:00+00:00",
            "source_url": "https://sportdharma.com/test",
            "method": "playwright"
        }

        result = fetch_source("https://sportdharma.com/test")

        mock_playwright.assert_called_once()
        assert result["method"] == "playwright"
        assert result["content"] == "Contenido renderizado por JS"

    @patch("core.fetcher.fetch_with_playwright")
    @patch("core.fetcher.requests.get")
    def test_playwright_activado_por_error_requests(self, mock_get, mock_playwright):
        """Si requests falla, se activa Playwright como fallback."""
        import requests
        mock_get.side_effect = requests.exceptions.ConnectionError("Connection refused")

        mock_playwright.return_value = {
            "content": "Contenido via Playwright",
            "content_hash": "def456",
            "retrieved_at": "2026-01-01T00:00:00+00:00",
            "source_url": "https://sportdharma.com/test",
            "method": "playwright"
        }

        result = fetch_source("https://sportdharma.com/test")

        mock_playwright.assert_called_once()
        assert result["method"] == "playwright"

    @patch("core.fetcher.requests.get")
    def test_requests_suficiente_no_activa_playwright(self, mock_get):
        """Si requests devuelve contenido suficiente, NO se activa Playwright."""
        mock_response = MagicMock()
        mock_response.text = "Contenido suficiente " * 20  # > 150 chars
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = fetch_source("https://sportdharma.com/test")

        assert result["method"] == "requests"
        assert "error" not in result

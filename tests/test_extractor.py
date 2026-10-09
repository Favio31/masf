"""
Tests para el Extractor (core/extractor.py).
Valida la extracción de datos con Ollama usando mocks.
Regla de Oro: "El LLM extrae, Python decide."
"""
import pytest
from unittest.mock import patch, MagicMock
import json
from core.extractor import extract_data


class TestExtractDataPrompt:
    """Tests para verificar que el prompt se construye correctamente."""

    @patch("core.extractor.requests.post")
    def test_prompt_incluye_texto_fuente(self, mock_post):
        """El prompt debe incluir el texto fuente."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"response": '{"campo1": {"value": "test", "quote": "test"}}'}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        extract_data("texto de prueba", ["campo1"])

        # Verificar que se llamó a requests.post
        assert mock_post.called
        # Verificar que el payload contiene el texto fuente
        call_kwargs = mock_post.call_args
        payload = call_kwargs[1]["json"] if "json" in call_kwargs[1] else call_kwargs[0][1]
        assert "texto de prueba" in payload["prompt"]

    @patch("core.extractor.requests.post")
    def test_prompt_incluye_campos_solicitados(self, mock_post):
        """El prompt debe incluir los campos solicitados."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"response": '{"nombre": {"value": "Juan", "quote": "Juan"}}'}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        extract_data("texto", ["nombre", "email"])

        call_kwargs = mock_post.call_args
        payload = call_kwargs[1]["json"] if "json" in call_kwargs[1] else call_kwargs[0][1]
        assert "nombre" in payload["prompt"]
        assert "email" in payload["prompt"]


class TestExtractDataRespuestaValida:
    """Tests para respuestas válidas de Ollama."""

    @patch("core.extractor.requests.post")
    def test_respuesta_json_valida(self, mock_post):
        """Respuesta JSON válida → retorna dict parseado."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "response": '{"nombre": {"value": "Juan", "quote": "Juan es"}}'
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        resultado = extract_data("Juan es un ciclista", ["nombre"])

        assert isinstance(resultado, dict)
        assert "fields" in resultado
        assert "nombre" in resultado["fields"]

    @patch("core.extractor.requests.post")
    def test_respuesta_vacia(self, mock_post):
        """Respuesta vacía → retorna dict vacío o error."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"response": "{}"}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        resultado = extract_data("texto", ["campo"])

        assert isinstance(resultado, dict)


class TestExtractDataErrores:
    """Tests para manejo de errores de red y parsing."""

    @patch("core.extractor.requests.post")
    def test_timeout_de_ollama(self, mock_post):
        """Timeout de Ollama → retorna dict con error."""
        import requests
        mock_post.side_effect = requests.exceptions.Timeout("Connection timed out")

        resultado = extract_data("texto", ["campo"])

        assert "error" in resultado
        assert "timed out" in resultado["error"].lower() or "timeout" in resultado["error"].lower()

    @patch("core.extractor.requests.post")
    def test_ollama_no_disponible(self, mock_post):
        """Ollama no disponible → retorna dict con error."""
        import requests
        mock_post.side_effect = requests.exceptions.ConnectionError("Connection refused")

        resultado = extract_data("texto", ["campo"])

        assert "error" in resultado

    @patch("core.extractor.requests.post")
    def test_json_malformado_en_respuesta(self, mock_post):
        """JSON malformado en respuesta → retorna dict con error."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"response": "esto no es JSON válido{"}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        resultado = extract_data("texto", ["campo"])

        assert "error" in resultado

    @patch("core.extractor.requests.post")
    def test_error_http_500(self, mock_post):
        """Error HTTP 500 → retorna dict con error."""
        import requests
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("500 Server Error")
        mock_post.return_value = mock_response

        resultado = extract_data("texto", ["campo"])

        assert "error" in resultado


class TestExtractDataParametros:
    """Tests para verificar parámetros de la llamada a Ollama."""

    @patch("core.extractor.requests.post")
    def test_temperatura_cero(self, mock_post):
        """La temperatura debe ser 0.0 para determinismo."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"response": "{}"}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        extract_data("texto", ["campo"])

        # Verificar que se llamó a requests.post
        assert mock_post.called

        # Obtener el payload enviado
        call_args = mock_post.call_args
        payload = call_args.kwargs.get("json", {}) if hasattr(call_args, 'kwargs') else call_args[1].get("json", {})

        # Verificar temperatura
        assert payload.get("options", {}).get("temperature") == 0.0
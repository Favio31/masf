from unittest.mock import patch, MagicMock
from core.fetcher import fetch_source, is_domain_allowed

def test_is_domain_allowed_true():
    assert is_domain_allowed("https://fundacioncodigolibre.org/convocatoria") is True

def test_is_domain_allowed_false():
    assert is_domain_allowed("https://dominio-prohibido.com") is False

def test_is_domain_allowed_with_www():
    assert is_domain_allowed("https://www.github.com/repo") is True

def test_fetch_source_success():
    """Simula descarga exitosa."""
    mock_response = MagicMock()
    mock_response.text = "<html>Contenido de prueba</html>"
    mock_response.raise_for_status = MagicMock()
    
    with patch('core.fetcher.requests.get', return_value=mock_response):
        result = fetch_source("https://fundacioncodigolibre.org/test")
    
    assert "error" not in result
    assert result["content"] == "<html>Contenido de prueba</html>"
    assert len(result["content_hash"]) == 64  # SHA-256 hex

def test_fetch_source_blocked_domain():
    """Dominio no permitido debe fallar sin hacer petición."""
    result = fetch_source("https://dominio-prohibido.com/test")
    assert "error" in result
    assert "no permitido" in result["error"]
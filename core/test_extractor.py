from unittest.mock import patch, MagicMock
from core.extractor import extract_data

def test_extract_data_success():
    """Simula que Ollama responde correctamente."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "response": '{"deadline": {"value": "15 marzo", "quote": "plazo: 15 marzo"}}'
    }
    mock_response.raise_for_status = MagicMock()

    with patch('core.extractor.requests.post', return_value=mock_response):
        result = extract_data("texto de prueba", ["deadline"])
        
    assert result["fields"]["deadline"]["value"] == "15 marzo"
    assert result["fields"]["deadline"]["quote"] == "plazo: 15 marzo"

def test_extract_data_error():
    """Simula que Ollama falla o no está corriendo."""
    with patch('core.extractor.requests.post', side_effect=Exception("Conexión rechazada")):
        result = extract_data("texto", ["campo"])
        
    assert "error" in result
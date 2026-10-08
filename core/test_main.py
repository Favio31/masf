from unittest.mock import patch, MagicMock
from core.main import process_source

def test_process_source_end_to_end():
    """Simula el pipeline completo con mocks."""
    # Mock del fetcher
    mock_fetch = {
        "content": "El plazo es el 15 de marzo de 2027. Monto: 50.000 euros.",
        "content_hash": "abc123",
        "retrieved_at": "2026-10-03T12:00:00",
        "source_url": "https://fundacioncodigolibre.org/test"
    }
    
    # Mock del extractor
    mock_extract = {
    "deadline": {"value": "2027-03-15", "quote": "El plazo es el 15 de marzo de 2027"},
    "amount": {"value": "50.000 euros", "quote": "Monto: 50.000 euros"}
}
    
    with patch('core.main.fetch_source', return_value=mock_fetch), \
         patch('core.main.extract_data', return_value=mock_extract):
        
        result = process_source("https://fundacioncodigolibre.org/test", ["deadline", "amount"])
    
    assert "error" not in result
    assert result["source_url"] == "https://fundacioncodigolibre.org/test"
    assert len(result["fields"]) == 2
    
    # Verificar que los campos tienen estado "verified" (las citas coinciden)
    for field in result["fields"]:
        assert field["status"] == "verified"

def test_process_source_fetch_error():
    """Si el fetcher falla, el pipeline debe devolver error."""
    with patch('core.main.fetch_source', return_value={"error": "Dominio no permitido"}):
        result = process_source("https://dominio-prohibido.com", ["campo"])
    
    assert "error" in result
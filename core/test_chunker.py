from core.chunker import chunk_text

def test_chunk_text_small():
    """Texto corto: debe devolver un solo bloque."""
    text = "Este es un texto corto."
    chunks = chunk_text(text, chunk_size=100, overlap=10)
    assert len(chunks) == 1
    assert chunks[0]["text"] == "Este es un texto corto."
    assert chunks[0]["start_offset"] == 0

def test_chunk_text_long():
    """Texto largo: debe dividir en múltiples bloques con solapamiento."""
    text = "palabra " * 500  # ~4000 caracteres
    chunks = chunk_text(text, chunk_size=1000, overlap=100)
    assert len(chunks) > 1
    # Verificar que los offsets son coherentes
    for chunk in chunks:
        assert chunk["start_offset"] >= 0
        assert chunk["end_offset"] > chunk["start_offset"]

def test_chunk_text_empty():
    """Texto vacío: debe devolver lista vacía."""
    assert chunk_text("", chunk_size=100, overlap=10) == []

def test_chunk_offsets_cover_full_text():
    """El primer bloque empieza en 0 y el último cubre el final."""
    text = "a " * 200
    chunks = chunk_text(text, chunk_size=50, overlap=10)
    assert chunks[0]["start_offset"] == 0
    assert chunks[-1]["end_offset"] >= len(text) - 50  # Margen por solapamiento
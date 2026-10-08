"""
Tests para el Chunker (core/chunker.py).
Valida la división de textos largos en bloques con solapamiento.
Regla de Oro: "El LLM extrae, Python decide."
"""
import pytest
from core.chunker import chunk_text


class TestChunkTextBasicos:
    """Tests básicos de división de texto."""

    def test_texto_vacio_retorna_lista_vacia(self):
        """Texto vacío → no debe romper, retorna []."""
        assert chunk_text("") == []

    def test_texto_muy_corto_un_solo_chunk(self):
        """Texto menor a chunk_size → 1 solo chunk."""
        texto = "Este es un texto corto."
        resultado = chunk_text(texto, chunk_size=3000, overlap=300)
        
        assert len(resultado) == 1
        assert resultado[0]["text"] == texto
        assert resultado[0]["start_offset"] == 0
        assert resultado[0]["end_offset"] == len(texto)

    def test_texto_exacto_al_chunk_size(self):
        """Texto exactamente del tamaño del chunk → 1 chunk."""
        texto = "a" * 3000
        resultado = chunk_text(texto, chunk_size=3000, overlap=300)
        
        assert len(resultado) == 1

    def test_texto_largo_genera_multiples_chunks(self):
        """Texto largo → múltiples chunks con solapamiento."""
        texto = "palabra " * 1000  # ~8000 caracteres
        resultado = chunk_text(texto, chunk_size=3000, overlap=300)
        
        assert len(resultado) > 1


class TestChunkOffsets:
    """Tests para verificar que los offsets son correctos y rastreables."""

    def test_primer_chunk_empieza_en_cero(self):
        """El primer chunk siempre empieza en offset 0."""
        texto = "texto de prueba " * 500
        resultado = chunk_text(texto, chunk_size=3000, overlap=300)
        
        assert resultado[0]["start_offset"] == 0

    def test_offsets_cubren_todo_el_texto(self):
        """El último chunk debe llegar hasta el final del texto."""
        texto = "texto de prueba " * 500
        resultado = chunk_text(texto, chunk_size=3000, overlap=300)
        
        ultimo_chunk = resultado[-1]
        assert ultimo_chunk["end_offset"] == len(texto)

    def test_texto_del_chunk_coincide_con_offsets(self):
        """El texto del chunk debe coincidir con text[start:end]."""
        texto = "texto de prueba " * 500
        resultado = chunk_text(texto, chunk_size=3000, overlap=300)
        
        for chunk in resultado:
            texto_esperado = texto[chunk["start_offset"]:chunk["end_offset"]]
            assert chunk["text"] == texto_esperado.strip()


class TestChunkOverlap:
    """Tests para verificar el solapamiento entre chunks."""

    def test_solapamiento_entre_chunks_consecutivos(self):
        """Chunks consecutivos deben solaparse ~overlap caracteres."""
        texto = "palabra " * 2000  # ~16000 caracteres
        resultado = chunk_text(texto, chunk_size=3000, overlap=300)
        
        # Verificar que hay solapamiento entre chunk 0 y chunk 1
        if len(resultado) >= 2:
            fin_chunk_0 = resultado[0]["end_offset"]
            inicio_chunk_1 = resultado[1]["start_offset"]
            solapamiento = fin_chunk_0 - inicio_chunk_1
            
            # El solapamiento debe ser aproximadamente 300 (con tolerancia)
            assert 200 <= solapamiento <= 400


class TestChunkCorteLimpio:
    """Tests para verificar que no corta palabras a la mitad."""

    def test_no_corta_palabras_a_la_mitad(self):
        """Los chunks deben cortarse en espacios o saltos de línea."""
        # Texto con palabras largas y espacios claros
        texto = "primera " * 500 + "segunda " * 500 + "tercera " * 500
        resultado = chunk_text(texto, chunk_size=3000, overlap=300)
        
        for chunk in resultado:
            texto_chunk = chunk["text"]
            # No debe terminar ni empezar con una palabra cortada
            # (excepto el último chunk que puede ser más corto)
            if texto_chunk:
                assert not texto_chunk.startswith(" "), \
                    f"Chunk empieza con espacio: '{texto_chunk[:20]}...'"


class TestChunkParametrosPersonalizados:
    """Tests con parámetros chunk_size y overlap personalizados."""

    def test_chunk_size_pequeno(self):
        """Chunk size pequeño → más chunks."""
        texto = "palabra " * 100  # ~800 caracteres
        resultado_grande = chunk_text(texto, chunk_size=3000, overlap=300)
        resultado_pequeno = chunk_text(texto, chunk_size=200, overlap=50)
        
        assert len(resultado_pequeno) > len(resultado_grande)

    def test_overlap_cero(self):
        """Overlap=0 → chunks sin solapamiento."""
        texto = "palabra " * 500
        resultado = chunk_text(texto, chunk_size=300, overlap=0)
        
        if len(resultado) >= 2:
            fin_chunk_0 = resultado[0]["end_offset"]
            inicio_chunk_1 = resultado[1]["start_offset"]
            assert fin_chunk_0 == inicio_chunk_1, "Con overlap=0 no debe haber solapamiento"
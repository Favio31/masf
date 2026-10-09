"""
Tests para GroundingValidator.
Valida que el sistema rechace valores no respaldados por la cita literal.
Regla de Oro: "El LLM extrae, Python decide."
"""
import pytest
from core.grounding_validator import verify_quote, determine_status


class TestVerifyQuote:
    """Tests para la función verify_quote."""

    def test_cita_exacta_con_valor(self):
        """Cita exacta que contiene el valor → True."""
        chunk = "El monto es de 25.000 USD para el proyecto."
        quote = "El monto es de 25.000 USD"
        value = "25.000 USD"
        assert verify_quote(chunk, quote, value) is True

    def test_cita_sin_valor(self):
        """Cita existe pero no contiene el valor → False."""
        chunk = "El proyecto fue aprobado."
        quote = "El proyecto fue aprobado."
        value = "25.000 USD"
        assert verify_quote(chunk, quote, value) is False

    def test_cita_muy_corta(self):
        """Cita menor al largo mínimo → False."""
        chunk = "El monto es de 25.000 USD."
        quote = "a"
        value = "25.000 USD"
        assert verify_quote(chunk, quote, value, min_len=8) is False

    def test_cita_vacia(self):
        """Cita vacía → False."""
        chunk = "Texto de prueba."
        quote = ""
        value = "valor"
        assert verify_quote(chunk, quote, value) is False

    def test_valor_vacio(self):
        """Valor vacío → False."""
        chunk = "Texto de prueba."
        quote = "Texto de prueba."
        value = ""
        assert verify_quote(chunk, quote, value) is False

    def test_chunk_vacio(self):
        """Chunk vacío → False."""
        chunk = ""
        quote = "Texto"
        value = "Texto"
        assert verify_quote(chunk, quote, value) is False

    def test_normalizacion_unicode(self):
        """Comillas tipográficas y acentos deben normalizarse."""
        chunk = "El monto es de \u201c25.000 USD\u201d según el documento."
        quote = "El monto es de \u201c25.000 USD\u201d"
        value = "25.000 USD"
        assert verify_quote(chunk, quote, value) is True

    def test_fuzzy_match_cercano(self):
        """Paráfrasis cercana con threshold alto → False (no es suficientemente cercano)."""
        chunk = "El presupuesto asignado es de aproximadamente 25.000 dólares."
        quote = "presupuesto asignado es de aproximadamente 25.000 dólares"
        value = "25.000 USD"
        assert verify_quote(chunk, quote, value, threshold=0.95) is False

    def test_cita_con_mayusculas(self):
        """Cita con mayúsculas diferentes → True (normalización)."""
        chunk = "EL MONTO ES DE 25.000 USD."
        quote = "el monto es de 25.000 usd"
        value = "25.000 USD"
        assert verify_quote(chunk, quote, value) is True


class TestDetermineStatus:
    """Tests para determine_status."""

    def test_valor_verificado(self):
        """Valor con cita verificada → verified."""
        assert determine_status(quote_verified=True, value="25.000 USD") == "verified"

    def test_valor_no_verificado(self):
        """Valor sin cita verificada → unverified."""
        assert determine_status(quote_verified=False, value="25.000 USD") == "unverified"

    def test_valor_nulo(self):
        """Valor None → missing."""
        assert determine_status(quote_verified=False, value=None) == "missing"

    def test_valor_vacio(self):
        """Valor vacío → missing."""
        assert determine_status(quote_verified=False, value="") == "missing"

    def test_valor_solo_espacios(self):
        """Valor solo espacios → missing."""
        assert determine_status(quote_verified=False, value="   ") == "missing"


class TestGroundingIntegration:
    """
    Tests de integración: el caso CRÍTICO que detectó Claude.
    Demuestra que el sistema debe rechazar valores alucinados
    incluso cuando la cita es real.
    """

    def test_valor_alucinado_con_cita_real_debe_ser_rechazado(self):
        """
        CASO CRÍTICO: El LLM inventa un monto pero cita texto real.
        El sistema DEBE detectarlo como unverified.
        """
        chunk = "El sponsor XYZ ofrece 5000 USD para proyectos de ciclismo."
        valor_extraido = "10000 USD"
        cita_extraida = "ofrece 5000 USD"
        
        # La cita existe en el chunk
        assert verify_quote(chunk, cita_extraida, "5000 USD") is True
        # Pero el valor alucinado NO está en la cita
        assert verify_quote(chunk, cita_extraida, valor_extraido) is False

    def test_valor_correcto_con_cita_correcta(self):
        """Valor y cita coinciden → verified."""
        chunk = "El sponsor XYZ ofrece 5000 USD para proyectos."
        valor_extraido = "5000 USD"
        cita_extraida = "ofrece 5000 USD"
        
        assert verify_quote(chunk, cita_extraida, valor_extraido) is True
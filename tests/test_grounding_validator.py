"""
Tests para GroundingValidator.
Valida que el sistema rechace valores no respaldados por la cita literal.
Regla de Oro: "El LLM extrae, Python decide."
"""
import pytest
from core.grounding_validator import verify_quote, determine_status


class TestVerifyQuote:
    """Tests para la función verify_quote."""

    def test_cita_exacta_coincide(self):
        """Cita literal presente en el texto → True."""
        texto = "El sponsor XYZ ofrece 5000 USD para proyectos de ciclismo."
        cita = "ofrece 5000 USD"
        assert verify_quote(texto, cita) is True

    def test_cita_no_existe(self):
        """Cita inexistente en el texto → False."""
        texto = "El sponsor XYZ ofrece 5000 USD."
        cita = "esta frase no existe en el texto"
        assert verify_quote(texto, cita) is False

    def test_cita_con_diferente_mayusculas(self):
        """La normalización debe ignorar mayúsculas/minúsculas."""
        texto = "El Sponsor XYZ ofrece 5000 USD."
        cita = "EL SPONSOR XYZ OFRECE"
        assert verify_quote(texto, cita) is True

    def test_entrada_vacia(self):
        """Entradas vacías deben retornar False, no romper el sistema."""
        assert verify_quote("texto", "") is False
        assert verify_quote("", "cita") is False
        assert verify_quote("", "") is False


class TestDetermineStatus:
    """Tests para la función determine_status."""

    def test_cita_verificada_sin_valor(self):
        """Cita verificada pero sin valor → missing."""
        assert determine_status(quote_verified=True, value=None) == "missing"

    def test_cita_verificada_con_valor(self):
        """Cita verificada y con valor → verified."""
        assert determine_status(quote_verified=True, value="5000 USD") == "verified"

    def test_cita_no_verificada(self):
        """Cita no verificada → unverified."""
        assert determine_status(quote_verified=False, value="5000 USD") == "unverified"


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
        texto = "El sponsor XYZ ofrece 5000 USD para proyectos de ciclismo."
        valor_extraido = "10000 USD"
        cita_extraida = "ofrece 5000 USD"
        
        assert verify_quote(texto, cita_extraida) is True
        assert verify_quote(cita_extraida, valor_extraido) is False

    def test_valor_correcto_con_cita_correcta(self):
        """Valor y cita coinciden → verified."""
        texto = "El sponsor XYZ ofrece 5000 USD para proyectos."
        valor_extraido = "5000 USD"
        cita_extraida = "ofrece 5000 USD"
        
        assert verify_quote(texto, cita_extraida) is True
        assert verify_quote(cita_extraida, valor_extraido) is True
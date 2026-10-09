"""
Core grounding validator.
Verifica que las citas extraídas por el LLM existan en el texto fuente
y que el valor extraído esté respaldado por dicha cita.
"""
import unicodedata
import re
from difflib import SequenceMatcher


def _normalize_text(text: str) -> str:
    """Normaliza texto para comparación robusta (NFKC, minúsculas, comillas)."""
    if not text:
        return ""
    text = unicodedata.normalize("NFKC", text).lower()
    text = text.replace("\u201c", '"').replace("\u201d", '"').replace("\u2019", "'")
    return re.sub(r"\s+", " ", text).strip()


def verify_quote(chunk_text: str, quote: str, value: str, min_len: int = 8, threshold: float = 0.95) -> bool:
    """
    Verifica:
    1. Que la cita tenga un largo mínimo (evita falsos positivos con "a" o "1").
    2. Que la cita esté en el chunk de texto.
    3. QUE EL VALOR ESTÉ DENTRO DE LA CITA (Regla de Oro).
    4. Fallback fuzzy match con threshold (para paráfrasis cercanas).
    """
    if not quote or not value or not chunk_text:
        return False
    
    norm_chunk = _normalize_text(chunk_text)
    norm_quote = _normalize_text(quote)
    norm_value = _normalize_text(value)
    
    # 1. Largo mínimo de la cita
    if len(norm_quote) < min_len:
        return False
    
    # 2. La cita debe estar en el chunk
    if norm_quote not in norm_chunk:
        return False
        
    # 3. El valor debe estar dentro de la cita (Corrección crítica C1)
    if norm_value in norm_quote:
        return True
    
    # 4. Fallback fuzzy match (para paráfrasis cercanas)
    ratio = SequenceMatcher(None, norm_value, norm_quote).ratio()
    return ratio >= threshold


def determine_status(quote_verified: bool, value: str = None) -> str:
    """Determina el estado del campo según la verificación."""
    if value is None or str(value).strip() == "":
        return "missing"
    
    if quote_verified:
        return "verified"
    
    return "unverified"
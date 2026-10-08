"""
Core grounding validator.
Verifica que las citas extraídas por el LLM existan en el texto fuente.
"""

def verify_quote(source_text: str, quote: str, threshold: float = 0.95) -> bool:
    """
    Verifica si la cita existe en el texto fuente.
    Usa coincidencia exacta primero, luego fuzzy si está implementado.
    """
    if not quote or not source_text:
        return False
    
    # Normalización básica (minúsculas y espacios)
    norm_source = " ".join(source_text.lower().split())
    norm_quote = " ".join(quote.lower().split())
    
    # Coincidencia exacta
    if norm_quote in norm_source:
        return True
        
    # TODO: Implementar fuzzy match con threshold en el futuro
    return False

def determine_status(quote_verified: bool, value: str = None) -> str:
    """Determina el estado del campo según la verificación."""
    
    # Primero: verificar si hay valor
    if value is None:
        return "missing"
    
    # Segundo: verificar si la cita respalda el valor
    if quote_verified:
        return "verified"
    
    # Tercero: valor existe pero cita no verificada
    return "unverified"
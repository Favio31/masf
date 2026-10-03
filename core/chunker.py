"""
Core chunker.
Divide textos largos en bloques con solapamiento para que quepan en num_ctx.
Conserva offsets para poder rastrear citas al texto original.
"""

def chunk_text(text: str, chunk_size: int = 3000, overlap: int = 300) -> list[dict]:
    """
    Divide el texto en bloques de ~chunk_size caracteres con solapamiento de overlap.
    Devuelve lista de dicts con 'text', 'start_offset', 'end_offset'.
    """
    if not text:
        return []
    
    chunks = []
    start = 0
    text_len = len(text)
    
    while start < text_len:
        end = start + chunk_size
        
        # Si no es el último bloque, buscar un punto de corte limpio (espacio o salto de línea)
        if end < text_len:
            # Buscar el último espacio o salto de línea dentro del rango
            cut_point = text.rfind(' ', start + chunk_size - overlap, end)
            if cut_point == -1:
                cut_point = text.rfind('\n', start + chunk_size - overlap, end)
            if cut_point != -1:
                end = cut_point + 1  # Incluir el espacio/salto
        
        chunk_text = text[start:end].strip()
        
        if chunk_text:
            chunks.append({
                "text": chunk_text,
                "start_offset": start,
                "end_offset": end
            })
        
        # Avanzar: siguiente bloque empieza donde terminó este menos el solapamiento
        start = end - overlap
        if start >= text_len:
            break
    
    return chunks
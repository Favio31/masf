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
        # FIX: Limitar end al tamaño real del texto
        end = min(start + chunk_size, text_len)

        # Si no es el último bloque, buscar un punto de corte limpio
        if end < text_len:
            cut_point = text.rfind(' ', start + chunk_size - overlap, end)
            if cut_point == -1:
                cut_point = text.rfind('\n', start + chunk_size - overlap, end)
            if cut_point != -1:
                end = cut_point + 1

        chunk_text_content = text[start:end].strip()

        # FIX: Solo agregar chunks no vacíos
        if chunk_text_content:
            chunks.append({
                "text": chunk_text_content,
                "start_offset": start,
                "end_offset": end
            })

        # Si llegamos al final del texto, salir
        if end >= text_len:
            break

        # Avanzar con solapamiento
        start = end - overlap

    return chunks
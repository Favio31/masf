"""
Core main.
Orquestador del pipeline: lee fuente, divide en chunks, extrae, valida y devuelve JSON.
"""
from core.fetcher import fetch_source
from core.chunker import chunk_text
from core.extractor import extract_data
from core.grounding_validator import verify_quote, determine_status

def process_source(url: str, fields: list[str]) -> dict:
    """
    Pipeline completo:
    1. Descarga la fuente (fetcher)
    2. Divide en chunks (chunker)
    3. Extrae datos de cada chunk (extractor)
    4. Valida citas (grounding_validator)
    5. Devuelve JSON con estados
    """
    # Paso 1: Descargar
    fetch_result = fetch_source(url)
    if "error" in fetch_result:
        return {"error": fetch_result["error"]}
    
    content = fetch_result["content"]
    
    # Paso 2: Dividir en chunks
    chunks = chunk_text(content, chunk_size=3000, overlap=300)
    
    # Paso 3: Extraer de cada chunk
    all_results = []
    for chunk in chunks:
        extraction = extract_data(chunk["text"], fields)
        if "error" not in extraction:
            # Paso 4: Validar cada campo
            for field, data in extraction.items():
                quote_verified = verify_quote(content, data.get("quote", ""))
                status = determine_status(quote_verified, data.get("value"))
                all_results.append({
                    "field": field,
                    "value": data.get("value"),
                    "quote": data.get("quote"),
                    "status": status,
                    "chunk_offset": chunk["start_offset"]
                })
    
    return {
        "source_url": url,
        "content_hash": fetch_result["content_hash"],
        "fields": all_results
    }
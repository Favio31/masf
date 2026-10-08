"""
Core main.
Orquestador del pipeline: lee fuente, divide en chunks, extrae, valida y guarda en drafts/.
Modelo Human-in-the-Loop: Nada se publica sin aprobación humana.
"""
import argparse
import json
import sys
import hashlib
from pathlib import Path
from datetime import datetime, timezone

from core.fetcher import fetch_source
from core.chunker import chunk_text
from core.extractor import extract_data
from core.grounding_validator import verify_quote, determine_status
from core.schemas import validate_date, validate_email, validate_url

# Directorios de flujo de trabajo
DRAFTS_DIR = Path("drafts")
PUBLISHED_DIR = Path("published")

def ensure_dirs():
    DRAFTS_DIR.mkdir(exist_ok=True)
    PUBLISHED_DIR.mkdir(exist_ok=True)

def process_source(url: str, fields: list[str]) -> dict:
    fetch_result = fetch_source(url)
    if "error" in fetch_result:
        return {"error": fetch_result["error"]}

    content = fetch_result["content"]
    chunks = chunk_text(content, chunk_size=3000, overlap=300)
    
    return _extract_from_chunks(content, chunks, fields, source_url=url)

def process_local_file(filepath: str, fields: list[str]) -> dict:
    path = Path(filepath)
    if not path.exists():
        return {"error": f"Archivo no encontrado: {filepath}"}

    content = path.read_text(encoding="utf-8")
    content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
    chunks = chunk_text(content, chunk_size=3000, overlap=300)
    
    return _extract_from_chunks(content, chunks, fields, source_file=filepath, content_hash=content_hash)

def _extract_from_chunks(content: str, chunks: list, fields: list[str], **metadata) -> dict:
    """Lógica central de extracción y validación."""
    all_results = []
    for chunk in chunks:
        extraction = extract_data(chunk["text"], fields)
        if "error" not in extraction:
            for field, data in extraction.items():
                quote_verified = verify_quote(chunk["text"], data.get("quote", ""), data.get("value", ""))
                status = determine_status(quote_verified, data.get("value"))
                
                field_type = infer_field_type(field)
                if field_type != "text" and data.get("value"):
                    status = validate_field_format(field_type, data.get("value"), status)
                
                all_results.append({
                    "field": field,
                    "value": data.get("value"),
                    "quote": data.get("quote"),
                    "status": status,
                    "field_type": field_type,
                    "chunk_offset": chunk["start_offset"]
                })

    result = {
        "status": "pending_review",
        "human_approved": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "fields": all_results
    }
    result.update(metadata)
    return result

def infer_field_type(field_name: str) -> str:
    field_lower = field_name.lower()
    if any(k in field_lower for k in ["fecha", "date", "deadline"]): return "date"
    if any(k in field_lower for k in ["email", "correo"]): return "email"
    if any(k in field_lower for k in ["url", "website", "link"]): return "url"
    return "text"

def validate_field_format(field_type: str, value: str, current_status: str) -> str:
    if current_status == "missing": return current_status
    is_valid = False
    if field_type == "date": is_valid = validate_date(value)
    elif field_type == "email": is_valid = validate_email(value)
    elif field_type == "url": is_valid = validate_url(value)
    else: return current_status
    
    return current_status if is_valid else "unverified"

def main():
    parser = argparse.ArgumentParser(description="MASF - Pipeline de extracción con revisión humana.")
    parser.add_argument("--input", type=str, help="Ruta a archivo local")
    parser.add_argument("--url", type=str, help="URL de la fuente")
    parser.add_argument("--fields", nargs="+", help="Campos a extraer")
    
    args = parser.parse_args()
    ensure_dirs()

    fields = args.fields or ["nombre", "monto", "fecha", "website", "email"]
    
    if args.input: result = process_local_file(args.input, fields)
    elif args.url: result = process_source(args.url, fields)
    else: parser.print_help(); sys.exit(1)

    if "error" in result:
        print(f"Error: {result['error']}")
        sys.exit(1)

    # Guardar en drafts con ID único basado en timestamp
    draft_id = f"draft_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    draft_path = DRAFTS_DIR / draft_id
    draft_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    
    print(f"✅ Borrador generado: {draft_path}")
    print("⚠️ Pendiente de revisión humana antes de publicar.")

if __name__ == "__main__":
    main()
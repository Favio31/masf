"""
Core main.
Orquestador del pipeline: lee fuente, divide en chunks, extrae, valida y guarda en drafts/.
Modelo Human-in-the-Loop: Nada se publica sin aprobación humana.
Incluye modo Scout para búsqueda autónoma de oportunidades.
Soporta múltiples perfiles: project (profiles/) y client (clients/).
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
from core.searcher import run_scout_profile

# Directorios de flujo de trabajo
DRAFTS_DIR = Path("drafts")
PUBLISHED_DIR = Path("published")


def ensure_dirs():
    """Asegura que existan los directorios de drafts y published."""
    DRAFTS_DIR.mkdir(exist_ok=True)
    PUBLISHED_DIR.mkdir(exist_ok=True)


def process_source(url: str, fields: list[str]) -> dict:
    """Pipeline completo para URL."""
    fetch_result = fetch_source(url)
    if "error" in fetch_result:
        return {"error": fetch_result["error"]}

    content = fetch_result["content"]
    chunks = chunk_text(content, chunk_size=3000, overlap=300)

    return _extract_from_chunks(content, chunks, fields, source_url=url)


def process_local_file(filepath: str, fields: list[str]) -> dict:
    """Pipeline para archivo local (sin fetcher)."""
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

        if "error" in extraction:
            continue

        fields_data = extraction.get("fields", {})

        for field, data in fields_data.items():
            value = data.get("value")
            quote = data.get("quote")

            quote_verified = verify_quote(chunk["text"], quote, value)
            status = determine_status(quote_verified, value)

            field_type = infer_field_type(field)
            if field_type != "text" and value:
                status = validate_field_format(field_type, value, status)

            all_results.append({
                "field": field,
                "value": value,
                "quote": quote,
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
    """Infiere el tipo de campo según su nombre."""
    field_lower = field_name.lower()
    if any(k in field_lower for k in ["fecha", "date", "deadline"]):
        return "date"
    if any(k in field_lower for k in ["email", "correo"]):
        return "email"
    if any(k in field_lower for k in ["url", "website", "link"]):
        return "url"
    return "text"


def validate_field_format(field_type: str, value: str, current_status: str) -> str:
    """Valida formato."""
    if current_status == "missing":
        return current_status

    is_valid = False
    if field_type == "date":
        is_valid = validate_date(value)
    elif field_type == "email":
        is_valid = validate_email(value)
    elif field_type == "url":
        is_valid = validate_url(value)
    else:
        return current_status

    return current_status if is_valid else "unverified"


def main():
    parser = argparse.ArgumentParser(
        description="MASF - Pipeline de extracción con revisión humana y modo Scout."
    )
    parser.add_argument("--input", type=str, help="Ruta a archivo local")
    parser.add_argument("--url", type=str, help="URL de la fuente")
    parser.add_argument("--fields", nargs="+", help="Campos a extraer")
    parser.add_argument("--scout", action="store_true", help="Ejecutar búsqueda de oportunidades")
    parser.add_argument("--profile", type=str, default="sponsors",
                        help="Nombre del perfil (sin _spec.md)")
    parser.add_argument("--type", type=str, default="project", choices=["project", "client"],
                        help="Tipo: 'project' (profiles/) o 'client' (clients/)")

    args = parser.parse_args()
    ensure_dirs()

    # ==========================================
    # MODO SCOUT (Búsqueda autónoma)
    # ==========================================
    if args.scout:
        print(f" Iniciando modo Scout ({args.type})...")
        if args.type == "project":
            profile_path = f"profiles/{args.profile}_spec.md"
        else:
            profile_path = f"clients/{args.profile}_spec.md"
        opportunities = run_scout_profile(profile_path=profile_path, max_results_per_keyword=3)

        if "error" in opportunities[0]:
            print(f"❌ Error en la búsqueda: {opportunities[0]['error']}")
            sys.exit(1)

        scout_result = {
            "status": "pending_review",
            "human_approved": False,
            "type": "scout_search",
            "profile": args.profile,
            "profile_type": args.type,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "opportunities": opportunities
        }

        draft_id = f"draft_scout_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        draft_path = DRAFTS_DIR / draft_id
        draft_path.write_text(json.dumps(scout_result, indent=2, ensure_ascii=False), encoding="utf-8")

        print(f"✅ Borrador de búsqueda generado: {draft_path}")
        print("👉 Revisá los snippets en el archivo y elegí las URLs para extraer.")
        sys.exit(0)

    # ==========================================
    # MODO EXTRACCIÓN TRADICIONAL
    # ==========================================
    fields = args.fields or ["nombre", "monto", "fecha", "website", "email"]

    if args.input:
        result = process_local_file(args.input, fields)
    elif args.url:
        result = process_source(args.url, fields)
    else:
        parser.print_help()
        sys.exit(1)

    if "error" in result:
        print(f"Error: {result['error']}")
        sys.exit(1)

    draft_id = f"draft_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    draft_path = DRAFTS_DIR / draft_id
    draft_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"✅ Borrador generado: {draft_path}")
    print("⚠️ Pendiente de revisión humana antes de publicar.")


if __name__ == "__main__":
    main()
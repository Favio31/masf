"""
Core main.
Orquestador del pipeline: lee fuente, divide en chunks, extrae, valida y devuelve JSON.
Soporta archivos locales (--input) y URLs (--url).
Integra validación de esquemas Pydantic v2 (schemas.py).
"""
import argparse
import json
import sys
import os
import hashlib
import requests
from pathlib import Path
from datetime import datetime, timezone

from core.fetcher import fetch_source
from core.chunker import chunk_text
from core.extractor import extract_data
from core.grounding_validator import verify_quote, determine_status
from core.schemas import SponsorField, SponsorCardPayload, validate_date, validate_email, validate_url


def process_source(url: str, fields: list[str]) -> dict:
    """
    Pipeline completo para URL:
    1. Descarga la fuente (fetcher)
    2. Divide en chunks (chunker)
    3. Extrae datos de cada chunk (extractor)
    4. Valida citas (grounding validator)
    5. Valida formatos (schemas.py)
    6. Devuelve JSON con estados
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
            for field, data in extraction.items():
                quote_verified = verify_quote(content, data.get("quote", ""))
                status = determine_status(quote_verified, data.get("value"))
                
                # Paso 4: Validar formato según tipo de campo
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

    return {
        "source_url": url,
        "content_hash": fetch_result["content_hash"],
        "fields": all_results
    }


def process_local_file(filepath: str, fields: list[str]) -> dict:
    """Pipeline para archivo local (sin fetcher)."""
    path = Path(filepath)
    if not path.exists():
        return {"error": f"Archivo no encontrado: {filepath}"}

    content = path.read_text(encoding="utf-8")
    content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()

    chunks = chunk_text(content, chunk_size=3000, overlap=300)

    all_results = []
    for chunk in chunks:
        extraction = extract_data(chunk["text"], fields)
        if "error" not in extraction:
            for field, data in extraction.items():
                quote_verified = verify_quote(content, data.get("quote", ""))
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

    return {
        "source_file": filepath,
        "content_hash": content_hash,
        "fields": all_results
    }


def infer_field_type(field_name: str) -> str:
    """Infiere el tipo de campo según su nombre."""
    field_lower = field_name.lower()
    if any(k in field_lower for k in ["fecha", "date", "deadline", "vencimiento"]):
        return "date"
    if any(k in field_lower for k in ["email", "correo", "mail"]):
        return "email"
    if any(k in field_lower for k in ["url", "website", "sitio", "enlace", "link"]):
        return "url"
    return "text"


def is_url_live(url: str) -> bool:
    """Verifica que una URL esté viva (no sea un enlace roto / Link Rot)."""
    try:
        # Hacemos un request HEAD rápido (no descarga el contenido, solo verifica que existe)
        response = requests.head(url, timeout=5, allow_redirects=True)
        return response.status_code < 400  # 200, 301, 302 son válidos
    except requests.exceptions.RequestException:
        return False


def validate_field_format(field_type: str, value: str, current_status: str) -> str:
    """Valida formato y, en el caso de URLs, que estén vivas."""
    if current_status == "missing":
        return current_status
    
    is_valid = False
    if field_type == "date":
        is_valid = validate_date(value)
    elif field_type == "email":
        is_valid = validate_email(value)
    elif field_type == "url":
        # Primero validamos el formato, luego que esté viva
        is_valid_format = validate_url(value)
        is_valid = is_valid_format and is_url_live(value)
    else:
        return current_status
    
    if not is_valid:
        return "unverified"
    return current_status


def load_profile(profile_name: str) -> list[str]:
    """Carga los campos desde un perfil en profiles/<name>/spec.md"""
    profile_path = Path(f"profiles/{profile_name}/spec.md")
    if not profile_path.exists():
        return ["nombre", "monto", "fecha", "contacto", "requisitos"]
    
    content = profile_path.read_text(encoding="utf-8")
    fields = []
    for line in content.splitlines():
        if line.startswith("| ") and "|" in line[2:]:
            parts = [p.strip() for p in line.split("|") if p.strip()]
            if parts:
                fields.append(parts[0])
    
    return fields if fields else ["nombre", "monto", "fecha", "contacto", "requisitos"]


def main():
    parser = argparse.ArgumentParser(
        description="MASF - Multi-Agent Swarm Framework. Pipeline de extracción y validación."
    )
    parser.add_argument("--profile", type=str, help="Nombre del perfil (ej: sponsors)")
    parser.add_argument("--input", type=str, help="Ruta a archivo local de texto")
    parser.add_argument("--url", type=str, help="URL de la fuente web (debe estar en allowlist)")
    parser.add_argument("--fields", nargs="+", help="Campos a extraer")
    parser.add_argument("--output", type=str, default=None, help="Archivo de salida JSON")

    args = parser.parse_args()

    if args.profile:
        fields = load_profile(args.profile)
    elif args.fields:
        fields = args.fields
    else:
        fields = ["nombre", "monto", "fecha", "contacto", "requisitos"]

    if args.input:
        result = process_local_file(args.input, fields)
    elif args.url:
        result = process_source(args.url, fields)
    else:
        parser.print_help()
        sys.exit(1)

    output_json = json.dumps(result, indent=2, ensure_ascii=False)
    
    if args.output:
        Path(args.output).write_text(output_json, encoding="utf-8")
        print(f"Resultado guardado en: {args.output}")
    else:
        print(output_json)


if __name__ == "__main__":
    main()
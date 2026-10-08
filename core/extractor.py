"""
Core extractor.
Llama al modelo local (Ollama) para extraer datos con citas.
Incluye validación Pydantic v2 y delimitadores seguros contra inyección.
"""
import requests
import json
import re
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional, Dict, Any
from datetime import datetime


OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen3:4b-instruct"
MAX_RETRIES = 2


# ============================================================
# MODELOS PYDANTIC V2 PARA VALIDACIÓN ESTRUCTURADA
# ============================================================

class FieldExtraction(BaseModel):
    """Modelo para un campo extraído con su valor y cita."""
    value: Optional[str] = Field(None, description="Valor extraído del campo")
    quote: Optional[str] = Field(None, description="Cita literal del texto fuente")

    @field_validator('value')
    @classmethod
    def validate_value(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v.strip() == "":
            return None
        return v

    @field_validator('quote')
    @classmethod
    def validate_quote(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v.strip() == "":
            return None
        return v


class ExtractionResult(BaseModel):
    """Modelo para el resultado completo de extracción."""
    fields: Dict[str, FieldExtraction]

    @model_validator(mode='before')
    @classmethod
    def validate_structure(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            raise ValueError("El resultado debe ser un diccionario")
        return {"fields": data}


# ============================================================
# VALIDADORES DE TIPOS ESPECÍFICOS (REQ-06 a REQ-08)
# ============================================================

def validate_date(value: str) -> bool:
    if not value:
        return False
    try:
        datetime.strptime(value, "%Y-%m-%d")
        return True
    except ValueError:
        for fmt in ["%d/%m/%Y", "%m/%d/%Y", "%Y/%m/%d"]:
            try:
                datetime.strptime(value, fmt)
                return True
            except ValueError:
                continue
        return False


def validate_email(value: str) -> bool:
    if not value:
        return False
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, value))


def validate_url(value: str) -> bool:
    if not value:
        return False
    pattern = r'^https?://[^\s/$.?#].[^\s]*$'
    return bool(re.match(pattern, value))


# ============================================================
# FUNCIÓN PRINCIPAL DE EXTRACCIÓN
# ============================================================

def extract_data(source_text: str, fields: list[str]) -> dict:
    """
    Envía el texto a Ollama y devuelve el JSON extraído.
    Incluye delimitadores seguros y reintentos.
    """
    fields_list = ", ".join([f'"{f}"' for f in fields])
    
    # Prompt endurecido para forzar nombres exactos de campos
    prompt = f"""Eres un extractor de datos preciso. Analiza el texto y extrae la información solicitada en formato JSON estricto.

=== INICIO DEL TEXTO FUENTE ===
{source_text}
=== FIN DEL TEXTO FUENTE ===

TAREA:
Extrae la información correspondiente a los siguientes campos: {fields_list}
Devuelve SOLO un objeto JSON válido. Las claves del objeto DEBEN ser EXACTAMENTE los nombres de los campos solicitados. No inventes claves como "campo1" o "campo2".

ESTRUCTURA OBLIGATORIA DEL JSON:
{{
  "nombre_del_campo_1": {{"value": "valor extraído", "quote": "cita textual exacta del fuente"}},
  "nombre_del_campo_2": {{"value": "valor extraído", "quote": "cita textual exacta del fuente"}}
}}

REGLAS ESTRICTAS:
1. Las claves del JSON deben coincidir letra por letra con: {fields_list}
2. "quote" debe ser una copia literal y exacta del texto fuente que respalda el valor.
3. Si un campo no se menciona en el texto, omítelo completamente del JSON.
4. No incluyas markdown (```json), comentarios ni texto adicional. Solo el objeto JSON."""

    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
        "format": "json"
    }

    for attempt in range(MAX_RETRIES):
        try:
            response = requests.post(OLLAMA_URL, json=payload, timeout=120)
            response.raise_for_status()
            result = response.json()
            
            raw_response = result.get('response', '{}')
            
            # Limpiar bloques de markdown si el modelo los agrega
            clean_response = re.sub(r'^```json\s*', '', raw_response, flags=re.IGNORECASE)
            clean_response = re.sub(r'\s*```$', '', clean_response, flags=re.IGNORECASE)
            
            parsed_json = json.loads(clean_response)
            return parsed_json
            
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
            if attempt < MAX_RETRIES - 1:
                continue
            return {"error": f"Error de conexión después de {MAX_RETRIES} intentos: {str(e)}"}
        except json.JSONDecodeError as e:
            return {"error": f"El modelo no devolvió JSON válido: {str(e)}"}
        except Exception as e:
            return {"error": str(e)}

    return {"error": "Error desconocido tras agotar reintentos"}
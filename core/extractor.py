"""
Core extractor.
Llama al modelo local (Ollama) para extraer datos con citas.
Incluye validación Pydantic v2 como frontera de confianza del output del LLM.
"""
import requests
import json
import re
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict


OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen3:4b-instruct"
MAX_RETRIES = 2


# ============================================================
# MODELOS PYDANTIC V2 - FRONTERA DE CONFIANZA
# ============================================================

class FieldExtraction(BaseModel):
    """Modelo para un campo extraído con su valor y cita."""
    model_config = ConfigDict(extra="forbid")
    
    value: Optional[str] = Field(None, description="Valor extraído del campo")
    quote: Optional[str] = Field(None, description="Cita literal del texto fuente")


class ExtractionResult(BaseModel):
    """Modelo para el resultado completo de extracción."""
    model_config = ConfigDict(extra="forbid")
    
    fields: Dict[str, FieldExtraction]


# ============================================================
# FUNCIÓN PRINCIPAL DE EXTRACCIÓN
# ============================================================

def extract_data(source_text: str, fields: list[str]) -> dict:
    """
    Envía el texto a Ollama y devuelve el JSON validado por Pydantic.
    Incluye delimitadores seguros y reintentos.
    """
    fields_list = ", ".join([f'"{f}"' for f in fields])
    
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
        "format": "json",
        "options": {
            "temperature": 0.0,
            "num_ctx": 8192,
            "seed": 42
        }
    }

    for attempt in range(MAX_RETRIES):
        try:
            response = requests.post(OLLAMA_URL, json=payload, timeout=120)
            response.raise_for_status()
            result = response.json()
            
            raw_response = result.get('response', '{}')
            
            # Limpiar bloques de markdown
            clean_response = re.sub(r'^```json\s*', '', raw_response, flags=re.IGNORECASE)
            clean_response = re.sub(r'\s*```$', '', clean_response, flags=re.IGNORECASE)
            
            parsed_json = json.loads(clean_response)
            
            # VALIDACIÓN PYDANTIC - Frontera de confianza
            validated = ExtractionResult.model_validate({"fields": parsed_json})
            return validated.model_dump()
            
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
            if attempt < MAX_RETRIES - 1:
                continue
            return {"error": f"Error de conexión después de {MAX_RETRIES} intentos: {str(e)}"}
        except (json.JSONDecodeError, Exception) as e:
            if attempt < MAX_RETRIES - 1:
                continue
            return {"error": f"El modelo no devolvió JSON válido: {str(e)}"}

    return {"error": "Error desconocido tras agotar reintentos"}
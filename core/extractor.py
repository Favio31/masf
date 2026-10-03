"""
Core extractor.
Llama al modelo local (Ollama) para extraer datos con citas.
"""
import requests
import json

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen3:4b-instruct"

def extract_data(source_text: str, fields: list[str]) -> dict:
    """
    Envía el texto a Ollama y devuelve el JSON extraído.
    """
    prompt = f"""Eres un extractor de datos. Analiza el siguiente texto y extrae la información solicitada en formato JSON estricto, sin markdown, sin explicaciones.

TEXTO FUENTE:
"{source_text}"

TAREA:
Extrae los siguientes campos: {', '.join(fields)}. Devuelve SOLO este JSON:
{{
  "campo1": {{"value": "...", "quote": "..."}},
  "campo2": {{"value": "...", "quote": "..."}}
}}
"""

    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.0,
            "num_ctx": 8192
        }
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=120)
        response.raise_for_status()
        result = response.json()
        # Ollama devuelve el JSON como string en 'response', hay que parsearlo
        return json.loads(result['response'])
    except Exception as e:
        return {"error": str(e)}
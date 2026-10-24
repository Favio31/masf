#!/usr/bin/env python3
"""
translate.py — Script puente para perfil Translator (MASF v4.3)
Arquitectura: Dos cuerpos (Core genérico + Perfiles específicos).
Assisted-by: Qwen via Chat
Prompts-log: Creación de script puente que usa API local de Ollama respetando los 6 temas de esencia.
Reviewed-by: Favio
"""
import sys
import json
import requests
import re

TARGET_LANGS = ['en', 'fr', 'pt', 'de']
MODEL = 'qwen3:4b-instruct'
OLLAMA_URL = "http://localhost:11434/api/generate"

SYSTEM_PROMPT = """Actúa como traductor experto en deportes outdoor, software libre, salud, espiritualidad budista, viajes y educación.
Traduce del español al idioma objetivo manteniendo el tono resiliente y soberano.
REGLAS ABSOLUTAS:
1. NUNCA uses "Edge AI" ni "Inteligencia Artificial en el borde".
2. Respeta el glosario: Cicloturismo=Cycle touring, Software libre=Free software, Offline-first=Offline-first.
3. Devuelve SOLO un objeto JSON válido con esta estructura exacta:
{"translations": {"clave_ejemplo": "valor traducido"}, "grounding_notes": ["nota de justificación 1", "nota 2"]}
"""

def translate_text(text: str, target_lang: str) -> dict:
    # Limitamos a 2500 chars para la prueba inicial para ser rápidos y frugales (Pilar Ecológico)
    clean_text = re.sub(r'<[^>]+>', ' ', text)[:2500].strip()
    
    payload = {
        "model": MODEL,
        "prompt": f"Idioma objetivo: {target_lang}\n\nTexto fuente:\n{clean_text}\n\nTraduce respetando las reglas. Devuelve SOLO JSON válido.",
        "system": SYSTEM_PROMPT,
        "stream": False,
        "options": {"temperature": 0.0, "num_ctx": 8192}
    }
    
    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=120)
        response.raise_for_status()
        raw_text = response.json().get("response", "{}").strip()
        # Limpieza de markdown por si el LLM lo añade
        raw_text = re.sub(r'^```json\s*', '', raw_text, flags=re.MULTILINE)
        raw_text = re.sub(r'\s*```$', '', raw_text, flags=re.MULTILINE)
        return json.loads(raw_text)
    except Exception as e:
        return {"error": str(e), "raw_response": raw_text if 'raw_text' in locals() else ""}

def main():
    if len(sys.argv) < 3:
        print("Uso: python translate.py <texto_o_url> <nombre_pagina>")
        print("Ejemplo: python translate.py \"Hola mundo\" fundador")
        sys.exit(1)
    
    source_input = sys.argv[1]
    page_name = sys.argv[2]
    
    print(f"\n{'='*60}")
    print(f"📄 Procesando perfil Translator para: {page_name}")
    print(f"{'='*60}")
    
    # Si es URL, intentamos un fetch simple (simulando core/fetcher.py)
    if source_input.startswith("http"):
        print("⬇️  Extrayendo contenido de la URL...")
        try:
            headers = {"User-Agent": "MASF-Translator/4.3 (Local-First)"}
            source_text = requests.get(source_input, headers=headers, timeout=10).text
        except Exception as e:
            print(f"❌ Error al extraer URL: {e}")
            sys.exit(1)
    else:
        source_text = source_input

    for lang in TARGET_LANGS:
        print(f"\n🌐 Traduciendo a {lang.upper()}...")
        result = translate_text(source_text, lang)
        
        output = {
            "page": page_name,
            "source_lang": "es",
            "target_lang": lang,
            "model": MODEL,
            "result": result,
            "status": "needs_human_review"
        }
        
        output_file = f"translations/output/{page_name}_{lang}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        print(f"✅ Guardado: {output_file}")

if __name__ == '__main__':
    main()
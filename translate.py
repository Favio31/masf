#!/usr/bin/env python3
"""
translate.py — Script puente para traducción MASF
Usa el Core genérico (fetcher + extractor) sin modificarlo.
"""
import sys
import json
import os
sys.path.insert(0, os.path.dirname(__file__))

from core.fetcher import fetch_url
from core.extractor import extract_with_ollama

# Configuración del Perfil Translator
TARGET_LANGS = ['en', 'fr', 'pt', 'de']
MODEL = 'qwen3:4b-instruct'
TEMPERATURE = 0.0
CONTEXT = 8192

SYSTEM_PROMPT = """Actúa como traductor experto en deportes outdoor, software libre, salud, espiritualidad budista, viajes y educación.
Traduce del español al idioma objetivo manteniendo el tono resiliente y soberano.
REGLAS:
1. NUNCA uses "Edge AI" ni "Inteligencia Artificial en el borde".
2. Respeta el glosario: Cicloturismo=Cycle touring, Software libre=Free software, Offline-first=Offline-first.
3. Devuelve SOLO un JSON válido con esta estructura:
{"translations": {"clave": "valor"}, "grounding_notes": ["nota1", "nota2"]}
"""

def translate_page(url: str, page_name: str):
    """Traduce una página a todos los idiomas objetivo."""
    print(f"\n{'='*60}")
    print(f"📄 Procesando: {page_name} ({url})")
    print(f"{'='*60}")
    
    # 1. Extraer contenido con el Core
    print("⬇️  Extrayendo contenido con fetcher...")
    content = fetch_url(url)
    if not content or len(content) < 100:
        print(f"️  Contenido insuficiente para {page_name}")
        return
    
    print(f"✅ Contenido extraído: {len(content)} caracteres")
    
    # 2. Traducir a cada idioma
    for lang in TARGET_LANGS:
        print(f"\n🌐 Traduciendo a {lang.upper()}...")
        
        prompt = f"""
Idioma objetivo: {lang}

Contenido fuente en español:
=== INICIO DEL TEXTO FUENTE ===
{content[:3000]}  # Limitamos para no saturar el contexto
=== FIN DEL TEXTO FUENTE ===

Traduce al {lang} respetando las reglas. Devuelve solo JSON válido.
"""
        
        result = extract_with_ollama(
            prompt=prompt,
            system_prompt=SYSTEM_PROMPT,
            model=MODEL,
            temperature=TEMPERATURE,
            num_ctx=CONTEXT
        )
        
        # 3. Guardar resultado
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
    if len(sys.argv) < 3:
        print("Uso: python translate.py <url> <nombre_pagina>")
        print("Ejemplo: python translate.py https://sportdharmaecosystem.com/es/fundador/ fundador")
        sys.exit(1)
    
    url = sys.argv[1]
    page_name = sys.argv[2]
    translate_page(url, page_name)
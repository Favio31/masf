import requests
import json
import os

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "qwen3:4b-instruct"

SYSTEM_PROMPT = """
Actúa como traductor experto para SportDharma Ecosystem.
Temas de esencia: Deporte, Salud, Espiritualidad, Open Source, Viajes, Educación.
REGLAS:
1. NUNCA uses "Edge AI".
2. Tono: Resiliente, soberano, humano.
3. Devuelve SOLO JSON válido: {"translations": {"titulo": "...", "subtitulo": "..."}, "grounding_notes": ["..."]}
"""

TEXT_TO_TRANSLATE = """
Título: Fundador | SportDharma Ecosystem
Subtítulo: Cicloviajero · Fundador · Desarrollador
Bio: Durante 11 años recorrí 120.000 km en bicicleta por 84 países. SportDharma nació de la necesidad de herramientas digitales soberanas, offline-first y sin tracking para deportistas y comunidades remotas.
"""

def translate(lang):
    payload = {
        "model": MODEL,
        "prompt": f"Traduce al {lang}:\n{TEXT_TO_TRANSLATE}",
        "system": SYSTEM_PROMPT,
        "stream": False,
        "options": {"temperature": 0.0}
    }
    r = requests.post(OLLAMA_URL, json=payload, timeout=120)
    return r.json().get("response", "{}")

os.makedirs("translations/output", exist_ok=True)

for lang in ['en', 'fr', 'pt', 'de']:
    print(f"🌐 Traduciendo a {lang}...")
    res = translate(lang)
    # Limpieza básica de markdown
    res = res.replace("```json", "").replace("```", "").strip()
    try:
        data = json.loads(res)
    except:
        data = {"raw": res, "error": "JSON inválido"}
    
    with open(f"translations/output/fundador_{lang}.json", "w", encoding="utf-8") as f:
        json.dump({"page": "fundador", "lang": lang, "data": data}, f, ensure_ascii=False, indent=2)
    print(f"✅ Guardado: translations/output/fundador_{lang}.json")
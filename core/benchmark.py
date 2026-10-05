# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2026 Favio (SportDharma Ecosystem)

"""
MASF Benchmark — Comparación de modelos para extracción de sponsors
Regla de Oro: Temperatura 0.0, LLM extrae, Python decide
"""
import json
import ollama
from pathlib import Path
from datetime import datetime

# Configuración
FIXTURE = Path("fixtures/sponsor_real_01.txt")
OUTPUT = Path("docs/model-benchmark.md")
MODELS = ["qwen3:4b-instruct", "smollm2:1.7b"]

# Prompt canónico multi-entity (temperatura 0.0, extracción estructurada)
PROMPT = """Extrae TODAS las oportunidades de financiamiento/patrocinio del texto en formato JSON.

Si hay múltiples oportunidades, devuelve un array JSON con cada una.
Si solo hay una, devuelve un array con un solo elemento.

Cada elemento debe tener estos campos:
- sponsor_name: nombre de la organización
- program_name: nombre del programa
- amount: monto máximo en USD/EUR (solo número)
- deadline: fecha límite (formato YYYY-MM-DD)
- website: URL oficial
- email: email de contacto

Si un campo no existe, usa null. No inventes datos.
Devuelve SOLO el JSON, sin texto adicional.
"""


def extract(model: str, text: str) -> list:
    """Llama al modelo local y devuelve lista de entidades extraídas."""
    try:
        response = ollama.chat(
            model=model,
            messages=[{"role": "user", "content": f"{PROMPT}\n\n{text}"}],
            options={"temperature": 0.0, "num_ctx": 4096},
        )
        content = response["message"]["content"].strip()

        # Limpiar markdown fences si el modelo las agrega
        if content.startswith("```"):
            lines = content.split("\n")
            content = "\n".join(lines[1:-1]) if lines[-1].startswith("```") else "\n".join(lines[1:])

        result = json.loads(content)

        # Normalizar: si es dict único, convertir a lista
        if isinstance(result, dict):
            result = [result]
        elif isinstance(result, list):
            pass
        else:
            result = []

        return result

    except json.JSONDecodeError as e:
        print(f"   ⚠️  JSON inválido: {e}")
        print(f"      Raw: {content[:200]}")
        return []
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return []


def run_benchmark():
    """Ejecuta el benchmark y genera reporte Markdown."""
    text = FIXTURE.read_text(encoding="utf-8")
    print(f"📄 Fixture: {FIXTURE}")
    print(f"🤖 Modelos: {MODELS}")
    print()

    results = {}
    for model in MODELS:
        print(f"⏳ Probando {model}...")
        entities = extract(model, text)

        if entities:
            print(f"   ✅ {len(entities)} entidad(es) extraída(s)")
            for i, e in enumerate(entities, 1):
                print(f"      [{i}] Sponsor: {e.get('sponsor_name')}")
                print(f"          Monto: {e.get('amount')}")
                print(f"          Deadline: {e.get('deadline')}")
                print(f"          Website: {e.get('website')}")
                print(f"          Email: {e.get('email')}")
        else:
            print(f"   ❌ Sin resultados")

        results[model] = entities
        print()

    # Generar reporte Markdown
    now = datetime.now().isoformat()
    md = f"# MASF Model Benchmark\n\n"
    md += f"**Fecha**: {now}\n"
    md += f"**Fixture**: `{FIXTURE}`\n"
    md += f"**Modelos evaluados**: {', '.join(MODELS)}\n\n"
    md += "## Resultados\n\n"

    for model, entities in results.items():
        md += f"### {model}\n\n"
        if entities:
            md += f"**{len(entities)} entidad(es) extraída(s)**\n\n"
            for i, e in enumerate(entities, 1):
                md += f"#### Entidad {i}\n\n"
                md += "```json\n"
                md += json.dumps(e, indent=2, ensure_ascii=False)
                md += "\n```\n\n"
        else:
            md += "*Sin resultados*\n\n"

    md += "## Criterios de Evaluación\n\n"
    md += "- **Precisión**: ¿Los datos extraídos coinciden con el texto fuente?\n"
    md += "- **Formato**: ¿El JSON es válido y sigue el esquema esperado?\n"
    md += "- **Alucinaciones**: ¿Inventó datos que no están en el texto?\n"
    md += "- **Grounding**: ¿Puede citar la fuente exacta de cada dato?\n"

    OUTPUT.write_text(md, encoding="utf-8")
    print(f"📝 Reporte generado: {OUTPUT}")


if __name__ == "__main__":
    run_benchmark()
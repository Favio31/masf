# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2026 Favio (SportDharma Ecosystem)

"""
MASF Benchmark — Comparación de modelos para extracción de sponsors
Regla de Oro: Temperatura 0.0, LLM extrae, Python decide
"""
import json
import ollama
...

# Configuración
FIXTURE = Path("fixtures/sponsor_01.txt")
OUTPUT = Path("docs/model-benchmark.md")
MODELS = ["qwen3:4b-instruct", "smollm2:1.7b"]

# Prompt canónico (temperatura 0.0, extracción estructurada)
PROMPT = """Extrae la siguiente información del texto en formato JSON estricto.
Si un campo no existe, usa null. No inventes datos.

Campos requeridos:
- sponsor_name: nombre de la organización
- program_name: nombre del programa de patrocinio
- amount: monto máximo en USD (solo número)
- deadline: fecha límite (formato YYYY-MM-DD)
- website: URL oficial
- email: correo de contacto

Texto:
{text}

Responde SOLO con JSON válido, sin explicaciones."""

def read_fixture():
    """Lee el archivo de prueba"""
    return FIXTURE.read_text(encoding="utf-8")

def extract_with_model(model: str, text: str) -> dict:
    """Extrae datos usando un modelo específico"""
    try:
        response = ollama.chat(
            model=model,
            messages=[{"role": "user", "content": PROMPT.format(text=text)}],
            options={"temperature": 0.0}
        )
        content = response["message"]["content"].strip()
        
        # Limpiar respuesta (quitar markdown code blocks si existen)
        if content.startswith("```"):
            content = content.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        
        return json.loads(content)
    except Exception as e:
        return {"error": str(e)}

def run_benchmark():
    """Ejecuta el benchmark completo"""
    text = read_fixture()
    results = {}
    
    print(f" Benchmark iniciado: {datetime.now().isoformat()}")
    print(f"📄 Fixture: {FIXTURE}")
    print(f" Modelos: {MODELS}\n")
    
    for model in MODELS:
        print(f"⏳ Probando {model}...")
        result = extract_with_model(model, text)
        results[model] = result
        
        # Mostrar resultado
        if "error" in result:
            print(f"   ❌ Error: {result['error']}")
        else:
            print(f"   ✅ Extracción exitosa")
            print(f"      Sponsor: {result.get('sponsor_name', 'N/A')}")
            print(f"      Monto: {result.get('amount', 'N/A')} USD")
            print(f"      Deadline: {result.get('deadline', 'N/A')}")
    
    # Generar reporte
    generate_report(results)
    print(f"\n Reporte generado: {OUTPUT}")

def generate_report(results: dict):
    """Genera el reporte en Markdown"""
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    
    report = f"""# MASF Model Benchmark

**Fecha**: {datetime.now().isoformat()}  
**Fixture**: `fixtures/sponsor_01.txt`  
**Modelos evaluados**: {', '.join(MODELS)}

## Resultados

"""
    for model, result in results.items():
        report += f"### {model}\n\n"
        if "error" in result:
            report += f"**Error**: {result['error']}\n\n"
        else:
            report += f"```json\n{json.dumps(result, indent=2, ensure_ascii=False)}\n```\n\n"
    
    report += """## Criterios de Evaluación

- **Precisión**: ¿Los datos extraídos coinciden con el texto fuente?
- **Formato**: ¿El JSON es válido y sigue el esquema esperado?
- **Alucinaciones**: ¿Inventó datos que no están en el texto?
- **Grounding**: ¿Puede citar la fuente exacta de cada dato?

## Próximo Paso

Validar resultados con `core/grounding_validator.py` para verificar citas literales.
"""
    
    OUTPUT.write_text(report, encoding="utf-8")

if __name__ == "__main__":
    run_benchmark()
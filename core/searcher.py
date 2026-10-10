"""
Core searcher.
Módulo de búsqueda web gratuito y privado (0.00 OPEX) usando DDGS (DuckDuckGo Search).
Recopila URLs y snippets para que el Revisor Humano evalúe las oportunidades.
"""
import json
from typing import List, Dict

try:
    from ddgs import DDGS
except ImportError:
    raise ImportError("Instala ddgs: pip install ddgs>=9.0.0")


def search_opportunities(keywords: str, max_results: int = 5) -> List[Dict[str, str]]:
    """
    Busca oportunidades en la web usando DDGS (DuckDuckGo).
    
    Args:
        keywords: La cadena de búsqueda (ej: "bikepacking sponsorship").
        max_results: Número máximo de resultados a devolver (default: 5).
        
    Returns:
        Lista de diccionarios con 'title', 'url' y 'snippet'.
    """
    results = []
    try:
        # Reutilizar una sola instancia de DDGS (mejor práctica)
        with DDGS() as ddgs:
            search_results = ddgs.text(
                keywords, 
                max_results=max_results,
                region="wt-wt",  # worldwide
                safesearch="moderate"
            )
            for r in search_results:
                results.append({
                    "title": r.get("title", "Sin título"),
                    "url": r.get("href", ""),
                    "snippet": r.get("body", "Sin descripción")
                })
    except Exception as e:
        return [{"error": f"Error en la búsqueda: {str(e)}"}]
    
    return results


def run_scout_profile(profile_path: str = "profiles/scout_spec.md", max_results_per_keyword: int = 3) -> List[Dict]:
    """
    Lee el perfil scout, extrae las keywords y ejecuta búsquedas.
    Retorna una lista consolidada de oportunidades encontradas.
    """
    try:
        with open(profile_path, "r", encoding="utf-8") as f:
            profile_content = f.read()
    except FileNotFoundError:
        return [{"error": f"No se encontró el perfil en {profile_path}"}]

    # Extracción simple de keywords
    keywords_list = []
    in_keywords_section = False
    for line in profile_content.split("\n"):
        if "Palabras Clave de Búsqueda" in line or "Keywords" in line:
            in_keywords_section = True
            continue
        if in_keywords_section:
            if line.strip().startswith("-") or line.strip().startswith("*"):
                # Separar por "OR" para hacer búsquedas individuales más precisas
                parts = line.split("OR")
                for part in parts:
                    clean_part = part.strip(" -*\"\n\r'")
                    if clean_part and len(clean_part) > 5:
                        keywords_list.append(clean_part)
            elif line.strip() and not line.startswith(" "):
                in_keywords_section = False

    if not keywords_list:
        return [{"error": "No se encontraron keywords en el perfil."}]

    print(f"[BUSQUEDA] Iniciando búsqueda con {len(keywords_list)} keywords...")
    all_opportunities = []

    for kw in keywords_list:
        print(f"  → Buscando: {kw[:50]}...")
        results = search_opportunities(kw, max_results=max_results_per_keyword)
        for r in results:
            if "error" not in r:
                r["search_keyword"] = kw
                all_opportunities.append(r)

    print(f"[OK] Búsqueda completada. Se encontraron {len(all_opportunities)} resultados.")
    return all_opportunities


if __name__ == "__main__":
    print("Ejecutando prueba del Searcher...")
    test_results = search_opportunities("open source affiliate program", max_results=3)
    print(json.dumps(test_results, indent=2, ensure_ascii=False))

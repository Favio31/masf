# MASF (Motor Autónomo de Search & Fetch)
### Ecosistema SportDharma | 0.00 OPEX | Human-in-the-Loop

MASF es un pipeline de extracción y búsqueda web diseñado para identificar oportunidades estratégicas con **costo operativo cero**, respetando la privacidad y manteniendo al humano como juez ético final.

## 🏗️ Arquitectura
- **`core/`**: Módulos genéricos (searcher, fetcher, extractor, grounding_validator).
- **`profiles/`**: Perfiles de búsqueda para el **proyecto SportDharma**.
- **`clients/`**: Perfiles de búsqueda aislados para **clientes del servicio MASF Concierge**.
- **`drafts/`**: Zona de cuarentena. Nada se publica sin aprobación humana.

## 🚀 Uso
### Modo Scout (Búsqueda Autónoma)
python -m core.main --scout --profile sponsors --type project

### Modo Extracción (Análisis Profundo)
python -m core.main --url https://ejemplo.com --fields nombre_programa requisitos contacto

## 🛡️ Principios de Diseño
1. **0.00 OPEX**: Usa `ddgs` y LLMs locales.
2. **Human-in-the-Loop**: El humano decide qué es ético.
3. **Seguridad**: `fetcher.py` usa una `ALLOWLIST` estricta.
4. **Grounding Obligatorio**: Sin citas literales, no hay dato válido.


## Motor de Extraccion Dual

El MASF utiliza un sistema inteligente de doble motor:

1. **Requests** (rapido, ~milisegundos): Para sitios que sirven HTML estatico suficiente (>150 chars).
2. **Playwright** (fallback, ~2-4s): Se activa automaticamente cuando:
   - El sitio devuelve un "JS shell" vacio (<150 chars)
   - `requests` falla por timeout o bloqueo de bot

Playwright lanza Chromium headless, espera el renderizado JavaScript y extrae el contenido completo.

### Ejemplo de funcionamiento

| Sitio | Metodo | Contenido |
|-------|--------|-----------|
| GitHub | Playwright | 6204 chars |
| Devinci | Playwright | 7450 chars |
| Bikepacking | Requests | 7905 chars |

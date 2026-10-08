# Privacidad y Modelo de Amenazas

SportDharma MASF está diseñado con un enfoque **local-first** y **privacy-preserving**.

## Principios de Privacidad

1. **Sin nube:** Todo el procesamiento (descarga, chunking, extracción y validación) ocurre 100% en el dispositivo del usuario.
2. **Sin telemetry:** No se envían datos, métricas ni logs a servidores externos.
3. **LLM Local:** Utiliza Ollama en `localhost:11434`, sin llamadas a APIs de terceros (OpenAI, Anthropic, etc.).
4. **Sin credenciales almacenadas:** No se guardan tokens, passwords ni claves de terceros.

## Flujo de Datos
[URL] → fetcher.py (allowlist) → [HTML] → chunker.py → [chunks]
→ extractor.py (Ollama local) → [JSON] → grounding_validator.py
→ [verified / unverified / missing]

Ningún dato sale del dispositivo del usuario en ningún punto del pipeline.

## Modelo de Amenazas Completo

Para entender qué protege este sistema, cuáles son sus límites y qué amenazas mitiga, consultá el documento técnico completo:

👉 **[Threat Model (docs/threat-model.md)](threat-model.md)**

## Limitaciones Declaradas

- **Host comprometido:** MASF no puede proteger contra malware o acceso físico al dispositivo del usuario. Esta amenaza está declarada como **out of scope**.
- **Fuentes web maliciosas:** El contenido descargado puede contener información falsa. El GroundingValidator solo verifica que el valor esté respaldado por la cita literal, no que la fuente sea veraz.
- **Sesgos del LLM:** Qwen3-4B-Instruct puede tener sesgos inherentes. MASF los hace trazables pero no los corrige automáticamente.

## Contacto

Para reportar vulnerabilidades de seguridad: **contact@sportdharmaecosystem.com**

---

*Última actualización: 2026-10-07*


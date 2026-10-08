# Threat Model — SportDharma MASF

**Versión:** 1.0  
**Fecha:** 2026-10-07  
**Autor:** Favio (SportDharma Ecosystem)

## 1. Alcance

MASF (Multi-Agent Swarm Framework) es un sistema **local-first** que extrae información de fuentes web usando un LLM local (Ollama). Este documento modela las amenazas relevantes para usuarios que operan con recursos limitados y conectividad intermitente.

## 2. Supuestos de diseño

- El sistema corre **100% en el dispositivo del usuario** (no hay backend en la nube).
- El LLM (Qwen3-4B-Instruct) corre vía Ollama en `localhost:11434`.
- Las fuentes web se descargan directamente desde el dispositivo del usuario.
- No se almacenan credenciales ni tokens de terceros.

## 3. Tabla de amenazas

| ID | Amenaza | Vector | Impacto | Probabilidad | Mitigación | Estado |
|----|---------|--------|---------|--------------|------------|--------|
| T01 | Inyección de prompt via fuente web | Texto malicioso en URL descargada | Alto | Media | Delimitadores `=== INICIO/FIN DEL TEXTO FUENTE ===` en extractor.py | ✅ Implementado |
| T02 | Dominio malicioso en allowlist | Allowlist comprometida | Alto | Baja | Allowlist hardcodeada de 3 dominios de confianza | ✅ Implementado |
| T03 | LLM local comprometido | Ollama expuesto en red | Crítico | Baja | Ollama bind a localhost por defecto | ⚠️ Documentado |
| T04 | Exfiltración de datos via respuesta LLM | Modelo envía datos a red | Alto | Baja | Temperatura 0.0, sin streaming, sin callbacks de red | ✅ Implementado |
| T05 | HTML malicioso (XSS/script) en fuente | Script injection al parsear | Medio | Media | **Pendiente**: limpieza HTML antes de pasar al LLM | 🔴 Pendiente |
| T06 | DoS por fuente gigante | Texto de GB consume memoria | Medio | Baja | Chunker limita a 3000 chars por bloque | ✅ Implementado |
| T07 | Host comprometido | Atacante con acceso al dispositivo | Crítico | N/A | **Out of scope**: ningún software puede proteger contra esto | ️ Declarado |
| T08 | Fuga de metadata en requests | User-Agent revela identidad | Bajo | Media | User-Agent genérico `SportDharma-MASF/1.0` | ✅ Implementado |
| T09 | Alucinación del LLM | Valor extraído no respaldado por cita | Alto | Media | GroundingValidator marca como `unverified` | ✅ Implementado |
| T10 | Robots.txt ignorado | Scraping no ético | Bajo | Media | **Pendiente**: respeto a robots.txt | 🔴 Pendiente |

## 4. Flujo de datos
[URL] → fetcher.py (allowlist) → [HTML crudo]
↓
(limpieza pendiente)
↓
chunker.py (3000 chars + overlap)
↓
[chunks] → extractor.py (Ollama local)
↓
[JSON con value + quote]
↓
grounding_validator.py
↓
[verified / unverified / missing]

## 5. Lo que MASF NO protege

- **Host comprometido**: si el dispositivo del usuario está infectado, ningún software puede garantizar seguridad.
- **Fuentes web maliciosas**: el contenido descargado puede contener información falsa; el GroundingValidator solo verifica que el valor esté respaldado por la cita, no que la fuente sea veraz.
- **Modelo LLM sesgado**: Qwen3-4B-Instruct puede tener sesgos inherentes; MASF no los corrige, solo los hace trazables.

## 6. Recomendaciones para el usuario

1. Mantener Ollama actualizado.
2. No exponer el puerto 11434 a la red.
3. Revisar manualmente los campos marcados como `unverified`.
4. Usar solo las fuentes de la allowlist.

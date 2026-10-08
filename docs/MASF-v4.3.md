# SportDharma Ecosystem — Multi-Agent Swarm Framework (MASF) v4.3

**Metodología:** Spec-Driven Development (SDD, nivel spec-anchored) + extracción verificada local
**Estado:** Canónico aprobado por el fundador · Fase A (Endurecimiento Técnico Completado)
**Fecha:** 7 de octubre de 2026 · Sustituye a: v4.2 (1 de octubre de 2026)
**Subordinado a:** Plan Maestro v4.0. Ante cualquier conflicto prevalece el Plan Maestro.
**Licencias:** Código fuente bajo GNU AGPLv3 (o posterior) · Documentación bajo CC-BY-SA 4.0

*Este documento es público. Las notas comerciales internas viven en un archivo aparte, fuera del repositorio público.*

---

## 1. RESUMEN EJECUTIVO

El MASF es el sistema de captura y curación automatizada del ecosistema SportDharma. Es un framework de dos cuerpos (Core genérico + Perfiles específicos) regido por la Regla de Oro: **"El LLM extrae, Python decide"**.

Su objetivo es capturar, curar y validar conocimiento técnico y oportunidades (grants, sponsors) con 0 euros de infraestructura recurrente, software 100% FOSS e inferencia local, entregando los resultados siempre para revisión humana antes de publicarse.

Técnicamente es un sistema de extracción atribuida y verificada: el modelo propone cada dato junto con la cita textual que lo respalda, y código determinista (Python) comprueba que la cita exista en la fuente. **Nota de transparencia crítica:** MASF no garantiza "cero alucinaciones". Lo que garantiza es que **toda afirmación no respaldada por una cita literal verificable se marca explícitamente como `unverified` o se rechaza**. El *fuzzy match* para validación de citas está **[PLANIFICADO]** para futuras versiones; la implementación actual usa *exact-match*.

**Alcance:** El MASF es el workstream A-Curación de la Parte A. No forma parte del núcleo táctico de seguridad y nunca interviene en una ruta crítica.

---

## 2. LOS 9 PILARES APLICADOS AL MASF

Un pilar sin test es un eslogan. Hoy el proyecto cuenta con **70 tests automatizados (100% passing)** que validan estos pilares.

1. **Software Soberano:** La descarga es el único paso con red. Extracción, validación y scoring se ejecutan sobre snapshots locales.
2. **Transparente:** Cada dato lleva cita, offsets, hash SHA-256 del snapshot, modelo y versión de spec.
3. **Modular:** Esquemas Pydantic v2 exportables; un perfil es solo configuración.
4. **Educación Permanente:** Solo se publica contenido propio bajo CC-BY-4.0; el de terceros se enlaza.
5. **Solidaria:** El MASF no toca fondos; solo genera fichas de oportunidad.
6. **Ecológica:** Ejecución local con `OLLAMA_KEEP_ALIVE=0` para liberar RAM inmediatamente.
7. **Inclusiva:** Fichas y boletines en ES/EN; gate de CI para accesibilidad.
8. **Sostenibilidad Alineada:** Filtro de esencia de 6 tests y registro público de decisiones.
9. **Resiliente:** Offline-First. El MASF produce snapshots JSON que la app y la web pueden servir sin red.

---

## 3. DOS SISTEMAS, NO UNO

- **A. Pipeline de ejecución (runtime):** Código Python + un LLM local (solo como función de extracción de texto a JSON). Sin herramientas, sin shell, sin web.
- **B. Flujo de desarrollo (dev-time):** Fundador + asistente de código (Continue.dev). Regido por `AGENTS.md` y ciclo SDD. Nada del flujo B se ejecuta en producción.

---

## 4. PIPELINE DE EJECUCIÓN (RUNTIME)

### 4.1 Componentes (Fase A Implementada)

- `core/main.py`: Orquestador con CLI (`argparse`). Soporta `--input`, `--url`, `--profile`, `--fields`, `--output`.
- `core/fetcher.py`: Descarga con allowlist de dominios, User-Agent genérico y **limpieza de HTML** (BeautifulSoup4) para mitigar inyección de scripts (T05). Guarda snapshot con hash SHA-256 del *texto limpio*.
- `core/chunker.py`: Divide en bloques (ej. 3000 chars + 300 overlap). Protegido contra bucles infinitos (MemoryError).
- `core/extractor.py`: Llama a Ollama con **delimitadores seguros** (`=== INICIO/FIN DEL TEXTO FUENTE ===`) para evitar inyección de prompt. Incluye lógica de **máximo 2 reintentos** ante fallos de red.
- `core/grounding_validator.py`: Verifica citas (exact-match) y determina estados (`verified`, `unverified`, `missing`).
- `core/schemas.py`: Esquemas Pydantic v2 específicos por perfil con validadores de formato (fecha, email, URL).

### 4.2 Modelo de extracción

- **Modelo adoptado:** `qwen3:4b-instruct` (Apache-2.0).
- **Respaldo probado:** `smollm2:1.7b` (Apache-2.0).
- **Configuración obligatoria:** Temperatura 0.0, `num_ctx=8192`, salida estructurada JSON, `OLLAMA_KEEP_ALIVE=0`.

---

## 5. GROUNDING VERIFICABLE

### 5.1 Contrato de extracción

Por cada campo, el LLM debe devolver: `{ "value": "...", "quote": "..." }`

### 5.2 Verificaciones (Python determinista)

1. **Cita presente:** `quote` aparece como substring exacto en el texto fuente normalizado.
2. **Valor contenido:** El `value` es coherente con la `quote`.
3. **Tipo y formato:** Validación estricta vía Pydantic v2 (REQ-06 a REQ-08).

### 5.3 Estados por campo

- `verified`: Pasó todas las verificaciones.
- `unverified`: El modelo lo propuso, pero la cita no existe o el formato es inválido. **No se publica sin revisión humana.**
- `missing`: La fuente no lo contiene.

*Nota:* El *fuzzy match* (similitud > 0.95) está **[PLANIFICADO]**. La versión actual usa *exact-match* por seguridad y simplicidad.

---

## 6. REINTENTOS ACOTADOS

- **Alcance:** Por campo, no por documento.
- **Máximo:** 2 reintentos. Prohibido el bucle infinito.
- **Agotados:** El campo queda `unverified`, se marca para revisión y se notifica.

---

## 7. ESQUEMA DE DATOS CANÓNICO (Pydantic v2)

Implementado en `core/schemas.py`. Incluye validadores automáticos:

```python
class SponsorField(BaseModel):
    value: Optional[str] = None
    quote: Optional[str] = None
    status: str = "missing"  # verified, unverified, missing
    field_type: str = "text"  # text, date, email, url

class SponsorCardPayload(BaseModel):
    sponsor_name: SponsorField
    program_name: SponsorField
    amount: SponsorField
    deadline: SponsorField    # Validador: ISO 8601 o DD/MM/YYYY
    website: SponsorField     # Validador: URL HTTP/HTTPS
    email: SponsorField       # Validador: RFC 5322 simplificado
    
    Si un campo de fecha, email o URL no pasa el validador de formato, su status se fuerza automáticamente a unverified

    masf/
├── core/               # Motor genérico (Python puro)
│   ├── main.py         # Entrypoint CLI
│   ├── fetcher.py      # Descarga + limpieza HTML + SHA-256
│   ├── chunker.py      # Segmentación segura
│   ├── extractor.py    # Extracción con delimitadores y reintentos
│   ├── grounding_validator.py  # Validación anti-alucinaciones
│   └── schemas.py      # Esquemas Pydantic v2 con validadores EARS
├── profiles/sponsors/
│   └── spec.md         # Especificación EARS (REQ-01 a REQ-13)
├── tests/              # Suite de 70 tests (100% passing)
│   ├── test_chunker.py
│   ├── test_extractor.py
│   ├── test_fetcher.py
│   ├── test_grounding_validator.py
│   └── test_schemas.py
├── docs/
│   ├── threat-model.md # 10 amenazas mapeadas y mitigadas
│   └── privacy.md      # Política local-first, sin telemetry
├── fixtures/           # Documentos de prueba (Dataset en construcción)
├── requirements.txt    # Dependencias Python
└── README.md

9. SEGURIDAD, LEGAL Y ÉTICA
9.1 Modelo de Amenazas
Ver documento completo: docs/threat-model.md. Resumen de mitigaciones implementadas:
T01 (Inyección de prompt): Mitigado con delimitadores === INICIO/FIN ===.
T02 (Dominio malicioso): Mitigado con allowlist hardcodeada.
T05 (HTML malicioso/XSS): Mitigado con limpieza vía BeautifulSoup4 en fetcher.py.
T07 (Host comprometido): Declarado honestamente como Out of Scope.
9.2 Datos Personales (RGPD)
Solo se extraen contactos institucionales públicos (ej. partnerships@marca.com). Se evita la extracción de nombres y correos personales directos para minimizar el tratamiento de PII.
9.3 Divulgación de IA (Política NLnet)
Todo código asistido por IA lleva trailers de commit (Assisted-by, Prompts-log, Reviewed-by). El trabajo generado en su mayor parte por LLM no se presenta como autoría humana exclusiva ni se factura contra hitos sin revisión.
10. EVALUACIÓN Y MÉTRICAS ACTUALES
10.1 Calidad de Código
Suite de tests: 70 tests automatizados.
Cobertura: 100% de los módulos críticos (chunker, extractor, fetcher, grounding_validator, schemas) pasando en verde.
Bugs críticos corregidos en v4.3:
Bucle infinito en chunker.py con overlap > tamaño de texto (MemoryError).
GroundingValidator marcando None como verified.
Claims falsos de "cero alucinaciones" en documentación.
10.2 Conjunto de Referencia (Fixtures)
Estado: Estructura lista. La anotación manual de 20-30 documentos reales con etiquetas de verdad terreno (ground truth) es una tarea pendiente del Bloque B, Paso 6.

11. PLAN DE TRABAJO — FASE A (ESTADO ACTUALIZADO)
Bloque
Paso
Tarea
Estado
A. Core
1
Entorno y Modelo (Ollama, Qwen3)
✅ Completo
2
Arnés de Control (Git hooks, CI)
🟡 Parcial (hooks pendientes)
3
Motor de Extracción y Validación
✅ Completo (con reintentos y delimitadores)
4
Benchmark (Qwen3 vs SmolLM2)
🟡 Pendiente (requiere fixtures anotados)
B. Perfiles
5
Especificación SDD (EARS)
✅ Completo (profiles/sponsors/spec.md)
6
Conjunto de Referencia (Fixtures)
🔴 Pendiente (tarea manual de curación)
7
Lógica Específica (Pydantic v2)
✅ Completo (core/schemas.py con validadores)
8
Prueba Extremo a Extremo (E2E)
🟡 Parcial (CLI funcional, falta dataset real)
C. Docs
9
Documentación Pública y Legal
✅ Completo (threat-model.md, privacy.md)
10
Publicación en GitHub (Favio31)
🔴 Pendiente
11
Dashboard Público (GitHub Pages)
🔴 Pendiente
12. GOBERNANZA Y LÍMITES NO NEGOCIABLES
Regla de Oro: El LLM extrae, Python decide. Temperatura 0.0.
Honestidad Brutal: Si no hay cita literal, el campo es unverified. No se ocultan las limitaciones del sistema.
Revisión Humana: needs_human_review = True siempre en Fase A.
Límite de Reintentos: Máximo 2 por campo.
Cláusula de Veto: Ante una solicitud que viole FOSS, 0.00 euros OPEX o privacidad, la única respuesta es "Alerta de Gobernanza".
13. DECISIONES ABIERTAS Y BACKLOG INMEDIATO
Integración del Pipeline: Conectar core/schemas.py directamente en el flujo de core/main.py para que la validación de fecha/email/URL se ejecute automáticamente en la salida del extractor.
Dataset de Fixtures: Anotar manualmente 20-30 documentos reales para establecer métricas de precisión y recall (Bloque B, Paso 6).
Fuzzy Match: Implementar algoritmo de similitud (ej. Levenshtein o embeddings locales) para la validación de citas, actualmente marcado como [PLANIFICADO].
Respeto a robots.txt: Agregar verificación de robots.txt en fetcher.py (actualmente marcado como T10 Pendiente en el Threat Model).
HISTORIAL DE VERSIONES
v4.0 | Sep 2026 | Versión inicial aprobada.
v4.1 | Sep 2026 | Integración de SDD, AGENTS.md y Multiagentes formales.
v4.2 | Oct 2026 | Protocolo de Transmisión de Contexto y Sintaxis EARS obligatoria.
v4.3 | 7 Oct 2026 | Ronda de Endurecimiento Técnico: Eliminación de claims de "cero alucinaciones". Implementación de 70 tests (100% passing). Pydantic v2 con validadores de fecha/email/URL. Limpieza de HTML en fetcher. Delimitadores seguros en prompt. Límite de 2 reintentos. Creación de docs/threat-model.md y docs/privacy.md honestos. CLI funcional en main.py.
Documento generado con asistencia de IA, consolidado y validado por Favio (SportDharma Ecosystem).
Última actualización: 2026-10-07
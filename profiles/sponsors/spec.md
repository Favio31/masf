\# MASF Profile Specification: Sponsors (Sponsor Scout)



\*\*Versión\*\*: 1.0  

\*\*Fecha\*\*: 2026-10-05  

\*\*Estado\*\*: Canónico · Fase A  

\*\*Subordinado a\*\*: Plan Maestro v4.0 · MASF Core  



\---



\## 1. Propósito



Este perfil define los requisitos funcionales y criterios de aceptación para la extracción, validación y curación de oportunidades de patrocinio deportivo (sponsors) dentro del MASF.



\---



\## 2. Schema de Datos (Pydantic)



El sistema SHALL extraer los siguientes campos de cada fuente:



| Campo | Tipo | Requerido | Descripción |

|-------|------|-----------|-------------|

| sponsor\_name | str | Sí | Nombre legal de la organización patrocinadora |

| program\_name | str | Sí | Nombre del programa de patrocinio |

| amount | Optional\[float] | No | Monto máximo en USD (solo número) |

| amount\_currency | str | No | Código ISO 4217 (default: "USD") |

| deadline | Optional\[str] | No | Fecha límite en formato ISO 8601 (YYYY-MM-DD) |

| website | Optional\[str] | No | URL oficial del programa |

| email | Optional\[str] | No | Correo de contacto |

| status | str | Sí | Estado: "active", "closed", "unknown" |

| uncertainty | Optional\[str] | No | Manejo de incertidumbre (ver §4) |

| source\_url | str | Sí | URL de la fuente original |

| extracted\_at | str | Sí | Timestamp ISO 8601 de la extracción |



\---



\## 3. Requisitos Funcionales (EARS)



\### 3.1 Extracción



\- \*\*REQ-01\*\*: WHEN el sistema recibe un texto fuente, SHALL extraer todos los campos del schema (§2) usando el LLM local con temperatura 0.0.

\- \*\*REQ-02\*\*: IF un campo no está presente en el texto fuente, SHALL asignar `null` al campo correspondiente.

\- \*\*REQ-03\*\*: The system SHALL NOT inventar datos que no estén explícitos en el texto fuente (cero alucinaciones).



\### 3.2 Validación



\- \*\*REQ-04\*\*: WHEN la extracción se completa, SHALL pasar los resultados al `GroundingValidator` para verificar citas literales.

\- \*\*REQ-05\*\*: IF el `GroundingValidator` detecta una alucinación, SHALL marcar el campo como `uncertain` y aplicar el fallback canónico (§4).

\- \*\*REQ-06\*\*: The system SHALL validar el formato de `deadline` como ISO 8601 (YYYY-MM-DD). IF el formato es inválido, SHALL asignar `null`.

\- \*\*REQ-07\*\*: The system SHALL validar el formato de `email` como RFC 5322. IF el formato es inválido, SHALL asignar `null`.

\- \*\*REQ-08\*\*: The system SHALL validar el formato de `website` como URL válida. IF el formato es inválido, SHALL asignar `null`.



\### 3.3 Manejo de Incertidumbre



\- \*\*REQ-09\*\*: WHEN un campo crítico (amount, deadline) no está explícito en el texto, SHALL asignar el valor de incertidumbre correspondiente:

&#x20; - amount → "Monto Variable/ Ver Detalles"

&#x20; - deadline → "Convocatoria Activa/ Consultar Bases"

\- \*\*REQ-10\*\*: IF el texto indica que el programa está cerrado o la fecha pasó, SHALL asignar `status: "closed"`.



\### 3.4 Salida



\- \*\*REQ-11\*\*: The system SHALL generar un JSON válido por cada oportunidad extraída.

\- \*\*REQ-12\*\*: The system SHALL incluir metadatos de trazabilidad: `source\_url`, `extracted\_at`, `model\_used`.

\- \*\*REQ-13\*\*: WHEN se procesan múltiples fuentes, SHALL generar un boletín curado con formato Markdown.



\---



\## 4. Fallbacks Canónicos



| Campo | Fallback |

|-------|----------|

| amount | "Monto Variable/ Ver Detalles" |

| deadline | "Convocatoria Activa/ Consultar Bases" |

| email | "Consultar sitio oficial" |

| website | "No disponible" |



\---



\## 5. Criterios de Aceptación



\- \*\*AC-01\*\*: El JSON de salida ES válido y parseable.

\- \*\*AC-02\*\*: Todos los campos requeridos (§2) están presentes.

\- \*\*AC-03\*\*: No hay alucinaciones detectadas por el `GroundingValidator`.

\- \*\*AC-04\*\*: Los formatos de fecha, email y URL son válidos o `null`.

\- \*\*AC-05\*\*: El campo `uncertainty` está presente cuando aplica (§3.3).



\---



\## 6. Ejemplo de Salida



```json

{

&#x20; "sponsor\_name": "Trek Bicycle Corporation",

&#x20; "program\_name": "Trek Seed Grant",

&#x20; "amount": 25000,

&#x20; "amount\_currency": "USD",

&#x20; "deadline": "2026-11-30",

&#x20; "website": "https://www.trekbikes.com/grants",

&#x20; "email": "grants@trekbikes.com",

&#x20; "status": "active",

&#x20; "uncertainty": null,

&#x20; "source\_url": "fixtures/sponsor\_01.txt",

&#x20; "extracted\_at": "2026-10-05T10:07:46.104969",

&#x20; "model\_used": "qwen3:4b-instruct"

}


\# AI Assistance Declaration



\*\*Project\*\*: MASF (Multi-Agent Swarm Framework)  

\*\*Part of\*\*: SportDharma Ecosystem  

\*\*License\*\*: GNU AGPLv3  

\*\*Last updated\*\*: 2026-10-05



\---



\## 1. Principio de transparencia



Este proyecto se construye con asistencia de inteligencia artificial local, siguiendo la \*\*Regla de Autoría\*\* del Plan Maestro (§3.3):



> \*"Nada puramente generado por IA se presenta como trabajo propio ni se factura contra hitos; divulgación con registro (ai-logs/, trailers Assisted-by/Prompts-log/Reviewed-by)."\*



\---



\## 2. Modelos utilizados



| Modelo | Uso | Licencia |

|--------|-----|----------|

| Qwen3-4B-Instruct | Motor de curación, benchmark, desarrollo | Apache-2.0 |

| SmolLM2-1.7B | Prototipo móvil (Edge AI) | Apache-2.0 |



Ambos modelos se ejecutan \*\*100% local\*\* vía Ollama, sin conexión a APIs externas.



\---



\## 3. Regla de Oro de la IA



El sistema MASF opera bajo el principio:



\*\*"El LLM extrae, Python decide."\*\*



\- Temperatura: 0.0 (determinista)

\- Validación: `GroundingValidator` con citas literales

\- Fallbacks canónicos para incertidumbre

\- Cero alucinaciones aceptadas



\---



\## 4. Trailers de autoría



Todos los commits incluyen:
Assisted-by: qwen3:4b-instruct via Ollama
Reviewed-by: Favio


Esto garantiza trazabilidad completa entre código humano y asistencia de IA.

---

## 5. Lo que la IA NO hace

- ❌ No toma decisiones de diseño arquitectónico
- ❌ No define requisitos funcionales (eso lo hace el Plan Maestro)
- ❌ No valida resultados (eso lo hace `GroundingValidator`)
- ❌ No se ejecuta en rutas críticas de seguridad (FSM Dharma Safe)

---

## 6. Cumplimiento normativo

Este documento cumple con:

- **Plan Maestro v4.0** §3.3 (Regla de Autoría)
- **Pilar 2** (Transparencia): todo uso de IA es verificable
- **Requisitos de grants FOSS/Proton**: declaración explícita de asistencia de IA

---

*Este documento es parte del SportDharma Ecosystem y está licenciado bajo CC-BY-SA 4.0.*




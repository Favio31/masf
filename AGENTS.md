\# SportDharma MASF

Misión: extracción verificada y local de conocimiento y oportunidades, alineada con los 9 pilares del Plan Maestro v4.0.



\## Stack

\- Python 3.12+, Pydantic v2, pytest

\- Ollama con Qwen3-4B-Instruct (Apache-2.0; ver MODEL.md); un modelo cargado a la vez



\## Comandos

\- python -m core.main --profile sponsors

\- pytest -q

\- ollama list



\## Estructura

core/ · profiles/ · fixtures/ · ai-logs/ · AGENTS.md · AI-ASSISTANCE.md



\## Convenciones

\- snake\_case; tests junto al módulo

\- Validar toda entrada externa

\- Temperatura 0.0 para extracción; num\_ctx explícito

\- Todo RF en spec.md usa EARS

\- Todo commit asistido lleva los trailers Assisted-by, Prompts-log y Reviewed-by



\## No hagas

\- No contactar sponsors ni enviar mensajes en nombre del fundador

\- No custodiar dinero ni datos sensibles

\- No inventar URLs, importes ni fechas

\- No subir .env\* ni credenciales

\- No aceptar código que el fundador no entienda

\- No superar 2 reintentos por campo

\- No dar al LLM de extracción herramientas (shell, web, escritura)



\## Flujo

\- Plan primero y esperar OK del fundador en tareas no triviales

\- Una tarea a la vez; informar qué cambió

\- Si hay menos de 80 % de certeza, preguntar



\## Verificación

\- pytest en verde antes de cada commit (hook)

\- Todo dato extraído pasa por grounding\_validator

\- Campo que agota reintentos → unverified + revisión humana


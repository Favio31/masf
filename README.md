\# MASF — Multi-Agent Swarm Framework



\*\*SportDharma Ecosystem\*\* · Infraestructura abierta de curación de oportunidades deportivas



!\[License](https://img.shields.io/badge/license-AGPL--3.0-blue.svg)

!\[Python](https://img.shields.io/badge/python-3.12+-green.svg)

!\[Status](https://img.shields.io/badge/status-Fase\_A-yellow.svg)



\---



\## 🎯 Qué es MASF



MASF es un framework de código abierto para la extracción, validación y curación automatizada de oportunidades deportivas (sponsors, grants, convocatorias) usando **IA local soberana** (Ollama + Qwen3-4B-Instruct + SmolLM2-1.7B) con **validación anti-alucinaciones basada en citas literales** y **cero dependencia de APIs externas**.

> **Nota de transparencia:** MASF no garantiza "cero alucinaciones". Toda afirmación extraída se valida contra la cita literal del texto fuente. Si el valor no está respaldado por una cita verificable, el campo se marca explícitamente como `unverified` o se rechaza. El fuzzy match está **[PLANIFICADO]** para futuras versiones.



\### Principios de diseño

\- \*\*Software Soberano\*\*: 100% local, sin vendor lock-in, sin rastreadores

\- \*\*Zero OPEX\*\*: Ejecución en GitHub Actions CRON + respaldo local con Ollama

\- \*\*Regla de Oro\*\*: El LLM extrae, Python decide. Temperatura 0.0, validación determinista

\- \*\*Copyleft fuerte\*\*: GNU AGPLv3 — cualquier derivado debe ser abierto



\---



\## 🏗️ Arquitectura

masf/

├── core/ # Motor genérico

│ ├── chunker.py # Segmentación de texto

│ ├── extractor.py # Extracción con LLM local

│ ├── fetcher.py # Obtención de fuentes

│ ├── grounding\_validator.py # Validación anti-alucinaciones

│ ├── benchmark.py # Comparación de modelos

│ └── main.py # Orquestador

├── fixtures/ # Datos de prueba

│ └── sponsor\_01.txt

├── profiles/ # Perfiles específicos

│ ── sponsors/

│ └── spec.md # Especificación EARS

├── docs/ # Documentación técnica

│ └── model-benchmark.md

├── AGENTS.md # Definición de agentes

├── MODEL.md # Selección de modelos

├── LICENSE # GNU AGPLv3

└── README.md



\---



\## 🚀 Inicio rápido



\### Requisitos

\- Python 3.12+

\- Ollama local con modelos descargados



\### Instalación

```bash

\# Clonar el repositorio

git clone https://github.com/Favio31/masf.git

cd masf



\# Instalar dependencias

pip install -r requirements.txt



\# Descargar modelos (si no los tienes)

ollama pull qwen3:4b-instruct

ollama pull smollm2:1.7b


# Reglas para Agentes de IA (MASF)

## 1. Arquitectura Sagrada
- **NUNCA** mezcles lógica de negocio específica en la carpeta `core/`. 
- `core/` es 100% genérico. Toda la especificidad va en `profiles/` o `clients/`.

## 2. Seguridad y Allowlist
- Si una URL no está en la `ALLOWLIST` de `fetcher.py`, **NO** la modifiques silenciosamente. Informa al humano.

## 3. Regla de Oro: Grounding Validator
- **NUNCA** inventes datos. Si no hay cita literal (`quote`), el estado es `"missing"` o `"unverified"`.

## 4. Human-in-the-Loop (HITL)
- **NUNCA** muevas archivos de `drafts/` a `published/` automáticamente.
- **NUNCA** envíes solicitudes sin que el humano apruebe el JSON.

## 5. Dependencias y OPEX
- Mantén el costo en **0.00**. Usa `ddgs`. No sugieras APIs de pago.

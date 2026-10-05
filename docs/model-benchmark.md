# MASF Model Benchmark

**Fecha**: 2026-10-05T11:56:38.775702  
**Fixture**: `fixtures/sponsor_01.txt`  
**Modelos evaluados**: qwen3:4b-instruct, smollm2:1.7b

## Resultados

### qwen3:4b-instruct

```json
{
  "sponsor_name": "New Belgium Brewing Company",
  "program_name": "Bicycle Advocacy Grant Program",
  "amount": 20000,
  "deadline": "2026-03-31",
  "website": "https://grantstation.com/grantmakers/new-belgium-bicycle-advocacy-grant",
  "email": "grants@newbelgium.com"
}
```

### smollm2:1.7b

```json
{
  "sponsor_name": "New Belgium Brewing Company",
  "program_name": "FY2026 Bicycle Advocacy Grant Program",
  "amount": 20000,
  "deadline": "2026-03-31",
  "website": "https://grantstation.com/grantmakers/new-belgium-bicycle-advocacy-grant",
  "email": "grants@newbelgium.com",
  "website_url": "https://grantstation.com/grantmakers/new-belgium-bicycle-advocacy-grant",
  "email_address": "grants@newbelgium.com"
}
```

## Criterios de Evaluación

- **Precisión**: ¿Los datos extraídos coinciden con el texto fuente?
- **Formato**: ¿El JSON es válido y sigue el esquema esperado?
- **Alucinaciones**: ¿Inventó datos que no están en el texto?
- **Grounding**: ¿Puede citar la fuente exacta de cada dato?

## Próximo Paso

Validar resultados con `core/grounding_validator.py` para verificar citas literales.

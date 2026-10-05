# MASF Model Benchmark

**Fecha**: 2026-10-05T10:09:31.280635  
**Fixture**: `fixtures/sponsor_01.txt`  
**Modelos evaluados**: qwen3:4b-instruct, smollm2:1.7b

## Resultados

### qwen3:4b-instruct

```json
{
  "sponsor_name": "Trek Bicycle Corporation",
  "program_name": "Trek Seed Grant",
  "amount": 25000,
  "deadline": "2026-11-30",
  "website": "https://www.trekbikes.com/grants",
  "email": "grants@trekbikes.com"
}
```

### smollm2:1.7b

```json
{
  "sponsor_name": "Trek Bicycle Corporation",
  "program_name": "Trek Seed Grant",
  "amount": 25000,
  "deadline": "2026-11-30",
  "website": "https://www.trekbikes.com/grants",
  "email": "grants@trekbikes.com"
}
```

## Criterios de Evaluación

- **Precisión**: ¿Los datos extraídos coinciden con el texto fuente?
- **Formato**: ¿El JSON es válido y sigue el esquema esperado?
- **Alucinaciones**: ¿Inventó datos que no están en el texto?
- **Grounding**: ¿Puede citar la fuente exacta de cada dato?

## Próximo Paso

Validar resultados con `core/grounding_validator.py` para verificar citas literales.

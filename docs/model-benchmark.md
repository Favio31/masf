# MASF Model Benchmark

**Fecha**: 2026-10-05T12:35:42.286386
**Fixture**: `fixtures\stress_test_multitier.txt`
**Modelos evaluados**: qwen3:4b-instruct, smollm2:1.7b

## Resultados

### qwen3:4b-instruct

**3 entidad(es) extraída(s)**

#### Entidad 1

```json
{
  "sponsor_name": "Global Adventure Sports Foundation",
  "program_name": "Explorer Grant",
  "amount": 15000,
  "deadline": "2026-10-15",
  "website": "https://gasf.example.org/explorer-grant",
  "email": "explorer@gasf.example.org"
}
```

#### Entidad 2

```json
{
  "sponsor_name": "Global Adventure Sports Foundation",
  "program_name": "Expedition Grant",
  "amount": 20000,
  "deadline": "2026-10-30",
  "website": "https://gasf.example.org/expedition-grant",
  "email": "expedition@gasf.example.org"
}
```

#### Entidad 3

```json
{
  "sponsor_name": "Global Adventure Sports Foundation",
  "program_name": "Legacy Grant",
  "amount": 50000,
  "deadline": "2026-11-20",
  "website": "https://gasf.example.org/legacy-grant",
  "email": "legacy@gasf.example.org"
}
```

### smollm2:1.7b

**3 entidad(es) extraída(s)**

#### Entidad 1

```json
{
  "sponsor_name": "Global Adventure Sports Foundation",
  "program_name": "2026 Multi-Tier Support Program",
  "amount": "€15,000",
  "deadline": "October 15, 2026",
  "website": "https://gasf.example.org/explorer-grant",
  "email": "explorer@gasf.example.org"
}
```

#### Entidad 2

```json
{
  "sponsor_name": "Global Adventure Sports Foundation",
  "program_name": "2026 Multi-Tier Support Program",
  "amount": "€20,000",
  "deadline": "October 30, 2026",
  "website": "https://gasf.example.org/expedition-grant",
  "email": "expedition@gasf.example.org"
}
```

#### Entidad 3

```json
{
  "sponsor_name": "Global Adventure Sports Foundation",
  "program_name": "2026 Multi-Tier Support Program",
  "amount": "€50,000",
  "deadline": "November 20, 2026",
  "website": "https://gasf.example.org/legacy-grant",
  "email": "legacy@gasf.example.org"
}
```

## Criterios de Evaluación

- **Precisión**: ¿Los datos extraídos coinciden con el texto fuente?
- **Formato**: ¿El JSON es válido y sigue el esquema esperado?
- **Alucinaciones**: ¿Inventó datos que no están en el texto?
- **Grounding**: ¿Puede citar la fuente exacta de cada dato?

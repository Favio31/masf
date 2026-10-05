\# Known Limitations — MASF



\*\*Last updated\*\*: 2026-10-05



\---



\## 1. Single-entity extraction only



\*\*Status\*\*: Identified · Phase A  

\*\*Severity\*\*: Medium  

\*\*Impact\*\*: Documents containing multiple grant opportunities (multi-tier programs) are not fully parsed.



\### Symptom

When a source document contains multiple funding tiers (e.g., Tier 1: €15,000, Tier 2: €20,000, Tier 3: €50,000), the current prompt schema returns either:

\- Only the first tier (SmolLM2 behavior)

\- Null/zero values due to schema confusion (Qwen3 behavior)



\### Root cause

The canonical prompt and Pydantic schema are designed for single-entity extraction. The model receives no instruction to return a list of objects.



\### Workaround

Split multi-tier documents into separate fixtures before processing.



\### Planned fix (Phase B)

\- Add `multi\_entity: bool` flag to the prompt

\- Update schema to support `List\[SponsorPayload]`

\- Implement chunking strategy by tier/section

\- Target: support documents with up to 10 opportunities



\### Test evidence

See `fixtures/stress\_test\_multitier.txt` (synthetic data, marked as stress test).


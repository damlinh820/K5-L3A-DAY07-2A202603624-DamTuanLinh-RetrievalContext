# Day 6 inventory

Inspected local repository: `D:\AI20K\day7\K5-L3A-DAY06-2A202603624-DataIngestion`.

## Corpus and benchmark

| Path | Type / rows | SHA-256 | Notes |
|---|---:|---|---|
| `data/manifest.json` | JSON, 324 lines | `CCA1B7581DB7120688E3C5352AA08F9B694D95EA8ABCE01B1218E3EDC511A051` | Corpus/source manifest |
| `results/pages.jsonl` | 255 rows | `A2EED46527C9E22678EFDE4F3068DB3C8DCB6D9CC7D8DB87C69AD06DC6F3A92D` | Page text snapshot |
| `results/chunks_C.jsonl` | 1,137 rows | `761C7126C47F6AD81EF3CB7AB034CC7A2C22DD84A42D358ED31B8D75A3D9114E` | Selected Điều/Khoản corpus |
| `benchmark/questions.jsonl` | 20 rows | `FA49A88CD96AD388B778E1CC91F77AC928BE0B05E211CDFA8F58FD85DD367F8C` | 15 dev / 5 test, answerable cases |
| `benchmark/protocol.json` | JSON, 37 lines | `105241B7468EFD6D43DA9CF68460E38AEDCCAACCE8DDEF3370FD0F95A8522132` | Locked protocol |

The question schema is `id, split, type, question, expected_answer, gold_source_id, gold_page, evidence_quote, gold_evidence, filter, legal_locator, human_review`. The chunk schema includes `chunk_id, config, document_id, source, part, page, page_end, article, chapter, section, clause, unit_type, text, n_tokens, provenance, context_provenance`.

## Locked retrieval configuration

- Corpus: three continuation PDFs of Luật Đất đai 31/2024/QH15, 253 pages with text.
- Selected configuration: C, article then clause, preserving article heading; threshold 512 tokens.
- Embedding: `openai/text-embedding-3-small`, 1536 dimensions.
- Store: persistent Chroma, cosine metric; collections `land_law_a`, `land_law_b`, `land_law_c`.
- Baseline benchmark selection in Day 6: C, Hit@3 13/15 dev and 4/5 test. These are historical Day 6 results, not Day 7 results.
- Day 6 already records AI-assisted audit labels and explicitly says independent student verification is pending; they must not be relabeled as human-verified.

## Relevant source files

- `src/embed.py`: OpenRouter embedding client, cache, dimension validation and usage ledger.
- `src/store.py`: Chroma persistent store, metadata and cosine search.
- `src/retrieve.py`: validates returned IDs, text and metadata against the approved snapshot.
- `src/run.py`: reproducible Day 6 preparation/embedding/index/retrieval workflow.
- `results/CHUNKS_LOCK.json`: chunk lock metadata, SHA-256 `A9D0D756EE70A546CF8AF496BA4F04BFD14CBCD04E2DE922BF5911FB9A8B727E`.
- `results/embedding_probe.json`: embedding probe, SHA-256 `9C523F6F5AEB340BAA027C71BAE2D81C5F32C729A8B78634521FC554F3939107`.
- `results/store_probe.json`: store probe, SHA-256 `54434248F61FD186F66E5B9896DA0E65CF2B87C28CA2E1AC2A3E239ABD82A198`.

## Availability and constraints

At Phase 0 only the immutable JSONL snapshots and benchmark were available;
the Day 6 clone omitted its persistent Chroma directory and embedding cache.
Day 7 subsequently rebuilt C into `runs/day6_rebuild/chroma`, collection
`day6_c_dense` (1,137 records), using the same model/dimensions/cosine metric.
The provider reported 306,697 tokens / $0.00613394; manifest records the corpus
hash and all batch usage. The local `.venv` uses Python 3.11.9. Keys are read
from the user's local `.env` and are not included in this inventory or Git.

No Day 6 files were modified by this phase.

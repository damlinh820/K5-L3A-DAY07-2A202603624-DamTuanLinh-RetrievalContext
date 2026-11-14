# PLAN.md — LAB 7 Agentic RAG: Retrieval & Context Engineering

> **Execution contract for Codex** · Phương án A (core only) · 2026-11-14  
> **Day 6 source:** https://github.com/damlinh820/K5-L3A-DAY06-2A202603624-DataIngestion  
> **Day 7 assignment (verify actual repository and linked documents):** https://github.com/VinUni-AI20k/K5-L3-Day07-Retrieval-Context-Engineering  
> **Status:** IMPLEMENTATION PLAN — not evidence that any experiment has been run.

## 0. Mission and non-negotiable rules

Build a **reproducible, auditable Vietnamese legal-domain Agentic RAG system** that extends Day 6 instead of silently replacing its corpus, embeddings, benchmark, or retrieval results. Compare **Dense / BM25 / Hybrid RRF**, add **Hybrid + reranker** as an improvement experiment, construct a real tool-using LLM agent, evaluate retrieval, context, answer grounding, citations, abstention, latency and cost, and provide a polished **local HTML demo** backed by actual results.

**Do not fabricate** results, references, logs, human judgments, benchmark labels, API calls, source pages, costs, or screenshots. **Do not mark an AI-generated judgment as human-verified.** Never leak test cases into development selection. Keep Day 6 source files and original labels immutable. No bonus multimodal pipeline in scope.

**Source-of-truth precedence:** (1) Day 7 official README and its linked GUIDE/RULES/BENCHMARK/CHECKPOINTS/RUBRIC/SUBMISSION or equivalent; (2) actual Day 6 repository files; (3) this plan. If the official instructions conflict with this plan, implement the official requirements and document the difference in `docs/requirement_matrix.md`. If inaccessible, do not claim verification; create an explicit blocker and continue only safe, reversible setup work.

**Required Codex behavior:** inspect repo before coding; do not assume names/paths/commands; execute phases in order; use deterministic seeds; write minimal maintainable Python 3.11 code; log changes; run tests after each phase; stop at each HUMAN GATE rather than approving it yourself. If secrets/data unavailable, provide a reproducible dry-run with clearly marked synthetic fixtures, not fake real metrics. No `git push`, no destructive cleanup, no paid API calls above a configurable budget without user approval.

## 1. Phase 0 — Repository reconnaissance and compliance (must run first)

1. Inspect current working directory, git status, branch, Python environment, file tree, requirements, existing code, artifacts, README and docs. **Do not overwrite uncommitted work.**
2. Fetch/read the official Day 7 README **and every relevant linked instruction document**. Record canonical links, commit SHA/date, exact required artifacts, rubric, allowed AI use, prohibited AI use, mandatory human reviews, number/split of cases, required model/tool usage, submission structure, checkpoints, and any limitations. Inspect Day 6 README and relevant source scripts/data/config/benchmark/metadata schema. If repositories are private/unreachable, ask user to supply them rather than inventing contents.
3. Build `docs/requirement_matrix.md`: `requirement | official source/link/section | implementation path | verification command | status | human approval?`.
4. Build `docs/day6_inventory.md`: path, file type, row count, hash, schema, corpus ID, PDF/text provenance, chunk strategy A/B/C, metadata, embedding model/dimension, Chroma collection, benchmark split, index persistence, existing scripts and runnable commands. Check Day 6 dataset availability and local index compatibility.
5. Record explicit deviations between this plan and official assignment. **Block code changes that violate official rules.**

**Exit:** verified requirements matrix and inventory; no assumptions about repo layout remain.

## 2. Target architecture and scope

```
Day 6 PDF/text snapshot + immutable metadata
       ├── existing Chroma dense index (or documented deterministic rebuild)
       └── same eligible chunk corpus -> BM25 index
User query -> query normalization (minimal, preserve original) -> retrieval mode:
       A dense top-k
       B BM25 top-k
       C hybrid RRF (dense + BM25, dedup by stable chunk_id)
       D hybrid candidate top-N -> reranker -> final top-k [improvement]
       -> context builder (token budget, dedup, ordering, metadata/citation)
       -> single tool-calling LLM agent (bounded calls)
       -> grounded response OR explicit insufficient-evidence abstention
       -> citation validator + trace recorder
       -> evaluation / local HTML comparison demo
```

**Fair comparison:** same frozen corpus version, chunk granularity, gold queries, top-k final context, generator model, prompt, temperature, context token budget and evaluator. Only retrieval strategy changes in A/B/C. Compare D separately as rerank enhancement. Do not mix different Day 6 chunk strategies into the primary retrieval comparison; use the Day 6 selected **Điều/Khoản** corpus if confirmed in repo. Preserve source identifiers and article/clause hierarchy.

**Legal-scope caution:** this is a retrieval exercise over a fixed snapshot, **not** an authoritative statement of current law. Distinguish document enactment/publication/effective dates and corpus coverage. If user asks about later changes (e.g. 2027) or other laws not indexed, state the scope limitation; never claim absence of evidence means legal nonexistence. Do not invent supersession/amendment relationships. Exact article/clause references must be grounded in the source text.

## 3. Suggested deliverable structure (adapt to existing repo, don't duplicate existing functionality)

```
README.md
plan.md
pyproject.toml OR requirements.txt
.env.example                     # placeholders only
configs/{default,experiments}.yaml
src/lab7/
  __init__.py
  config.py                     # typed validation + environment settings
  schemas.py                    # Query, Chunk, Evidence, Answer, Trace
  ingestion.py                  # reuse Day 6 snapshot, validate provenance
  store.py                      # persistent Chroma adapter
  bm25.py                       # Vietnamese-aware lexical index
  retrieval.py                  # dense, lexical, RRF
  rerank.py                     # optional rerank with fallback
  context.py                    # context budget + source formatting
  tools.py                      # structured tool interfaces
  agent.py                      # bounded real LLM tool calling
  citation.py                   # citation integrity checks
  evaluation.py                 # retrieval, answer, abstention metrics
  trace.py                      # JSONL audit log + run manifest
  cli.py                        # build/eval/serve/demo commands
  api.py                        # FastAPI backend for local demo
benchmarks/{day6_original,lab7_dev,lab7_test}.jsonl
benchmarks/SCHEMA.md
reviews/{human_review_template,review_log}.csv
scripts/{audit_day6,build_index,run_experiments,export_demo}.py
tests/{test_ingestion,test_retrieval,test_rrf,test_context,test_citations,test_agent,test_eval,test_api}.py
runs/                            # ignored/generated; publish safe samples only
reports/{dev_failure_analysis,comparison,final_report}.md
docs/{requirement_matrix,day6_inventory,architecture,runbook,limitations}.md
web/                             # HTML/CSS/JS, no fabricated metrics
```

Use the repo's conventions when present. `.gitignore`: `.env`, credentials, local caches, large vectors, raw sensitive inputs, transient runs. Include provenance/hash manifests and safe artifact examples; do not accidentally commit binary indices or secrets.

## 4. Phase 1 — Freeze Day 6 and create the evaluation dataset

### 4.1 Dataset contract
- Inspect actual Day 6 question JSON/CSV schema and migrate by **copy**, never mutate original. Preserve original IDs, gold evidence, original split and source citations; record migration provenance.
- Expected design **if official instructions confirm**: 24 total questions = 20 answerable (15 dev / 5 test) + 4 insufficient-evidence (2 dev / 2 test), yielding 17 dev / 7 test. **Official benchmark wins if different.**
- Each case: `case_id`, `question`, `split`, `answerability` (`answerable|insufficient_evidence`), `expected_evidence_ids`, `source_document_ids`, `gold_article`, `gold_clause`, `gold_pages`, `reference_answer` (optional), `gold_status` (`pending_human_review|human_verified`), `reviewer`, `review_timestamp`, `review_reason`, `corpus_hash`, `notes`.
- Gold references must be validated against actual source chunks and, when needed, PDF page text. Do not treat the AI-generated reference answer as final gold.
- Insufficient-evidence cases must be **genuinely outside corpus coverage** after a human checks full corpus/search, not merely absent from top-3. Include examples covering future-law amendments, outside-scope documents or unavailable details, but only after human verification. Do not use test examples in prompts or dev error analysis.
- **HUMAN GATE H1:** user reviews source pages, gold IDs, answerability and four insufficient-evidence cases. Freeze a `benchmark_manifest.json` with hash, date, approval status. Until approved, evaluation results are `provisional`, not final.

### 4.2 Ingestion/data integrity
- Verify PDF extraction is textual vs OCR only from actual PDF inspection; don't assert it without evidence.
- Stable chunk ID = hash(document version + source location + normalized chunk text + chunk strategy). Avoid cross-run unstable sequential IDs.
- Required metadata where available: `document_id`, `title`, `document_number`, `article`, `clause`, `page_start`, `page_end`, `source_path`, `source_hash`, `chunk_strategy`, `effective_date` **only if verifiable**, `ingestion_version`.
- Validate nonempty text, duplicate IDs, missing source references, page boundaries, embedding dimension, collection metric, stale index. Emit a QA report and fail fast on schema errors.

## 5. Phase 2 — Implement retrievers and controlled comparison

### A. Dense (Day 6 baseline)
- Reuse confirmed embedding provider/model and Chroma collection; if missing, rebuild from frozen chunks only after checking API availability/cost. Never silently swap model/dimension.
- Query embedding with the **same** embedding model and preprocessing; cosine metric consistent with index. Return ranked `Evidence` with score, ID, metadata, source text.

### B. BM25
- Index **exactly the same chunks**. Implement deterministic Vietnamese tokenization: choose `underthesea`/`pyvi` if installable, otherwise explicitly documented Unicode-aware fallback; test accented text, `Điều 45`, numbers, abbreviations, punctuation and casing. Use `rank_bm25` or transparent equivalent.
- Persist index metadata/corpus hash; rebuild when source changes. Return comparable evidence schema; do not pretend BM25 scores are cosine scores.

### C. Hybrid RRF
- Retrieve candidate pool from each retriever (e.g. 10–20, configurable), dedup on stable `chunk_id`, then fuse ranks using `sum(1/(rrf_k+rank))`, default `rrf_k=60`, rank starts at 1. Preserve per-source ranks/scores and final RRF score in trace. Deterministic tie-break by chunk ID.
- If one backend fails, **surface the failure**, mark degraded mode, and do not silently label it normal hybrid.

### D. Reranking improvement
- For Hybrid candidate top-N, apply a separately configurable cross-encoder or API reranker **only if available and approved**; otherwise mark D `not_run` and preserve baseline A/B/C. Use multilingual/Vietnamese-capable reranker and record exact model/revision, latency, token/cost where applicable. Don't assume a GPU model fits memory. Compare top-3 final context fairly.
- Optional improvement experiment #2: **metadata-aware source lookup or article/clause expansion** with strict token budget and citations; enable only if official assignment requires two distinct improvement configurations. Do not call changing `top_k` alone a new retrieval method.

### Retrieval acceptance tests
- Same query/corpus -> deterministic ordered IDs.
- Dense/BM25/Hybrid return unique, valid chunk IDs and bounded top-k.
- RRF unit test with hand-calculated ranks, missing backend, ties, duplicates.
- Vietnamese tokenization tests; exact article number and synonym/paraphrase queries.
- No index mutation during evaluation; index/corpus hashes logged.

## 6. Phase 3 — Context engineering and Agentic RAG

### Context builder
- Select final top-k (default 3, configurable), dedup, apply hard context token budget with actual tokenizer where possible, preserve complete source identifiers. Avoid arbitrary mid-sentence cuts of legal exceptions. Prefer section-aware truncation and record dropped evidence.
- Format each block: `[EVIDENCE_ID] document / Điều / Khoản / page / exact excerpt`. Distinguish evidence text from instructions; treat retrieved documents as **untrusted data** to resist prompt injection.
- Detect missing metadata; never synthesize page numbers or dates.

### Agent design
- One real LLM with tool calling (use existing approved provider/config; no hardcoded credentials). Tool schemas with validated arguments: `dense_search(query,k)`, `bm25_search(query,k)`, `hybrid_search(query,k)`, `lookup_article(article,clause?)` if metadata supports it. For controlled experiments, support `forced_mode` that limits search to selected retrieval strategy; for separate agent demo, allow autonomous routing.
- **Bounded loop**: maximum 2 retrieval rounds / 4 tool calls (configurable); explicit timeouts, retries with backoff, rate limits, token and dollar budget; handle provider errors without fabricating answer.
- System prompt in versioned file: answer in Vietnamese, only from retrieved corpus, preserve qualifications and exceptions, cite evidence IDs, never use unsupported claims, say `Không đủ bằng chứng trong bộ dữ liệu hiện có để kết luận...` when appropriate, and state corpus scope.
- Structured answer: `answer`, `citations[]`, `abstained`, `limitations[]`, `tool_trace_id`, `model`, `prompt_version`, `retrieval_mode`.
- Citation validator: (1) syntactic ID present in supplied context; (2) cited excerpt exists; (3) **semantic support requires separate human review**. Do not mislabel (1) as full correctness.
- For fair A/B/C comparison, prefer **fixed single retrieval call + same generator prompt** in the benchmark. Evaluate autonomous tool-routing separately to avoid conflating retrieval quality with routing decisions.

## 7. Phase 4 — Evaluation design and experiment protocol

### Protocol
1. Run unit/integration tests and a tiny smoke set first.
2. Use **dev only** to compare A/B/C, identify >=2 genuine failure cases, propose and test >=2 improvement configurations (e.g. D rerank, metadata expansion), report negative results honestly.
3. Record baseline and improvement metrics for each case. Keep frozen generator settings; set temperature=0 when supported, seed where supported; note residual nondeterminism.
4. User reviews dev findings and selects final configuration; record `selection_reason`, config hash and timestamp. **HUMAN GATE H2** before opening test.
5. Run **test once** on frozen config and benchmark; do not retune based on test. Report all failures and caveats. If test accidentally used for tuning, disclose and re-establish a clean holdout.

### Required metrics and precise denominators
- `Hit@1`: answerable cases where top-1 contains accepted gold evidence / number of answerable cases.
- `Evidence Hit@3`: answerable cases with at least one gold evidence in top-3 / number of answerable cases. If gold requires multiple complementary excerpts, also report `all_required_evidence@3` separately.
- `Context Evidence Rate`: answerable cases with sufficient source evidence in final supplied context / reviewed answerable cases; human review for semantic sufficiency.
- `Citation ID Validity`: citations pointing to actually supplied evidence / total emitted citations; automatic structural check.
- `Citation Support Rate`: human-reviewed supported citations / human-reviewed citations; never conflate with ID validity.
- `Grounded Answer Score`: human rubric 0=unsupported/incorrect, 1=partially supported/incomplete, 2=correct and sufficiently supported; report mean and counts by class.
- `Abstention precision/recall`: based on frozen `insufficient_evidence` gold; confusion matrix, false abstentions and false confident answers. Also show answerable vs unanswerable separately.
- `Latency`: p50/p95 end-to-end and retrieval; `cost`: input/output tokens and actual provider prices when available, otherwise `unknown` (never invented).
- `Tool compliance`: correct tool schema/routing and bounded calls, separately from retrieval metrics.
- Report sample size `n`, confidence limitations, per-case traces, failed API calls, no silent dropping. Handle zero denominator as `N/A`, not 0%.

### Human review protocol
- `reviews/human_review_template.csv`: `case_id,run_id,reviewer,reviewed_at,source_verified,evidence_sufficiency_0_2,grounded_answer_0_2,citation_support_0_2,abstention_correct,notes,status`.
- AI can prefill **suggestions** in separate fields prefixed `ai_suggestion_`; it cannot fill reviewer/verified status or approve itself.
- User checks original law source, omitted legal exceptions, exact article/clause and any time scope. Keep adjudication notes.
- **HUMAN GATE H3:** review final answer quality and citation support before final report claims human-verified results.

## 8. Phase 5 — Local HTML demo (real data, no decorative fake charts)

Build a responsive, clean **Vietnamese HTML/CSS/JS demo** with FastAPI local backend. Must work on Windows 11, Python 3.11; no mandatory paid hosting or CDN. Features:
1. Input question, choose retrieval mode `Dense / BM25 / Hybrid / Hybrid+Rerank`, run query, show agent answer/abstention and evidence citations.
2. Side-by-side comparison of three retrieval modes for the same query: ranked chunks, article/clause/page, retrieval scores **with score types labeled**, highlighted matched evidence IDs, latency and context size.
3. A benchmark dashboard reading **real run artifacts only**: dev/test split, Hit@1, Evidence Hit@3, grounded scores, citation support, abstention confusion matrix, latency, cost; clearly label `provisional`, `human_verified`, `not_run`, `unavailable`.
4. Expandable trace panel: model/provider, config hash, prompt version, tool calls, retrieved IDs, rerank positions, final context, token/cost when available, errors.
5. Examples: one answerable, one insufficient evidence, one failure analysis; use real benchmark IDs and approved examples, not fake results.
6. If backend/API/index missing, show actionable setup error and optionally **explicit fixture mode** (`DEMO_FIXTURE_MODE=1`), never present fixtures as measured results.
7. Security: do not expose `.env`/API keys or arbitrary local file reads; validate query length and mode; use safe HTML rendering (escape retrieved text); CORS localhost only.

Acceptance: launch with one documented command; browser opens local app; all metrics trace to run JSONL/CSV; screenshots optional, clearly generated from real demo.

## 9. Phase 6 — Reports, reproducibility, and submission

Generate:
- `reports/comparison.md`: corpus/index fingerprint, configs, model names, retrieval metrics table, dev comparison, two dev failures (query, expected vs retrieved, root cause, proposed fix, measured outcome), tradeoffs and limitations.
- `reports/final_report.md`: requirement-by-requirement evidence, methodology, human-review status, frozen choice, untouched test outcomes, grounded answer/citation/abstention evaluation, error analysis, cost/latency and lessons learned. Distinguish machine-derived vs human-reviewed metrics.
- `docs/runbook.md`: Windows PowerShell + cross-platform instructions, environment creation, `.env`, dependency installation, Day 6 data placement, index validation/rebuild, CLI commands, tests, experiment run, local web demo, troubleshooting.
- `README.md`: quick start, architecture, real results with trace links, known limitations, compliance matrix link, exact submission commands. Follow official submission naming/structure if different.
- `runs/<run_id>/manifest.json`: UTC timestamp, git SHA, corpus/index/benchmark hashes, code/config/prompt versions, model IDs, seed, dependency lock, cost settings, approval status. `retrieval.jsonl`, `agent.jsonl`, `metrics.json`, `errors.jsonl` as applicable.
- CLI subcommands such as `audit-day6`, `build-index`, `validate-benchmark`, `eval --split dev --mode dense|bm25|hybrid|rerank`, `eval --split test --frozen-config ...`, `serve`. Validate command names against actual implementation.

## 10. Engineering quality, test matrix and guardrails

- Unit tests: BM25 Vietnamese segmentation; RRF rank math and deterministic ties; citation IDs; context truncation; score schema; empty/no-answer queries; date scope; duplicate chunks; invalid metadata; no-gold denominator; API failures; malicious instruction inside retrieved excerpt.
- Integration tests: Chroma retrieval with small **clearly marked fixture**; fake/mock LLM tool calls; FastAPI endpoints; persistence and manifest hashes.
- Live smoke test: only with configured provider and budget approval; save exact run ID and error logs.
- Quality gates: formatter/linter/type checks if installed; `pytest`; JSON schema validation; no plaintext secrets; all required commands documented; no unhandled exceptions in UI.
- Dependency versions pinned or locked. Reuse existing stack, avoid needless LangChain/LangGraph unless justified by current repo. Prefer standard Python, `chromadb`, `rank-bm25`, `fastapi`, `pydantic`, `pytest`, HTTP/provider SDK as needed.
- Provider fallback: do not silently change embedding model, generator, or reranker. Missing API key => explicit `provider_unavailable` and no false final score.
- Resource constraints: design to work on CPU for BM25/Chroma and use remote API for LLM where permitted; optional GPU rerank must have CPU/off switch. Cache embeddings and queries with fingerprint, never cache secret headers.
- Trace privacy: redact secrets, avoid logging private user data, keep legal corpus references clear.

## 11. Checkpoints, human gates and definition of done

| Checkpoint | Codex must deliver | User action | Pass condition |
|---|---|---|---|
| C0 | Official requirement matrix + Day 6 inventory | Confirm corpus/source | Requirements verified; unknowns explicit |
| C1 | Migrated benchmark + source references | **H1** review gold and insufficiency | Approved immutable benchmark hash |
| C2 | A/B/C retrievers, tests, dev metrics | Review comparison | Same corpus, fair configs, traceable results |
| C3 | Agent + context + citation checks + 2 improvements | Review dev failure analysis | Bounded real tool calls, evidence gate works |
| C4 | Frozen dev selection manifest | **H2** approve choice | No test leakage |
| C5 | Test run, human review template, audit | **H3** review semantic labels | Results separated by verification status |
| C6 | HTML demo, reports, runbook, final tests | Approve submission | Reproducible run, all official files present |

**Definition of done:** all official mandatory criteria checked with links to artifacts; A/B/C compared on identical Day 6 corpus; improvements honestly measured; real agent/tool-calling works when configured; no fabricated scores; test untouched until H2; human approval traceable; demo reflects real run artifacts; reproducible setup; all tests pass or documented blockers; repository ready for user review, **not automatically pushed**.

## 12. Codex execution instructions — follow exactly

1. Read this entire file, then **verify** official Day 7 linked docs and Day 6 repo source files; summarize discovered requirements and actual paths in `docs/requirement_matrix.md` and `docs/day6_inventory.md`.
2. Create a brief `docs/implementation_status.md` with task checklist, blockers, completed tests, exact commands and run IDs. Update it after each phase. Do not stop to ask about minor implementation preferences; use safe defaults and document decisions.
3. Implement phases 1–6 incrementally; run tests and log output after each; preserve existing files; no rewriting gold/benchmarks in place. Keep implementation modular and readable, with meaningful docstrings.
4. At H1/H2/H3, **STOP** for user verification if the next step depends on human approval. You may continue independent tasks (e.g. unit tests or UI skeleton), but do not claim approval or run final test before H2.
5. On missing data, credentials, unavailable official docs or failed dependencies: create an explicit blocker with path, command, error, exact remedy; do not fabricate. Continue safe tasks that do not require the blocker.
6. Final Codex response must include: files created/modified, runnable commands, tests passed/failed, real metrics with run IDs or `not_run`, pending human gates, blockers, and exact next action for user. **Do not claim complete until all gates actually pass.**

### Suggested first Codex prompt

> Read `plan.md` fully. Start at Phase 0: inspect repository, official Day 7 README and all linked instruction files, plus Day 6 repository and artifacts. Create `docs/requirement_matrix.md`, `docs/day6_inventory.md`, and `docs/implementation_status.md`. Then implement the plan in order without changing Day 6 original data or inventing metrics. At every HUMAN GATE, stop for my explicit confirmation. Run tests and record real results. Follow the official assignment over this plan if there is any discrepancy. Do not push commits or spend paid API budget without approval.

---

**Important:** The numerical benchmark split, Day 6 corpus configuration, and expected Day 7 rubric described above are **planning assumptions drawn from prior conversation** until Codex independently verifies official repo files. All such assumptions must be validated during Phase 0 and updated in the requirement matrix, not treated as already checked.

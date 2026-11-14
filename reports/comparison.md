# Day 7 dev retrieval comparison

**Cập nhật cuối: H1/H2/H3 đã hoàn tất.** Người học xác nhận cả 14 nhãn trong
`final_holdout_v1`; nhãn cuối ở `reviews/verified/`, biên nhận ở
`reviews/final_holdout_v1_confirmation.json` (tính từ gốc repo).
Các đoạn đề xuất/pending bên dưới ghi lại quy trình trước xác nhận; không còn là bước đang chờ của test này.

Run artifacts: `runs/phase3_dev_improvements/summary.json` and `traces.json`.
The run used the frozen Day 6 C corpus (1,137 chunks), 15 answerable dev
questions, the same final top-3 cutoff and the same gold evidence. Test was not
read by this experiment.

| Configuration | Hit@1 | Evidence Hit@3 | Change |
|---|---:|---:|---|
| Dense | 10/15 (66.7%) | 13/15 (86.7%) | Day 6 embedding + Chroma |
| BM25 | 14/15 (93.3%) | 14/15 (93.3%) | Offline lexical baseline |
| Hybrid RRF | 14/15 (93.3%) | 15/15 (100%) | Dense+BM25, candidate 10, RRF k=60 |
| Improvement 1: Hybrid RRF candidate pool 20 | 13/15 (86.7%) | 14/15 (93.3%) | Dense10 + lexical20 |
| Improvement 2: Hybrid + lexical rerank | 12/15 (80.0%) | 14/15 (93.3%) | Query-term coverage + exact article bonus |

## Failure analysis

- Dense missed `q03` (definition of chiếm đất) and `q08` (exception in Điều 45); lexical matching recovered both, suggesting exact legal terminology and article-specific wording mattered for this snapshot.
- BM25 missed `q01`, a broad scope question; lexical overlap was insufficient for the document-level summary.
- Hybrid RRF recovered all 15 top-3 evidence cases. The two improvement configurations degraded Hit@1, so they are not selected.

## Selection decision

Retain Hybrid RRF with candidate pool 10 and `rrf_k=60`: it is the only tested
configuration with Evidence Hit@3 15/15. The two negative experiments remain
documented. This is a dev selection only; no test result has been used.

Embedding usage for the rebuild was 306,697 tokens / `$0.00613394`; the dev
query embedding call used 792 tokens / `$0.00001584`.

## Five-way improvement run

The combined pipeline added query transformation, metadata-aware article/clause
boosting, same-article neighbor expansion, score-aware context ordering and a
prompt rule distinguishing missing evidence from relevant evidence. On the
same 15 dev answerable cases it achieved Hit@1 `15/15` and Evidence Hit@3
`15/15`. The real agent rerun is in `runs/agent_dev_all5/all_traces.json`;
17/17 calls completed with no system errors, but that script still used the
original retrieval pipeline with a new prompt. Its folder name must not be read
as proof that all five retrieval changes ran through the agent. The shared
pipeline and real tool agent below supersede it.

## Actual tool-calling agent on dev

Run `tool_agent_dev` uses model-emitted search calls and role=tool responses on
the same 17 cases, model, temperature and context budget.

| Mode | Hit@1 | Hit@3 | Context exact (machine) | Errors | Insufficient abstention |
|---|---:|---:|---:|---:|---:|
| Dense | 10/15 | 13/15 | 13/15 | 0/17 | 1/2 |
| BM25 | 14/15 | 14/15 | 14/15 | 0/17 | 1/2 |
| Hybrid RRF | 14/15 | 15/15 | 15/15 | 0/17 | 1/2 |
| Hybrid improved (first run) | 15/15 | 15/15 | 15/15 | 1/17 | 1/2 |

The first improved run exposed quote-capitalization failure on q11 and an
out-of-jurisdiction answer on q22. Subsequent dev fixes restore exact source
capitalization, explicitly state corpus scope and apply a narrow scope guard.
A live demo smoke check also found model-requested/executed query mismatch;
controlled mode now constrains the tool schema to the original query.

Final dev run: `runs/tool_agent_submission_dev/hybrid_improved`.
Hit@1/Hit@3/context exact are 15/15; 17/17 search use; 15 answered, 2 abstained,
0 errors, no answerable abstentions. Human grounded/citation labels for these
new outputs remain pending. p50/p95 4,27/5,73 sec; 42,210 input + 4,584 output
tokens; estimated chat cost $0.0090819 (not invoice/billed cost).

## Test metric audit

`reports/recomputed_retrieval.json` recalculates the exact same stored rankings
using original page provenance. Dense Hit@3 rises 3/5 to 4/5, BM25 Hit@1/Hit@3
2/5 and 2/5 to 4/5 and 4/5, Hybrid Hit@3 3/5 to 4/5. The old calculation
incorrectly required evidence page to equal the chunk's first page. No ranking,
gold label or historical artifact was changed by this audit.

The original test has been used for debugging. A new 5+2 holdout was approved
under H1/H2 and executed once in `runs/final_holdout_v1`. Dense Hit@1/Hit@3 is
4/5 and 4/5; Hybrid improved is 3/5 and 4/5; both context exact 4/5 and
insufficient abstention 1/2. Hybrid has one validation error. This test does
not show Hybrid outperforming Dense. Source/answer/citation proposals for all
14 outputs are in `reviews/final_holdout_v1_H3.md`; H3 is pending and no
inference code was retuned after observing these results.

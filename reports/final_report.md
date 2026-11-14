# Báo cáo lịch sử — trước cấu hình tool-agent cuối

**Cập nhật cuối: H1/H2/H3 đã hoàn tất.** Người học xác nhận cả 14 nhãn trong
`final_holdout_v1`; nhãn cuối ở `reviews/verified/`, biên nhận ở
`reviews/final_holdout_v1_confirmation.json` (tính từ gốc repo).
Các đoạn đề xuất/pending bên dưới ghi lại quy trình trước xác nhận; không còn là bước đang chờ của test này.

Báo cáo hiện tại để nộp là [báo cáo cá nhân](../report/individual/2A202603624_DamTuanLinh.md).
Các bảng gốc bên dưới giữ để đối chiếu lịch sử; không phải điểm test của
pipeline cuối. Trạng thái mới nhất nằm trong [checklist](../docs/FINAL_CHECKLIST.md).

## Frozen setup

- Corpus: Day 6 configuration C, 1,137 chunks, three Luật Đất đai 31/2024/QH15 PDF parts.
- Embedding: `openai/text-embedding-3-small`, 1536 dimensions; Chroma cosine index rebuilt locally at `runs/day6_rebuild/chroma`.
- Generator: OpenAI `gpt-4o-mini`.
- Frozen retrieval: Hybrid RRF, candidate pool 10, `rrf_k=60`, final top-3.
- Benchmark: 24 cases, 17 dev and 7 test; test was opened only after dev selection.

## Retrieval metrics

Dev answerable cases (15): Dense Hit@1 10/15, Evidence Hit@3 13/15; BM25 14/15 and 14/15; Hybrid RRF 14/15 and 15/15.

Test answerable cases (5): Dense Hit@1 1/5, Evidence Hit@3 3/5; BM25 2/5 and 2/5; Hybrid RRF 2/5 and 3/5.

## Human-reviewed agent test

| Class | Count |
|---|---:|
| Test answerable grounded 0 | 3/5 |
| Test answerable grounded 1 | 0/5 |
| Test answerable grounded 2 | 2/5 |
| Test insufficient-evidence abstention correct | 2/2 |
| Test system errors | 0/7 |

The original run abstained on `q16`, `q17`, `q19`. A later audit corrected the
original review explanation: q17 did not contain the required duration evidence
in its context (it retrieved area-limit clauses instead). q19 had evidence but
failed the citation-marker check. q16's old raw model response was not retained,
so the precise generation/validation cause cannot be reconstructed.
`q18` and `q20` answered correctly with supported citations.

## Diagnostic follow-up (exposed test)

See `reports/diagnostic_3q.md` and `runs/case_diagnostic_final`. After general
retrieval/format fixes, q16/q17/q19 produce substantive answers with matching
citations/excerpts and q23/q24 still abstain. The user confirmed the new q16/q17/q19
outputs: all three received context, grounded-answer and citation-support grade
2/2. Supported citations are 3/3 for that reviewed subset. These labels are keyed
to `case_diagnostic_final` in `reviews/review_log.csv`; the confirmation records
the original trace hash. q23/q24 remain unreviewed for this new run.
This replay was used for debugging and is not a new independent holdout score.
The historical test scores above are preserved; results from different runs
must not be pooled into a claimed 5/5 test score.

## Limitations

- Citation support and groundedness are based on the user-confirmed review log, not an automatic judge.
- At the time of this historical run, the demo displayed artifacts only. The current demo also executes new queries; see the personal report.
- Historical costs: rebuild embedding `$0.00613394`; dev query embedding `$0.00001584`. The current tool-agent records estimated chat cost separately; actual invoice cost remains unknown.
- The benchmark and corpus remain a fixed legal snapshot and are not current legal advice.

## Submission implementation update

The expanded Vietnamese report is
`report/individual/2A202603624_DamTuanLinh.md`. The new production path uses
`src/tool_agent.py` (real model function calls), shared retrieval, FastAPI and
CLI. Latest dev run is `tool_agent_submission_dev/hybrid_improved`: machine
Hit@1/Hit@3/context exact 15/15, search use 17/17, 15 answered + 2 abstained,
0 errors. New grounded/citation labels are not inferred from these statuses.

The old retrieval test metrics above are retained as originally stored. The
provenance-aware audit in `reports/recomputed_retrieval.json` gives Dense 1/5
and 4/5, BM25 4/5 and 4/5, Hybrid 2/5 and 4/5. These are recomputations of
unchanged rankings, not new test runs or improvements obtained by retuning.

Interactive demo, CLI, dependency lock and runbook are implemented. API routes,
assets and a real model-backed query were smoke checked; browser preview was
unavailable due to the computer-use kernel initialization error.

H1/H2 were subsequently approved, and `runs/final_holdout_v1` executed Dense
and Hybrid improved once on the new benchmark. See the personal report for
the measured results and `reviews/final_holdout_v1_H3.md` for 14 pending H3
proposals. Do not treat old review labels as approval of these new outputs.

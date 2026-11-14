# Implementation status

Updated 2026-11-14. Scope: core lab, no multimodal bonus. Code/demo/docs are
implemented; independent test and H3 for both modes are complete.

| Plan phase | Status | Evidence |
|---|---|---|
| 0 Reconnaissance | Done | ASSIGNMENT + linked docs, requirement_matrix, day6_inventory |
| 1 Data/benchmark | Original 24 cases migrated; H1 receipt records 4 insufficient cases, inherited 20 gold rows remain pending | data/benchmark_day7 + review history |
| 2 Retrieval | Done | Dense/BM25/RRF/lexical rerank; real dev artifacts |
| 3 Context/agent | Done | Real function-calling model, controlled/autonomous modes, bounds/trace/validator |
| 4 Evaluation | H1/H2 approved; independent test and all 14 H3 labels confirmed | final_holdout_v1; reviews/verified |
| 5 Local demo | API/assets/live query checked; screenshot QA unavailable | src/api.py + web, localhost 8766 smoke |
| 6 Reports/reproducibility | Report and metrics finalized after H3 | README, runbook, lock, personal report, submission checker |

## Latest dev run

`runs/tool_agent_submission_dev/hybrid_improved` (17 dev cases):

- Model emitted search calls on 17/17 cases.
- Machine Hit@1 / Hit@3 / context exact evidence: 15/15 each.
- 15 answered, 2 abstained, 0 processing errors; no answerable abstentions.
- 42,210 prompt + 4,584 completion tokens. Estimated chat $0.0090819; actual invoice cost unknown.
- Latency p50/p95 4.27/5.73 sec.
- New semantic grounded/citation labels remain pending. Old labels cannot transfer by case ID alone.

Comparable A/B/C tool runs are in `runs/tool_agent_dev`. Keep the q11 output
error and q22 scope error in the first runs; fixes were chosen using dev.
`reports/comparison.md` gives positive and negative experiments and exact paths.

## Historical results and reviews

- Original corpus C SHA-256 remains
  `761c7126c47f6ad81ef3cb7ab034cc7a2c22dd84a42d358ed31b8d75a3d9114e`.
- Original benchmark has 24 cases (15+2 dev, 5+2 test), hash unchanged.
- Day 6 Chroma was missing in clone; rebuilt separately in Day 7, 1,137 records,
  model/dimension/metric unchanged. Embedding provider reported $0.00613394.
- Original agent test: 2 answered, 5 abstained, 0 errors; reviewed grounded 2/5.
- q16/q17/q19 diagnostic fixes were confirmed by the user for
  `case_diagnostic_final`; receipt binds the original trace hash. Those three
  reviews are not pooled with other runs into an independent 5/5 result.
- Original test rankings were recalculated for multipage provenance without
  rerunning retrieval: Hybrid Hit@3 is 4/5, not stored old 3/5.
- Test has been used for debugging; only the prepared new holdout can provide
  an independent result for the final pipeline.

## Required remaining user action

H1/H2 are confirmed in `benchmarks/h1_h2_confirmation.json`. The approved
snapshot preserves candidate questions/gold and adds review metadata only.
`runs/final_holdout_v1` has completed both modes once. Dense Hit@1/Hit@3 is
4/5 and 4/5; Hybrid is 3/5 and 4/5; both context exact 4/5 and abstention 1/2.
Hybrid has one output-validation error. No pipeline retuning or replacement
test run was performed. User confirmed all 14 H3 labels; receipt is in
`reviews/final_holdout_v1_confirmation.json`, accepted labels in `reviews/verified/`.

Technical follow-up from the final audit is complete: per-citation metrics,
trace-bound prepare/finalize reviews, run-specific benchmark snapshots,
dynamic dashboard, one-time holdout reservation, full text-artifact inventory,
and separate readiness/report-sealing checks. The inference core of the latest
dev run is unchanged. See `reports/technical_completion.md`.

Exact user decisions, the four historical context corrections and optional
dev review proposals are in `docs/USER_CONFIRMATIONS.md`. Pending proposals
do not change verified labels or historical trace files.

## Verification

- Unit, metric, function-call protocol, submission workflow and FastAPI tests: 56/56 pass;
  `reports/verification.json` records the commands and smoke results.
- `pip check`: no broken requirements; compileall passed.
- Submission checker: no missing required files, no detected key patterns in
  source/report/data directories, original benchmark hash valid, no duplicate run/case reviews.
- GUI browser and computer-use tools failed at kernel initialization. No screenshot
  or visual browser QA is claimed. HTTP routes/assets/comparison and model query
  were tested directly.
- Day 6 source/data unchanged; no commit or push performed.

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m src.cli audit-day6
.\.venv\Scripts\python.exe -m src.cli validate-benchmark
.\.venv\Scripts\python.exe -m src.cli summarize
.\.venv\Scripts\python.exe scripts/check_submission.py
.\.venv\Scripts\python.exe web/server.py --open
```

API tests may need to run outside the Windows execution sandbox because asyncio
uses a loopback socketpair. This is not a Python dependency or retrieval error.

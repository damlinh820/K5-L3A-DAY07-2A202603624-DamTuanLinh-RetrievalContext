# Ma trận yêu cầu và bằng chứng

Nguồn đề: [repo Day 7](https://github.com/VinUni-AI20k/K5-L3-Day07-Retrieval-Context-Engineering),
snapshot local HEAD `c67ec6292cd6d15e6e6cbaa2c7e7260398bb5a19`, commit
2026-11-13T22:56:27+07:00. README đề gốc giữ trong `ASSIGNMENT.md`; GUIDE,
RULES, BENCHMARK, CHECKPOINTS, RUBRIC, SUBMISSION, starter/data/report docs đã đọc.
Không tuyên bố đã fetch lại remote hoặc biết deadline ngoài thông báo giảng viên.

| Yêu cầu | Nguồn | Bằng chứng triển khai | Kiểm tra | Trạng thái |
|---|---|---|---|---|
| Dùng dữ liệu/embedding/vector store Day 6 | GUIDE §1 | `src/pipeline.py`, `docs/day6_inventory.md`, `runs/day6_rebuild/dense_manifest.json` | `python -m src.cli audit-day6` | Có, Chroma rebuild riêng, corpus hash giữ nguyên |
| >=3 retrieval, gồm dense | GUIDE §2, RUBRIC | Dense/BM25/Hybrid RRF + lexical rerank + pipeline cải thiện | `runs/tool_agent_dev/*/metrics.json` | Đã chạy dev thật |
| Model thật điều phối tool | GUIDE §3 | `src/tool_agent.py`, model phát function call, role=tool, bounds/budget | `tests/test_tool_agent_api.py`, `runs/tool_agent_submission_dev` | Có; trace fixed-generation cũ không tính là tool calling |
| Context, citation, abstain | GUIDE §3 | `src/context.py`, `src/agent.py`, review log | 56 tests + review theo run/case/trace | Có; nhãn mới không tự kế thừa review cũ |
| 15+2 dev, 5+2 test tối thiểu | BENCHMARK §1 | `data/benchmark_day7/lab7_benchmark.jsonl` | `python -m src.cli validate-benchmark` | Đủ 24; 20 gold kế thừa Day 6, 4 insuff được duyệt |
| Hit@1, Hit@3, CER, thời gian/chi phí | BENCHMARK §2 | `src/evaluation.py`, `reports/metrics.json`, `reports/recomputed_retrieval.json` | `python scripts/recompute_metrics.py`, `python -m src.cli summarize` | Có; CER máy và CER đã review tách riêng; chi phí chat ước tính |
| >=2 cấu hình cải thiện + >=2 lỗi dev | GUIDE §4 | `reports/comparison.md`, candidate20, lexical rerank, scope/quote fixes | Trace + bảng dev thực tế | Có; giữ cả kết quả giảm chất lượng |
| Chọn dev rồi test độc lập | BENCHMARK §1 | Config chốt + approved benchmark + receipt | Hash guard, one-time reservation, final_holdout_v1 | H1/H2 đã duyệt; test mới đã chạy một lần |
| Baseline và cấu hình chọn trên cùng test, review 5+2 | BENCHMARK §2–3 | `benchmarks/fresh_holdout_approved.jsonl`, `configs/final_tool_agent.json` | Dense/Hybrid cùng 7 câu; 14 output | Đã chạy; đề xuất H3 đủ 14, chờ xác nhận |
| Review semantic từng câu test | BENCHMARK §3, plan H3 | `reviews/final_holdout_v1_H3.md`, pending packets | Join đúng run_id + case_id + trace hash | Review cũ giữ nguyên; H3 mới chưa human-verified |
| Local HTML demo | Plan §8 | FastAPI, hỏi đáp live, so sánh, dashboard, ví dụ, trace | API fixture tests + HTTP smoke thật | Route/assets/API đã kiểm tra; browser runtime lỗi nên chưa QA bằng ảnh |
| Tái lập và báo cáo cá nhân | SUBMISSION | README, runbook, requirements lock, `report/individual/2A202603624_DamTuanLinh.md` | `python scripts/check_submission.py` | Code/docs sẵn; còn gate benchmark/test cuối |
| Không secret / không số liệu giả | RULES | .gitignore, scanner chỉ báo tên file, raw traces/cost unknown | submission checker | Đã kiểm tra; không commit/push tự động |
| Bonus multimodal | ADVANCED | Ngoài scope Plan A | N/A | Không thực hiện |

Sau audit đã bổ sung benchmark snapshot theo run, review gắn hash trace và
từng citation, finalize không gọi lại model, guard một lần cho test mới,
inventory đủ prompt/trace và `check_submission.py --ready`. Nhãn gold gốc
q01–q20 vẫn pending theo metadata; biên nhận H1 hiện ghi q21–q24. Không tự
chuyển trạng thái gold kế thừa hoặc các đề xuất review thành human-verified.

## Khác biệt / giới hạn đã xác định

- Đề không bắt buộc FastAPI, số tool, số vòng hoặc token budget cụ thể; các lựa
  chọn này theo plan và được ghi cấu hình.
- Starter chỉ có TF-IDF/mock; không dùng chúng như kết quả agent thật.
- Day 6 chọn corpus C với ID hash gốc. Giữ ID này để nối index và provenance;
  không băm lại ID theo một công thức khác trong plan.
- Reranker hiện là lexical heuristic minh bạch. Cross-encoder/API reranker chưa
  chạy; không ghi nhận nó như thí nghiệm neural rerank.
- Thí nghiệm `candidate20` cũ là pool dense10 + lexical20, không phải cả hai 20.
- Metric cũ so page bắt đầu nên hụt evidence nhiều trang; báo cả số lưu gốc và
  bản tính lại theo provenance, không ghi đè artifacts cũ.
- Test gốc đã mở và dùng debug; bản sửa mới cần test mới để đánh giá độc lập.
- Tài liệu là snapshot 2024, không xác nhận luật đang có hiệu lực ở thời điểm hỏi.

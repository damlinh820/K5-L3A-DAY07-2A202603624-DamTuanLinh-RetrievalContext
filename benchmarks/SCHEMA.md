# Benchmark

Benchmark gốc: `data/benchmark_day7/lab7_benchmark.jsonl`, 24 câu, giữ nguyên.
`fresh_holdout_candidates.jsonl`: 7 câu mới (5 answerable + 2 insufficient),
chưa chạy retrieval/agent, chờ duyệt sau khi code/config được chốt.

- `id`, `split`, `question`, `answerability`: thông tin case. Pipeline runtime
  chỉ nhận `question` và mode/top-k; các trường còn lại chỉ dùng trong evaluator.
- `gold`: source_id, page, evidence_quote; các phần tử là evidence thay thế.
- `expected_evidence_ids`: ID chunk Day 6 làm bằng chứng, không truyền vào agent.
- `gold_status`, reviewer, timestamp: đề xuất để trống đến khi người học xác nhận.
- Câu thiếu bằng chứng: absence_reason + cách kiểm tra toàn corpus.

Evidence nhiều trang được kiểm tra theo provenance; không đòi `chunk.page`
phải bằng gold.page vì page thường là trang bắt đầu chunk.

Phê duyệt benchmark và cấu hình mới là H1/H2; chấm kết quả sau khi chạy là H3.
Không dùng các câu mới để sửa prompt hoặc chọn cấu hình.

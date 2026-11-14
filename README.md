# Day 7 · Agentic RAG — Đàm Tuấn Linh

**2A202603624 · L3A · Python 3.11+ · nối tiếp Day 6**

Agent truy xuất snapshot Luật Đất đai 31/2024/QH15, trả lời tiếng Việt kèm
evidence/citation. Dùng lại 1.137 chunk cấu hình C, embedding
`openai/text-embedding-3-small` 1536 chiều và Chroma cosine của Day 6.

[Báo cáo cá nhân](report/individual/2A202603624_DamTuanLinh.md) ·
[Hướng dẫn chạy](docs/runbook.md) · [Ma trận yêu cầu](docs/requirement_matrix.md) ·
[Đề bài gốc](ASSIGNMENT.md) · [Benchmark mới và biên nhận](benchmarks/REVIEW.md)

[Checklist cuối](docs/FINAL_CHECKLIST.md) · [Các phần cần bạn xác nhận](docs/USER_CONFIRMATIONS.md)

## Mở demo

Chạy từ thư mục repo Day 7, dùng venv đã tạo:

```powershell
cd "D:\AI20K\day7\K5-L3A-DAY07-2A202603624-DamTuanLinh-RetrievalContext"
.\.venv\Scripts\python.exe web/server.py --open
```

Mở `http://127.0.0.1:8765`. Nếu đang chạy server cũ, Ctrl+C rồi chạy lại.
Demo có hỏi đáp thật, chọn phương pháp, so sánh ba retriever, evidence theo
Điều/Khoản/trang, ví dụ đã chạy, dashboard và trace có thể mở rộng.
Xem artifacts không gọi API; hỏi đáp live có gọi API theo ngân sách cấu hình.

## Cài lại / kiểm tra

```powershell
# Khi chưa có venv: dùng Python thật 3.11+ để chạy -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.lock.txt
.\.venv\Scripts\python.exe -m src.cli audit-day6
.\.venv\Scripts\python.exe -m src.cli validate-benchmark
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe scripts/check_submission.py
# Chỉ đạt khi test độc lập và H3 cũng hoàn tất:
.\.venv\Scripts\python.exe scripts/check_submission.py --ready
```

`OPENAI_API_KEY` dùng chat; `OPENROUTER_API_KEY` dùng query embeddings. Giữ
trong .env cục bộ Day 6 hoặc Day 7; không đưa vào Git. Repo Day 6 mặc định nằm
cạnh repo này, có thể đổi DAY6_ROOT. Chroma/cache/binary không nộp; runbook có
lệnh rebuild trong thư mục mới và ghi usage thực tế.

## Kết quả đã đo

So sánh dev trên cùng corpus, model, top-3 và context budget:

| Retrieval | Hit@1 | Evidence Hit@3 |
|---|---:|---:|
| Dense | 10/15 | 13/15 |
| BM25 | 14/15 | 14/15 |
| Hybrid RRF | 14/15 | 15/15 |
| Hybrid cải thiện | 15/15 | 15/15 |

Agent tool-calling cấu hình cuối: 17/17 có gọi search thật, 15 câu answerable
trả lời, 2 câu thiếu evidence từ chối, 0 lỗi xử lý. Context exact evidence
15/15 theo kiểm tra máy; **không đồng nghĩa 15/15 grounded answer đã được chấm**.
Artifacts: `runs/tool_agent_submission_dev/hybrid_improved/metrics.json`.
Độ trễ p50/p95 khoảng 4,27/5,73 giây, chat ước tính $0,00908 cho 17 câu.

Test gốc có Hybrid Hit@3 4/5 khi tính lại theo provenance, so với số 3/5 của
evaluator cũ chỉ so trang đầu chunk. Grounded answer của agent gốc vẫn 2/5 theo
review đã duyệt. Ba case diagnostic q16/q17/q19 sau sửa được duyệt 2/2; các
điểm đó không ghép vào test gốc và không thay cho một holdout mới.

**Test mới đã chạy sau H1/H2:** `runs/final_holdout_v1`, 7 câu cho mỗi mode.

| Cấu hình test mới | Hit@1 | Evidence Hit@3 | Context exact (máy) | Answered / abstain / error |
|---|---:|---:|---:|---:|
| Dense | 4/5 | 4/5 | 4/5 | 6 / 1 / 0 |
| Hybrid cải thiện | 3/5 | 4/5 | 4/5 | 5 / 1 / 1 |

Cả hai abstain 1/2 câu thiếu evidence; h07 trả lời điều kiện chung thay vì
từ chối tình trạng hồ sơ riêng. Dense h02 thiếu nguồn trực tiếp; Hybrid h04
bỏ Điều 151 và output bị validator chặn. Test này chưa cho thấy Hybrid vượt
Dense. Người học đã xác nhận [14 nhãn H3](reviews/final_holdout_v1_H3.md).
Grounded mean 1,6/2 và CER human 4/5 cho cả hai; citation Dense 4/7, Hybrid 6/6.
Biên nhận và nhãn cuối nằm trong `reviews/final_holdout_v1_confirmation.json` và `reviews/verified/`.

Workflow review/test/đóng gói đã được bổ sung: benchmark snapshot theo run,
review gắn trace và từng citation, finalize không gọi lại model, dashboard nhận
run mới và readiness check riêng. Inventory bao phủ mọi run được giữ; xem
runbook để stage đủ prompt và trace. Các nhãn context lịch sử còn cần đính
chính được liệt kê riêng trong phần xác nhận.

## Chạy thí nghiệm

```powershell
.\.venv\Scripts\python.exe -m src.cli ask "Người sử dụng đất có quyền hưởng thành quả lao động trên loại đất nào?" --mode hybrid_improved
.\.venv\Scripts\python.exe -m src.cli eval --split dev --modes dense bm25 hybrid_rrf hybrid_improved --output runs/dev_new --max-run-cost-usd 0.20
.\.venv\Scripts\python.exe -m src.cli summarize
```

Mỗi run dùng thư mục mới. Lệnh test tự chặn khi chưa có approval/hash khớp.
`--diagnostic` chỉ dành cho test đã mở, được ghi rõ như replay trong manifest.
Không tự đổi model/provider hoặc dùng mock khi API lỗi.

## Mã và tài liệu

- `src/`: pipeline, BM25/RRF/rerank, tool-calling agent, validator, metrics, API/CLI.
- `web/`: HTML/CSS/JS local, không CDN, render dữ liệu bằng textContent.
- `configs/`, `benchmarks/`: cấu hình chốt và benchmark cần duyệt.
- `reviews/`: nhãn gắn đúng run/case; giữ review cũ và mới riêng.
- `runs/`: kết quả/trace/manifest thật; index và query vectors bị Git ignore.
- `reports/`: so sánh, kiểm toán metric, diagnostic và metrics tổng hợp.
- `report/individual/`: báo cáo cá nhân theo cấu trúc nộp bài.

Không làm bonus multimodal. Model có thể sai dù citation ID và excerpt khớp.
Người học kiểm tra semantic support với nguồn snapshot; nội dung không phải
xác nhận hiệu lực pháp luật hiện tại. Không tự commit hoặc push bài.

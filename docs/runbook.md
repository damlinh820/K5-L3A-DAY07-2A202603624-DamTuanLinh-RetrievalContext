# Chạy bài lab

Chạy các lệnh từ thư mục gốc repo Day 7. Python 3.11+ (đã kiểm thử 3.11.9).
Corpus/index có sẵn trên máy này; không cần gọi embedding lại để mở dashboard.

## Windows PowerShell

```powershell
cd "D:\AI20K\day7\K5-L3A-DAY07-2A202603624-DamTuanLinh-RetrievalContext"
# Chỉ tạo venv khi chưa có:
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.lock.txt
.\.venv\Scripts\python.exe -m src.cli audit-day6
.\.venv\Scripts\python.exe -m src.cli validate-benchmark
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe web/server.py --open
```

Nếu `py` chưa nhận Python nhưng runtime có sẵn, dùng đường dẫn tuyệt đối đến
python.exe để tạo venv. Không cần activate; gọi trực tiếp python.exe trong venv.
Nếu port 8765 đang chạy server cũ, Ctrl+C trong terminal đó rồi chạy lại.
Dùng `--port 8766` để mở một server riêng.

Giữ hai biến `OPENAI_API_KEY` (chat) và `OPENROUTER_API_KEY` (query embeddings)
trong .env Day 6 đang có, hoặc sao chép `.env.example` sang `.env` Day 7 và điền
cục bộ. Không dùng dấu ngoặc cong, không dán key vào chat hoặc lệnh terminal.
`DAY6_ROOT` mặc định là repo Day 6 cạnh repo này; có thể thay trong .env.

Nếu cài trên máy mới, clone [repo Day 6](https://github.com/damlinh820/K5-L3A-DAY06-2A202603624-DataIngestion)
cạnh thư mục Day 7 với tên `K5-L3A-DAY06-2A202603624-DataIngestion` hoặc trỏ
`DAY6_ROOT` tới clone đã có. Cần quyền đọc `results/chunks_C.jsonl` và snapshot
trang để đối chiếu; không cần sao chép .env từ máy người khác.

## Linux/macOS

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
export DAY6_ROOT=/absolute/path/to/Day6
.venv/bin/python -m src.cli audit-day6
.venv/bin/python web/server.py
```

Lock đầy đủ được tạo trên Windows; trên nền tảng khác dùng requirements.txt
và lưu `pip freeze` của môi trường đó trong manifest tái lập.

## Index

Nguồn cần có là `Day6/results/chunks_C.jsonl`, hash được ghi trong manifest.
Chroma mặc định nằm tại `runs/day6_rebuild/chroma`, collection `day6_c_dense`,
model `openai/text-embedding-3-small`, 1536 chiều, cosine.

```powershell
# Chỉ audit, không gọi API:
.\.venv\Scripts\python.exe -m src.cli build-index
# Nếu thật sự thiếu index, chọn thư mục mới; có gọi embedding API:
.\.venv\Scripts\python.exe -m src.cli build-index --output runs/rebuild_new --execute
```

Sau khi rebuild ở vị trí khác, cập nhật LAB7_CHROMA. Không thay model query đơn
thuần vì vector phải khớp index. Chroma HNSW approximate có thể đổi thứ hạng khi
xây lại; vì vậy giữ corpus/index fingerprints và báo kết quả mới riêng.

## Hỏi đáp và benchmark

```powershell
.\.venv\Scripts\python.exe -m src.cli ask "Luật trong bộ tài liệu điều chỉnh những nội dung nào?" --mode hybrid_improved
.\.venv\Scripts\python.exe -m src.cli eval --split dev --modes dense bm25 hybrid_rrf hybrid_improved --output runs/dev_new --max-run-cost-usd 0.20
.\.venv\Scripts\python.exe -m src.cli summarize
```

Mọi output benchmark phải dùng thư mục mới. Cache query embeddings nằm trong
`runs/local_cache` và không chứa header/key. Dashboard không gọi API; nút hỏi
đáp hoặc so sánh sẽ gọi API nếu query chưa có vector cache.

Chạy test mới chỉ sau khi manifest benchmark có `approved=true` và hash config
khớp. `eval --split test` tự kiểm tra điều kiện này; `--diagnostic` là replay test
đã mở và sẽ được ghi rõ trong manifest. Không ghép kết quả khác run thành điểm test.

## Review và nộp

Review được gắn run_id + case_id; nhãn mới còn gắn SHA-256 của chính trace.
`reviews/review_log.csv` giữ nhãn lịch sử; `reviews/verified/*.json` giữ review
theo từng citation đã xác nhận. Các file `reviews/pending/` không được tính điểm.
Đọc báo cáo tại `report/individual/2A202603624_DamTuanLinh.md` và ma trận yêu cầu.

Phần cần người học xác nhận nằm trong [USER_CONFIRMATIONS.md](USER_CONFIRMATIONS.md).
Snapshot hiện tại đã hoàn tất H1/H2 và lần test `final_holdout_v1`; xem
[bản đề xuất H3](../reviews/final_holdout_v1_H3.md), không chạy lại test để chấm nhãn.
Quy trình chung: sau H1/H2, chạy test mới một lần với Dense và Hybrid theo checklist.
Sau khi có output, tạo bộ hồ sơ review không gọi API:

```powershell
.\.venv\Scripts\python.exe -m src.cli prepare-reviews --run runs/final_holdout_v1
```

Đối chiếu source/context, điền context/grounded 0–2, lý do, nhãn boolean từng
citation, reviewer/thời điểm và status `human_verified` **sau xác nhận thật**.
H3 cần cả 7 output/mode. Sau đó finalize từng mode; chỉ đọc trace và nhãn:

```powershell
.\.venv\Scripts\python.exe -m src.cli finalize-reviews --run runs/final_holdout_v1/dense --reviews reviews/pending/final_holdout_v1__dense.json
.\.venv\Scripts\python.exe -m src.cli finalize-reviews --run runs/final_holdout_v1/hybrid_improved --reviews reviews/pending/final_holdout_v1__hybrid_improved.json
.\.venv\Scripts\python.exe -m src.cli summarize
```

Chỉ dùng `--partial` khi xuất bản một nhóm nhãn lịch sử đã xác nhận; review một
phần không hoàn tất H3. File nhãn thiếu lý do, chưa duyệt hoặc sai trace sẽ bị chặn.

Cuối cùng cập nhật báo cáo/verification, tạo lại inventory và kiểm tra readiness:

```powershell
.\.venv\Scripts\python.exe scripts/export_artifacts.py
.\.venv\Scripts\python.exe scripts/check_submission.py
.\.venv\Scripts\python.exe scripts/check_submission.py --ready
```

Lệnh mặc định kiểm cấu trúc và báo `ready_to_submit`; `--ready` trả mã 2 nếu
còn bước bắt buộc. Inventory bao gồm prompt, tài liệu đề và trace các run; không
bao gồm Chroma/query vectors/.env. Nó là danh sách checksum, không phải ZIP.
Sau khi đọc inventory và nội dung cần nộp, người học có thể stage:

```powershell
$gitExe = 'C:\Program Files\Git\cmd\git.exe'
$submissionPaths = (Get-Content -LiteralPath 'reports/submission_artifacts.json' -Raw -Encoding utf8 | ConvertFrom-Json).files.path
& $gitExe add -- $submissionPaths
& $gitExe add -- reports/submission_artifacts.json
& $gitExe diff --cached --name-only
& $gitExe diff --cached --stat
& $gitExe diff --cached --check
```

Nếu Git đã có trong PATH, dùng `git` trực tiếp. Không stage .env, venv hoặc binary
index. Quyền xem repo, commit/push và nộp link do người học kiểm tra theo lớp.

## Khắc phục

- HTTP 402 OpenRouter: xem response/account credit, không tự kết luận hết lượt ngày.
- HTTP 401: kiểm tra key đúng provider trong .env; key ASCII không bọc dấu ngoặc cong.
- DLL bị Application Control chặn: xem chính sách với quản trị viên; không dùng
  việc tắt bảo vệ máy như một yêu cầu của bài.
- Test FastAPI trên môi trường sandbox Windows có thể kẹt ở socketpair loopback;
  chạy trực tiếp terminal local. Không phải lỗi retrieval.
- Tokenizer tải dữ liệu chính thức ở lần đầu; lần sau dùng cache.
- Model alias không còn phục vụ: cấu hình model mới có phê duyệt và cập nhật pricing,
  chạy lại dev, lưu model/version mới; không tự dùng model khác khi báo lỗi.

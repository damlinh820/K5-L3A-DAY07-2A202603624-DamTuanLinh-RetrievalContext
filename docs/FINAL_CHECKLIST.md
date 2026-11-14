# Checklist hoàn thiện Day 7

**Cập nhật cuối: H1/H2/H3 đã hoàn tất.** Người học xác nhận cả 14 nhãn trong
`final_holdout_v1`; nhãn cuối ở `reviews/verified/`, biên nhận ở
`reviews/final_holdout_v1_confirmation.json` (tính từ gốc repo).
Các đoạn đề xuất/pending bên dưới ghi lại quy trình trước xác nhận; không còn là bước đang chờ của test này.

Cập nhật sau audit và sửa kỹ thuật ngày 14/11/2026. Phạm vi phần cơ bản tối đa
85 điểm; bonus đa phương thức ngoài plan. Kết quả thấp không tự làm mất điểm
nếu quy trình đúng và phân tích trung thực; phần cơ bản không có ngưỡng 90%.

**H1/H2 và test độc lập đã hoàn tất.** Đã đối chiếu và chuẩn bị đề xuất H3
cho 14 output. Bài còn chờ xác nhận H3 → chốt kết quả/kết luận cuối và nộp repo.
Phần cần người học xác nhận được tách tại
[USER_CONFIRMATIONS.md](USER_CONFIRMATIONS.md).

## 1. Đã thực hiện

- [x] Kết nối corpus C Day 6 1.137 chunk; giữ nguyên ID, text, provenance và
  hash. Benchmark gốc 24 câu giữ nguyên.
- [x] Dense/BM25/Hybrid và các cấu hình cải thiện có trace thực; giữ kết quả
  tăng/giảm chất lượng và phân biệt fixed generation cũ với function calling.
- [x] Sửa tổng hợp theo benchmark snapshot của từng run; dashboard tìm run mới
  qua manifest, không dùng chung q01–q24 cho h01–h07.
- [x] Thêm prepare/finalize review gắn run/case/hash trace. Finalize từ dữ liệu
  đã lưu, không gọi model lại; chặn nhãn pending/sai trace/thiếu citation.
- [x] Citation support theo từng citation, phải ở trong context; giữ toàn bộ
  mẫu số và N/A khi thiếu nhãn. Tỷ lệ câu trả lời có citation chỉ chia answered.
- [x] Bổ sung phân bố context 0/1/2, abstention được review và nhãn còn thiếu.
- [x] Test guard kiểm H1/H2, gold, corpus/model/mode/budget/runtime/index; đặt
  reservation một lần, lưu lỗi/kết quả một phần và chặn mở test mới bằng diagnostic.
- [x] Trạng thái holdout trong dashboard lấy từ artifact thực tế; evidence card
  bổ sung cả chunk neighbor trong context mà search top-3 không liệt kê.
- [x] Export mọi artifact văn bản của các run được giữ, prompt và tài liệu đề;
  loại binary index/query vectors/venv/.env. Sửa lệnh stage theo inventory.
- [x] Thêm `check_submission.py --ready`: chặn readiness khi chưa test/review,
  hash sai, inventory thiếu/stale hoặc báo cáo/metrics chưa chốt.
- [x] Cập nhật runbook, README src/docs, chỉ mục runs/reviews và phân biệt
  final_report lịch sử với báo cáo cá nhân hiện tại.
- [x] Đánh dấu script cũ; retrieval script legacy chặn test và ghi đè output.
- [x] Chuẩn bị hồ sơ đính chính q03/q05/q09/q10 và review dev mới nhất, giữ pending.
- [x] Sửa mô tả 20 gold kế thừa: metadata vẫn pending; biên nhận H1 gốc ghi
  q21–q24, không tự gọi cả benchmark là đã human-verified.
- [x] Kiểm thử workflow bằng fixture và kiểm tra kỹ thuật; kết quả thực chạy nằm
  trong [verification.json](../reports/verification.json).
- [x] Tạo lại inventory checksum sau các thay đổi hiện tại. Phải tạo lại lần nữa
  khi có test, review và báo cáo cuối.

Chi tiết thay đổi: [technical_completion.md](../reports/technical_completion.md).
Inference core đã tạo dev mới nhất được giữ nguyên; các fingerprint workflow
và index manifest được bổ sung trước khi người học chốt H2. Không sinh số đo
mới bằng fixture và không chuyển nhãn cũ sang run khác.

## 2. Người học cần xác nhận

- [x] **H1/H2, trước test:** bạn đã xác nhận h01–h07 và cấu hình; lưu
  [biên nhận](../benchmarks/h1_h2_confirmation.json), không cần duyệt lại.
- [ ] **H3, sau test:** review 14 output = 7 câu × Dense/Hybrid cải thiện;
  xem [bản đề xuất đầy đủ](../reviews/final_holdout_v1_H3.md), xác nhận hoặc
  điều chỉnh context, grounded, từng citation và abstention theo đúng trace.
- [ ] **Nếu sửa nhãn lịch sử:** xác nhận đính chính context bốn câu
  q03/q05/q09/q10 từ 0 lên 2, grounded giữ 0. Nếu chưa xác nhận, giữ errata và
  không dùng CER lịch sử đó làm kết luận cuối.
- [ ] **Tùy chọn:** duyệt [17 đề xuất dev](../reviews/dev_review_proposals.md)
  nếu muốn báo semantic metrics human-reviewed cho dev; có thể giữ N/A.
- [ ] **Khi nộp:** kiểm tra repo cá nhân, quyền xem của người chấm, nơi nộp link.

Không cần bạn tự sửa JSON hoặc chạy các lệnh kỹ thuật. Sau xác nhận thật,
agent có thể ghi metadata/hash, chạy, chuẩn bị hồ sơ, tính điểm và cập nhật báo cáo.

## 3. Agent thực hiện sau H1/H2

- [x] Ghi reviewer/time, gold status, receipt và hash đúng phiên bản vào manifest.
- [x] Kiểm tra corpus/index/freeze; dùng output mới cho lần test độc lập.
- [x] Chạy Dense và Hybrid cải thiện trên cùng bộ mới. Lệnh đã dùng, không chạy lại:

```powershell
.\.venv\Scripts\python.exe -m src.cli eval --split test `
  --questions benchmarks/fresh_holdout_approved.jsonl `
  --modes dense hybrid_improved `
  --output runs/final_holdout_v1 `
  --max-run-cost-usd 0.20
```

- [x] Giữ đủ 14 kết quả, kể cả error; lưu model/version, tool/ranking/context,
  answer/citation, token, thời gian và chi phí. Không rerun âm thầm.
- [x] Tạo hồ sơ review, không gọi API:

```powershell
.\.venv\Scripts\python.exe -m src.cli prepare-reviews --run runs/final_holdout_v1
```

- [x] Chuẩn bị bản đối chiếu cho người học duyệt H3. Nếu dùng test để chỉnh pipeline,
  báo rõ exposed test và cần holdout khác cho kết luận độc lập.

## 4. Agent thực hiện sau H3

- [ ] Ghi nhãn từng case/citation gắn trace và reviewer/time/lý do; finalize
  cả hai mode theo [runbook](runbook.md#review-và-nộp).
- [ ] Chạy summarize, kiểm các số giữa metrics, dashboard, README và báo cáo.
- [ ] Điền bảng test mới cho baseline và cấu hình chọn, cùng định nghĩa/cutoff:
  Hit@1, Evidence Hit@3, CER máy và CER human có n/N và tỷ lệ.
- [ ] Báo context 0/1/2, grounded 0/1/2 và mean /2, citation support toàn bộ
  citation, số câu answered có citation, abstention/false abstention, tool use,
  phân bố call và error.
- [ ] Báo latency p50/p95, token, chi phí theo cấu hình; phân biệt rebuild,
  query embedding và chat, estimate/actual unknown/cache.
- [ ] Giữ ít nhất hai lỗi dev có trace trước/sau và hai thử nghiệm cải thiện,
  kể cả kết quả giảm. Candidate20 cũ là dense10 + lexical20, lexical rerank
  không phải cross-encoder.
- [ ] Giữ test gốc và diagnostic trong phần lịch sử. Provenance sửa Hybrid
  Hit@3 cũ 3/5 → 4/5 không phải lần chạy model mới. Không ghép run thành 5/5.
- [ ] Bổ sung ví dụ answered, abstain và lỗi/giới hạn thật, nguồn/trace/nhãn;
  kết luận đúng phạm vi sample 5+2 và snapshot.
- [ ] Chốt [báo cáo cá nhân](../report/individual/2A202603624_DamTuanLinh.md),
  cập nhật trạng thái/verification, rồi ghi hash report/metrics và run cuối
  vào `reports/finalization.json`. Đây là công việc của agent sau nhãn đã duyệt.
- [ ] Chạy kiểm tra cuối, export lại và yêu cầu readiness đạt:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m src.cli audit-day6
.\.venv\Scripts\python.exe -m src.cli validate-benchmark
.\.venv\Scripts\python.exe -m src.cli validate-benchmark --questions benchmarks/fresh_holdout_candidates.jsonl
.\.venv\Scripts\python.exe scripts/export_artifacts.py
.\.venv\Scripts\python.exe scripts/check_submission.py --ready
```

Lệnh check mặc định chỉ kiểm cấu trúc và báo readiness. `--ready` trả mã 2
khi còn bước bắt buộc. Việc thiếu nhãn được giữ là N/A, không tự chấm thành 0/100%.

## 5. Dọn file và đóng gói

- [x] Giữ code/prompt/config/lock/tests/web, dữ liệu được chia sẻ hoặc cách lấy
  snapshot, gold/review/receipts, mọi trace dùng trong báo cáo và kết quả xấu.
- [x] Giữ tài liệu đề/template và starter. `src/agent.py` vẫn là dependency
  của ToolAgent, không phải file thừa có thể xóa.
- [x] Run trung gian và đề xuất cũ có chỉ mục/lưu ý lịch sử; không di chuyển
  đường dẫn hoặc xóa evidence gốc để làm gọn.
- [x] .env, venv, Chroma và query vectors giữ cục bộ; manifest/lệnh rebuild,
  model/dimension/metric và quyền truy cập Day 6 được ghi trong runbook.
- [ ] Sau bản cuối, đọc inventory và stage theo [runbook](runbook.md#review-và-nộp).
  Không dùng `git add` danh sách cũ bỏ sót prompts/runs.
- [ ] Kiểm tra clone sạch khi có điều kiện; rebuild có phí embedding và HNSW
  có thể đổi thứ hạng nên ghi kết quả rebuild riêng.
- [ ] Người học kiểm tra quyền xem, commit/push và nộp link theo lớp.

**Hiện chưa sẵn sàng nộp vì nhãn H3 và bước chốt báo cáo chưa hoàn tất.**
Các mục sau các mốc xác nhận được agent tiếp tục thực hiện khi có nhãn/duyệt,
không phải danh sách thao tác kỹ thuật bắt bạn tự làm.

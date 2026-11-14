# Hoàn thiện kỹ thuật sau audit

**Cập nhật cuối: H1/H2/H3 đã hoàn tất.** Người học xác nhận cả 14 nhãn trong
`final_holdout_v1`; nhãn cuối ở `reviews/verified/`, biên nhận ở
`reviews/final_holdout_v1_confirmation.json` (tính từ gốc repo).
Các đoạn đề xuất/pending bên dưới ghi lại quy trình trước xác nhận; không còn là bước đang chờ của test này.

Ngày 14/11/2026. Phạm vi phần cơ bản 85 điểm. Các thay đổi dưới đây phục vụ
đánh giá/đóng gói, không tạo số liệu test mới và không đổi nhãn đã xác nhận.

| Hạng mục | Thay đổi |
|---|---|
| Metrics | Citation có nhãn từng nguồn và phải ở trong context; mẫu số giữ toàn bộ citation, thiếu nhãn trả N/A. Câu trả lời có citation chỉ chia số câu answered. Bổ sung phân bố context và abstention human-reviewed |
| Benchmark theo run | Run mới giữ `benchmark.jsonl` và hash; dashboard tìm run qua manifest và dùng đúng case map, hỗ trợ h01–h07 |
| Review/finalize | Tạo hồ sơ pending; kiểm run/case/hash trace, nguồn, điểm, timestamp và lý do từng citation. Tổng hợp nhãn đã xác nhận không gọi API; subset lịch sử không được coi là H3 hoàn tất |
| Holdout | Kiểm H1/H2, gold, model/mode/budget, corpus/runtime/index; đặt reservation độc quyền và ghi trạng thái chạy. Chặn lặp holdout hoặc dùng diagnostic để mở bộ chưa chạy |
| Lỗi giữa run | Ghi từng output và all_traces sau từng query; manifest ghi failed khi lỗi/gián đoạn, giữ kết quả một phần |
| Dashboard/demo | Trạng thái holdout động, hiện bảng retrieval từ run mới; evidence card có cả chunk mở rộng từ context, không cần gọi search lại |
| Export | Bỏ whitelist run cứng; bao gồm code/prompt/tài liệu đề/nhãn và artifact văn bản các run; loại index binary, query vectors, venv và .env |
| Submission check | Tách kiểm cấu trúc với `--ready`; báo bước còn thiếu, inventory stale/missing, hash và artifact lỗi; chưa H1/H2/H3 không coi là sẵn sàng |
| Tài liệu | Sửa runbook stage đủ file, mô tả src, chỉ mục docs/runs/reviews; final_report cũ được ghi rõ lịch sử, báo cáo cá nhân là bản chính |
| Script cũ | Đánh dấu fixed-generation legacy; script retrieval cũ chặn test và ghi đè output |

Giữ nguyên inference core của dev mới nhất: tool-agent, prompt, retrieval,
context và validator. Fingerprint bản chốt được bổ sung phần workflow và index
manifest trước H2. Phần kiểm tra kỹ thuật không gọi lại model; sau đó người
học đã duyệt H1/H2 và test độc lập được chạy một lần trong `final_holdout_v1`.

Các kiểm tra và số test thực chạy được ghi trong
[verification.json](verification.json): 56/56 test pass, pip check/compileall
pass, JavaScript kiểm cú pháp bằng V8, HTTP fixture dashboard/evidence pass.
Test mới chỉ dùng fixture khi kiểm
workflow; không dùng output fixture làm benchmark thực. Số đo thật hiện tại
vẫn lấy từ `tool_agent_submission_dev/hybrid_improved` và các run lịch sử.

Chuẩn bị cho người học:

- [Danh sách xác nhận H1/H2, H3 và đính chính](../docs/USER_CONFIRMATIONS.md).
- [Đề xuất review dev](../reviews/dev_review_proposals.md); pending, chưa tính
  thành điểm human-reviewed.
- Bốn đề xuất context lịch sử 0 → 2, grounded giữ 0 vì abstain; chưa đổi CSV.
- [Checklist trạng thái hiện tại](../docs/FINAL_CHECKLIST.md).

Còn lại phụ thuộc xác nhận: H3 hai mode theo `reviews/final_holdout_v1_H3.md`,
sau đó tổng hợp nhãn và chốt kết luận/báo cáo, verification và inventory.

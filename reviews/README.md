# Nhãn và quy trình xác nhận

**Cập nhật cuối: H1/H2/H3 đã hoàn tất.** Người học xác nhận cả 14 nhãn trong
`final_holdout_v1`; nhãn cuối ở `reviews/verified/`, biên nhận ở
`reviews/final_holdout_v1_confirmation.json` (tính từ gốc repo).
Các đoạn đề xuất/pending bên dưới ghi lại quy trình trước xác nhận; không còn là bước đang chờ của test này.

Hiện cần xác nhận [14 đề xuất H3 của test mới](final_holdout_v1_H3.md).
H1/H2 đã hoàn tất; nhãn H3 trong pending vẫn chưa chuyển vào verified.

- `review_log.csv`: nhãn lịch sử đã xác nhận, giữ nguyên để truy vết.
- `pending/*.json`: hồ sơ cần đối chiếu, không đưa vào metric đã duyệt.
- `verified/*.json`: nhãn mới đã xác nhận theo run/case và hash trace; nhãn có
  cấu trúc này được ưu tiên khi đính chính cùng case của CSV lịch sử.
- `ai_suggestions*.csv`, các file pending/diagnostic cũ: lịch sử đề xuất,
  không thay cho `verified` hoặc biên nhận của người học.

Tạo hồ sơ bằng `python -m src.cli prepare-reviews --run runs/<run>/<mode>`.
Hồ sơ có câu hỏi, gold, câu trả lời, context, đường dẫn trace và citation.
Chỉ sau xác nhận thật mới điền reviewer/time, `source_verified=true`,
`status=human_verified`, điểm/lý do và nhãn từng citation rồi finalize.

`python -m src.cli finalize-reviews --run ... --reviews ...` kiểm đầy đủ toàn
bộ mode và tổng hợp lại từ trace, không gọi API. `--partial` dành cho đính
chính một nhóm lịch sử, không hoàn tất H3 của test mới. Không thay đổi hash
để dùng nhãn của một output khác. Xem [phần xác nhận](../docs/USER_CONFIRMATIONS.md).

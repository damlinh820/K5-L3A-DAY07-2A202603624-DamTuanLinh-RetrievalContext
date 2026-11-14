# Duyệt benchmark mới và cấu hình cuối

**Đã hoàn tất H1/H2.** Người học đã xác nhận h01–h07 và yêu cầu chạy Dense +
Hybrid theo cấu hình hiện tại. Xem [biên nhận](h1_h2_confirmation.json) và
[bản benchmark được duyệt](fresh_holdout_approved.jsonl). Bản candidates giữ
nguyên để truy vết quá trình chuẩn bị. Test `final_holdout_v1` đã chạy một lần;
[bản review H3](../reviews/final_holdout_v1_H3.md) đang chờ xác nhận output.

Cấu hình đã chốt trong `configs/final_tool_agent.json`: Hybrid cải thiện,
candidate 10, RRF 60, top-3, context 6.000 ký tự, tool search do model gọi,
baseline Dense cùng model và cùng prompt. Test mới chạy cả baseline và cấu hình
đã chọn sau khi duyệt. Bảng dưới là nội dung đã dùng để duyệt trước lần chạy.

| ID | Câu hỏi / đáp án dự kiến | Nguồn cần đối chiếu |
|---|---|---|
| h01 | Đất đai thuộc sở hữu ai, ai đại diện? → Toàn dân; Nhà nước đại diện chủ sở hữu và thống nhất quản lý. | luatdat1, trang 12, Điều 12 |
| h02 | Tổ chức trong nước được giao đất không thu tiền có quyền cho thuê/thế chấp không? → Không, theo phạm vi khoản 2 Điều 32. | luatdat1, trang 26, Điều 32 |
| h03 | Thời kỳ và tầm nhìn quy hoạch sử dụng đất cấp huyện? → 10 năm và 20 năm. | luatdat1, trang 55, Điều 62 khoản 3 |
| h04 | Đất nông nghiệp công ích theo Điều 179 có thuộc diện không cấp GCN của Điều 151? → Có. | luatdat2, trang 71, Điều 151 khoản 1 điểm a |
| h05 | Đất trụ sở Mặt trận Tổ quốc Việt Nam có được liệt kê ở Điều 199 khoản 1? → Có. | luatdat3, trang 18, Điều 199 khoản 1 |
| h06 | Phí đo đạc địa phương năm 2026 cho thửa đất 120m² tại Đà Nẵng? → Chưa đủ evidence. | Corpus không có biểu phí/hồ sơ thửa đất riêng; cần xác nhận phạm vi |
| h07 | Hồ sơ xin cấp GCN riêng của người dân đã phê duyệt chưa? → Chưa đủ evidence. | Corpus không có hồ sơ hoặc quyết định cá nhân; cần xác nhận phạm vi |

Gold quote nguyên văn, source URL, chunk IDs và trạng thái review nằm trong
`fresh_holdout_candidates.jsonl`. Đã kiểm tra 5/5 quote với snapshot văn bản theo
trang Day 6; đây không thay thế việc bạn đọc và xác nhận.

Nội dung đã được duyệt: câu hỏi không trùng/đổi cách hỏi của benchmark cũ, evidence đúng
nguồn/trang/điều kiện, hai câu thiếu bằng chứng thật sự ngoài corpus, và đồng ý
dùng cấu hình cuối để đánh giá. Bước này là H1/H2 theo plan và BENCHMARK.md.
Approval/hash và lần chạy đã được lưu; H3 là review output sau chạy, tách với H1/H2.

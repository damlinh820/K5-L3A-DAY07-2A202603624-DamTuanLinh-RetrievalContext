# Đề xuất review dev mới nhất

Run: `tool_agent_submission_dev/hybrid_improved`. Đã đối chiếu câu hỏi, answer,
gold và quote/context đã lưu. Bảng này đang pending; không tính thành nhãn đã
duyệt. Toàn bộ nguồn, context, hash và nhãn từng citation nằm trong
[hồ sơ đầy đủ](pending/tool_agent_submission_dev__hybrid_improved.json).

| ID | Context đề xuất | Grounded đề xuất | Nhận xét |
|---|---:|---:|---|
| q01 | 2 | 2 | Trả lời đủ các nhóm nội dung điều chỉnh; citation Điều 1 hỗ trợ phần tóm tắt. |
| q02 | 2 | 2 | Đủ cấp xã/cấp huyện nơi không lập cấp xã và cơ quan nhà nước có thẩm quyền xác nhận. |
| q03 | 2 | 2 | Nêu đúng chiếm đất; evidence khoản 9 Điều 3 có trong context. |
| q04 | 2 | 2 | Đủ ba nhóm: nông nghiệp, phi nông nghiệp, chưa sử dụng. |
| q05 | 2 | 2 | Trả lời có, dựa Điều 11 phần 1 và đúng ba hành vi bị hỏi. |
| q06 | 2 | 2 | Giữ điều kiện đất sử dụng hợp pháp; nguồn Điều 26 hỗ trợ. |
| q07 | 2 | 2 | Đủ mục đích, ranh giới, độ sâu/chiều cao và bảo vệ công trình, tuân thủ quy định. |
| q08 | 2 | 2 | Nêu đúng ngoại lệ tại điểm a khoản 1 Điều 45; citation thứ hai hỗ trợ điều kiện đủ cấp GCN ở khoản 4. Cần xem phần bổ sung này có phù hợp phạm vi câu hỏi chỉ xét điều kiện GCN. |
| q09 | 2 | 2 | Nêu đúng quy hoạch sử dụng đất cấp trên; khoản 4 Điều 60 hỗ trợ. |
| q10 | 2 | 2 | Liệt kê đủ các nhu cầu trong khoản 1 Điều 29, không bỏ nhóm cấp khí ga/điện/thông tin. |
| q11 | 2 | 2 | Giữ điều kiện nguyện vọng đã đăng ký khi lập phương án, không đổi thành chọn tiền vô điều kiện. |
| q12 | 2 | 2 | Giữ đúng mốc trước quyết định thu hồi đất và nguồn phần 2. |
| q13 | 2 | 2 | Nêu đúng trừ nghĩa vụ tài chính vào tiền bồi thường để hoàn trả ngân sách. |
| q14 | 2 | 2 | Trả lời cần cho phép, dựa điểm b khoản 1 Điều 121. |
| q15 | 2 | 2 | Giữ điều kiện nhiều thửa nông nghiệp cùng đơn vị hành chính và có yêu cầu cấp chung. |
| q21 | N/A | N/A; abstention đúng | Từ chối rõ, không đưa mức phạt nghị định 2027 không có trong snapshot. |
| q22 | N/A | N/A; abstention đúng | Từ chối yêu cầu về quốc gia khác; không dùng luật Việt Nam trả lời thủ tục nước khác. |

15 câu answerable đề xuất mức 2; hai câu insufficient đề xuất từ chối đúng.
Các citation được đề xuất hỗ trợ, nhưng chỉ sau người học xác nhận mới chuyển
nhãn vào verified. Riêng q08 cần đọc cả hai nguồn và phạm vi câu hỏi.

Không chuyển đề xuất này thành điểm test; đây là dev. Có thể giữ N/A semantic
cho dev và ưu tiên H1/H2 rồi H3 của bộ test mới theo
[danh sách xác nhận](../docs/USER_CONFIRMATIONS.md).

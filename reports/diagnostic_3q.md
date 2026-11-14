# Kiểm tra lại q16, q17, q19

Lần chạy cuối: `runs/case_diagnostic_final`. Đây là kiểm tra chẩn đoán trên test
đã mở, có sửa code dựa trên lỗi đã quan sát; không phải đánh giá holdout mới.
Không suy rộng kết quả ba câu thành độ chính xác của cả hệ thống.

## Kết quả cuối để người học đối chiếu

| Câu | Trạng thái | Nội dung trả lời | Nguồn snapshot | Review mới |
|---|---|---|---|---|
| q16 | answered | Đất ở thuộc nhóm sử dụng ổn định lâu dài. | luatdat3, Điều 171 khoản 1, trang 1; ID `0bdc591d4a3757a7bcd740e6f887eedf` | human_verified |
| q17 | answered | 50 năm; được tiếp tục sử dụng mà không phải làm thủ tục gia hạn. | luatdat3, Điều 172 khoản 1 điểm a, chunk trang 1–2, evidence ở trang 2; ID `8f9858b390b20bbbd00836d99647486c` | human_verified |
| q19 | answered | Liệt kê đủ bốn loại Giấy chứng nhận theo câu hỏi. | luatdat3, Điều 220 khoản 1 điểm a, trang 34; ID `c036e6ec6d93a0b2900ebb12804a7505` | human_verified |

q19 liệt kê: Giấy chứng nhận quyền sử dụng đất; Giấy chứng nhận quyền sở hữu nhà ở
và quyền sử dụng đất ở; Giấy chứng nhận quyền sử dụng đất, quyền sở hữu nhà ở và
tài sản khác gắn liền với đất; Giấy chứng nhận quyền sử dụng đất, quyền sở hữu
tài sản gắn liền với đất.

Hai case đối chứng q23/q24 vẫn abstain. Cả ba câu chính có gold trong top-3 và
context; câu trả lời có citation ID và excerpt khớp nguồn. Người học đã xác nhận
ba câu mới ngày 2026-11-14; context, grounded answer và citation support đều 2/2.
Kết quả trên tập ba câu được duyệt: grounded 3/3, citation hỗ trợ 3/3.
Hai case đối chứng q23/q24 chưa được gán review mới trong lần xác nhận này.

## Nguyên nhân thực tế và sửa chữa

- q16: evidence đúng đã có trong trace gốc; output thô cũ không được lưu nên
  không thể phân biệt model abstain với validator loại câu chỉ có citation.
  Replay mới cho thấy model thường có nội dung nhưng thiếu marker trong answer.
  Hệ thống hiện render marker từ citation model đã chọn, sau kiểm tra ID/excerpt.
- q17: context gốc chỉ chứa Điều 176 về diện tích, không có Điều 172 về thời hạn.
  Nhận xét review cũ rằng context đã đủ evidence là sai. Corpus không mất dữ liệu:
  chunk Điều 172 có sẵn, nhưng RRF xếp nó dưới top-3. Pipeline mới tách dẫn chiếu
  hạn mức khỏi ý hỏi thời hạn/gia hạn, ưu tiên candidate có các trường cần trả lời.
- q19: trace gốc có đúng khoản 1 Điều 220 nhưng thiếu marker trong answer; validator
  chuyển lỗi format thành abstain. Ngoài ra script cũ không áp dụng giới hạn phần 3.
  Pipeline chung hiện suy ra phạm vi phần từ câu hỏi và ghi rõ filter.
- Script agent trước đó luôn dùng hybrid gốc, chưa nối retrieval cải thiện dù tên
  output là `agent_dev_all5`. `scripts/run_agent_dev.py` hiện dùng chung pipeline,
  có `--mode hybrid_improved` và ghi query variants/rankings.
- Quote có dấu rút gọn chỉ được mở rộng nếu từng mảnh khớp chính xác, theo thứ tự,
  duy nhất trong đúng chunk. Lưu cả quote gốc và bản chuẩn hóa; không dò gần đúng.
- Response hỏng vẫn không qua kiểm tra sau tối đa một lần tạo lại mang status
  `error`, reason `output_validation_failed`, không bị tính là thiếu evidence.

Request OpenAI dùng structured JSON theo
[tài liệu Structured Outputs](https://developers.openai.com/api/docs/guides/structured-outputs).
Raw response, lỗi kiểm tra, bước chuẩn hóa, token và hash code/prompt được lưu
trong artifacts. Chỉ gọi generation cố định cho lần so sánh này; đây chưa phải
agent để model tự chọn tool.

## Các lần chạy được giữ lại

- `case_diagnostic_v2`: q16/q19 trả lời được; q17 trả lời sai (nhầm diện tích thành
  thời hạn và thêm claim gia hạn không có nguồn). Không được tính q17 là đạt.
- `case_diagnostic_v3`/`v4`: đưa đúng evidence vào q17, nhưng quote model dùng dấu
  rút gọn nên bị từ chối ở bước kiểm tra excerpt.
- `case_diagnostic_final`: ba câu answered, hai câu đối chứng abstain, mỗi case
  một chat call; 8.452 input + 883 output = 9.335 tokens. Chi phí chat unknown
  vì response OpenAI không chứa số tiền; embedding usage được ghi riêng.

Unit tests: 35/35 passed, gồm missing marker, quote sai chunk, bịa đoạn trích,
nhầm diện tích/thời gian và giới hạn số lần sửa. File review cũ giữ nguyên như
lịch sử; nhận xét sai về q17 được đính chính tại đây, không tự thay nhãn đã duyệt.

Nhãn đã duyệt cho **lần chạy mới này** được ghi trong `reviews/review_log.csv`,
với biên nhận `reviews/diagnostic_3q_confirmation.json` gắn đúng hash trace.
`reviews/diagnostic_3q_pending.csv` giữ bản đề xuất trước xác nhận làm lịch sử.
Đánh giá độc lập cho cấu hình mới vẫn cần một test chưa dùng để chỉnh theo BENCHMARK.md.

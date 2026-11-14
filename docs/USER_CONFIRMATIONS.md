# Các phần cần người học xác nhận

**Cập nhật cuối: H1/H2/H3 đã hoàn tất.** Người học xác nhận cả 14 nhãn trong
`final_holdout_v1`; nhãn cuối ở `reviews/verified/`, biên nhận ở
`reviews/final_holdout_v1_confirmation.json` (tính từ gốc repo).
Các đoạn đề xuất/pending bên dưới ghi lại quy trình trước xác nhận; không còn là bước đang chờ của test này.

Các phần kỹ thuật được agent thực hiện và kiểm tra. File này chỉ liệt kê
những quyết định/nhãn cần người học đối chiếu và xác nhận thật.

**Trạng thái hiện tại:** H1/H2 đã xác nhận và test hai mode đã chạy. Việc cần
bạn tiếp theo là đọc [14 đề xuất H3](../reviews/final_holdout_v1_H3.md).
Không cần duyệt lại H1/H2.

## 1. H1 và H2 — đã hoàn tất trước test

**H1 — duyệt 7 câu mới và gold/phạm vi corpus.** Đọc
[bảng duyệt](../benchmarks/REVIEW.md) và
[gold/quote/source chi tiết](../benchmarks/fresh_holdout_candidates.jsonl).
Đối chiếu với snapshot Day 6; “trang” bên dưới là trang trong phần PDF tương ứng.

| ID | Nội dung cần xác nhận | Nguồn/phạm vi |
|---|---|---|
| h01 | Sở hữu toàn dân; Nhà nước đại diện chủ sở hữu và thống nhất quản lý | Phần 1, trang 12, Điều 12 |
| h02 | Tổ chức được giao đất không thu tiền không có quyền cho thuê/thế chấp nêu trong câu hỏi | Phần 1, trang 26, khoản 2 Điều 32 |
| h03 | Thời kỳ quy hoạch cấp huyện 10 năm, tầm nhìn 20 năm | Phần 1, trang 55, khoản 3 Điều 62 |
| h04 | Đất nông nghiệp công ích theo Điều 179 thuộc trường hợp không cấp GCN được hỏi | Phần 2, trang 71, điểm a khoản 1 Điều 151 |
| h05 | Đất trụ sở Mặt trận Tổ quốc Việt Nam được liệt kê | Phần 3, trang 18, khoản 1 Điều 199 |
| h06 | Corpus không có biểu phí đo đạc địa phương 2026 cho thửa 120 m² tại Đà Nẵng | Kiểm phạm vi dữ liệu; không suy chỉ từ top-k |
| h07 | Corpus không có hồ sơ/quyết định phê duyệt riêng của người dân được hỏi | Kiểm phạm vi dữ liệu; không suy chỉ từ top-k |

Cũng xác nhận đây không chỉ là đổi cách hỏi của các câu cũ đã dùng chỉnh hệ
thống. Gold 5 câu answerable khớp snapshot theo trang; bạn đã xác nhận nguồn/
phạm vi của cả 7 câu. Biên nhận nằm ở
[h1_h2_confirmation.json](../benchmarks/h1_h2_confirmation.json).

**H2 — đồng ý dùng cấu hình cuối để đánh giá.** Đọc
[final_tool_agent.json](../configs/final_tool_agent.json):

- Baseline `dense`, cấu hình chọn `hybrid_improved`.
- Chat OpenAI `gpt-4o-mini`; query embedding OpenRouter
  `openai/text-embedding-3-small`, 1536 chiều; Chroma cosine, corpus C 1.137 chunk.
- Candidate 10, RRF 60, top-3, context 6.000 ký tự, controlled một lượt retrieval.
- Cùng corpus/index/prompt/model và điều kiện so sánh; đóng băng bằng hash.
- Ngân sách chat ước tính tối đa $0,20 cho lệnh test hai mode, $0,10/query;
  usage/chi phí query embedding được ghi riêng theo provider. Đây là giới hạn
  ước tính, không phải số tiền hóa đơn đã biết trước.

Xác nhận H1/H2 bạn đã gửi được lưu theo câu trả lời thực tế:

> Tôi check h1-07 đều đúng rồi
>
> Đã xác nhận H1; chạy Dense và Hybrid theo cấu hình hiện tại

Agent đã ghi reviewer/thời điểm/hash và chạy đúng một lần; gold/cấu hình
inference không bị chỉnh theo kết quả test.

**Vì sao cần bạn:** [BENCHMARK.md §1](../BENCHMARK.md) yêu cầu “Chốt cấu hình
và tiêu chí chọn trước khi chạy test”; [plan.md](../plan.md) yêu cầu “stop at
each HUMAN GATE rather than approving it yourself”. Những lần xác nhận q cũ
không tự áp dụng cho gold/cấu hình và output mới này.

## 2. Bắt buộc sau test mới: H3

Đã có [bản H3 đầy đủ](../reviews/final_holdout_v1_H3.md) và hai hồ sơ
[Dense](../reviews/pending/final_holdout_v1__dense.json),
[Hybrid](../reviews/pending/final_holdout_v1__hybrid_improved.json).
Mỗi hồ sơ có câu hỏi, answer, context, nguồn, citation, trace và đề xuất nhãn.

- Mỗi mode đọc h01–h05: context 0/1/2, grounded 0/1/2 và lý do.
- Đọc từng citation: có trong context và hỗ trợ đúng mệnh đề/điều kiện không.
- Đọc h06–h07: thực sự từ chối, không kèm khẳng định thiếu căn cứ.
- Xác nhận cả **14 output = 7 câu × 2 mode**, không chép nhãn từ run khác.

Theo [BENCHMARK.md §2–3](../BENCHMARK.md), baseline và cấu hình chọn đều cần
review ít nhất 5 câu có đáp án và 2 câu thiếu evidence. Agent sẽ ghi nhãn đã
xác nhận, tổng hợp metric, cập nhật báo cáo và inventory mà không gọi model lại.

Nếu đồng ý sau đối chiếu, xác nhận các nhãn H3 trong `final_holdout_v1_H3.md`
cho cả hai mode. Nếu khác, nêu mode + ID + nhãn/lý do cần đổi. Các nhãn H3
hiện vẫn pending; H1/H2 không tự duyệt các output được tạo sau đó.

## 3. Cần xác nhận nếu sửa nhãn context lịch sử

Run `agent_dev_fixed` có bốn nhãn context đang ghi 0 nhưng trace chứa evidence
trực tiếp. Đã chuẩn bị [hồ sơ đính chính](../reviews/pending/context_corrections.json)
với gold quote, nguyên context và hash trace.

| ID | Evidence nằm trong context | Đề xuất |
|---|---|---|
| q03 | Định nghĩa chiếm đất, khoản 9 Điều 3, phần 1 trang 2 | Context 0 → 2; grounded giữ 0 |
| q05 | Lấn/chiếm/hủy hoại đất bị nghiêm cấm, khoản 1 Điều 11, phần 1 trang 11 | Context 0 → 2; grounded giữ 0 |
| q09 | Quy hoạch cấp dưới phù hợp cấp trên, khoản 4 Điều 60, phần 1 trang 53 | Context 0 → 2; grounded giữ 0 |
| q10 | Các quyền thửa đất liền kề, khoản 1 Điều 29, phần 1 trang 25 | Context 0 → 2; grounded giữ 0 |

Grounded giữ 0 vì output cũ đã abstain dù câu có đáp án. Nhãn gốc chưa thay
đổi. Nếu đồng ý sau đối chiếu, xác nhận “Tôi xác nhận đính chính context bốn
câu q03/q05/q09/q10 như đề xuất”. Agent sẽ lưu đính chính gắn trace, giữ CSV
lịch sử và tính lại bảng liên quan. Nếu chưa xác nhận, báo cáo giữ errata và
không dùng CER lịch sử này làm kết luận cuối.

## 4. Tùy chọn: xác nhận review dev mới nhất

[Bảng đề xuất dev](../reviews/dev_review_proposals.md) và
[hồ sơ đầy đủ](../reviews/pending/tool_agent_submission_dev__hybrid_improved.json)
đã chuẩn bị cho 17 output. Chúng chưa được đưa vào nhãn đã duyệt.
Chỉ cần duyệt bộ này nếu muốn báo grounded/citation human-reviewed cho dev;
có thể giữ N/A cho dev và hoàn tất H3 test mới theo yêu cầu đề.

Metadata benchmark lịch sử cũng cần phân biệt: 20 gold kế thừa q01–q20 còn
`pending_human_review`, trong khi biên nhận H1 gốc ghi rõ q21–q24 đã duyệt.
Báo cáo đã sửa để không gọi cả 20 gold là human-verified. Không đổi benchmark
gốc/hash hay yêu cầu bạn duyệt lại những nhãn đã có biên nhận. Nếu muốn chốt
trạng thái human-verified cho 20 gold này, cần xác nhận riêng dựa trên
[benchmark gốc](../data/benchmark_day7/lab7_benchmark.jsonl) và nguồn; lưu biên
nhận bổ sung thay vì ghi đè snapshot. Việc này không thay H1/H2/H3 của test mới.

## 5. Trước khi nộp

Người học kiểm tra repo cá nhân, quyền xem của người chấm và nơi nộp link theo
lớp. Agent chuẩn bị inventory/lệnh stage; việc publish/commit/push không được
thực hiện trong lượt hoàn thiện này. Kiểm tra giao diện bằng mắt trên máy là
khuyến nghị cho demo, không phải mốc duyệt nhãn bắt buộc của benchmark.

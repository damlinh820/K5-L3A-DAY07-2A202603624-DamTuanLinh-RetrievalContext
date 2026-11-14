# H3 — Review 14 output của test mới

**Cập nhật cuối: H1/H2/H3 đã hoàn tất.** Người học xác nhận cả 14 nhãn trong
`final_holdout_v1`; nhãn cuối ở `reviews/verified/`, biên nhận ở
`reviews/final_holdout_v1_confirmation.json` (tính từ gốc repo).
Các đoạn đề xuất/pending bên dưới ghi lại quy trình trước xác nhận; không còn là bước đang chờ của test này.

Run: `final_holdout_v1`. H1/H2 đã được bạn xác nhận; biên nhận ở
[h1_h2_confirmation.json](../benchmarks/h1_h2_confirmation.json).
Đã chạy đúng một lần Dense và Hybrid cải thiện trên cùng bản
[benchmark được duyệt](../benchmarks/fresh_holdout_approved.jsonl).
**Các điểm semantic bên dưới là đề xuất đang chờ bạn xác nhận H3.**
Không dùng việc duyệt gold ở H1 để tự duyệt output được tạo sau đó.

## Kết quả đo được

| Chỉ số | Dense | Hybrid cải thiện |
|---|---:|---:|
| Hit@1 | 4/5 (80%) | 3/5 (60%) |
| Evidence Hit@3 | 4/5 (80%) | 4/5 (80%) |
| Context exact evidence (máy) | 4/5 (80%) | 4/5 (80%) |
| Answered / abstain / error | 6 / 1 / 0 | 5 / 1 / 1 |
| Thiếu evidence được abstain (theo status) | 1/2 | 1/2 |
| Answerable bị abstain | 0/5 | 0/5 |
| Tool use trên lượt thành công | 7/7 | 6/6 |
| Latency p50 / p95 | 6.05 / 11.10 giây | 4.39 / 8.10 giây |
| Chat ước tính | $0.0039546 | $0.0042528 |

Có 31 response model cho 14 lượt chạy (7 câu × 2 mode), gồm các lần sửa format.
Tổng chat ước tính $0,0082074; query embedding provider báo $0,00000722
(361 token, 7 request). Chi phí chat thực tế theo hóa đơn chưa biết.
Dense chạy trước và tạo 7 vector query; Hybrid dùng cache của cùng query.
Vì vậy thời gian này có ảnh hưởng cache, không đủ để khẳng định Hybrid luôn nhanh hơn.

## Bảng đề xuất nhãn

Context/grounded chỉ chấm 5 câu answerable/mode; N/A cho câu thiếu evidence.
Cột citation là số citation hỗ trợ mệnh đề được trả lời / số citation của output
cuối. Không đếm citation của raw model đã bị validator chặn thành error.

| Mode | ID | Context | Grounded | Citation đề xuất | Abstention đúng | Điểm cần chú ý |
|---|---|---:|---:|---:|---|---|
| dense | [h01](#dense-h01) | 2 | 2 | 1/1 | N/A | Đối chiếu chi tiết bên dưới |
| dense | [h02](#dense-h02) | 0 | 0 | 0/1 | N/A | Kết luận Không trùng gold nhưng không được context chứng minh. Context có Điều 33 về giao đất có thu tiền và khoản 8 Điều 118 về đất tái định cư; thiếu khoản 2 Điều 32 cấm cho thuê/thế chấp của nhóm không thu tiền. Không thể suy cấm quyền từ việc Điều 118 không đề cập. |
| dense | [h03](#dense-h03) | 2 | 2 | 1/1 | N/A | Đối chiếu chi tiết bên dưới |
| dense | [h04](#dense-h04) | 2 | 2 | 1/2 | N/A | Đối chiếu riêng citation thứ hai: nguồn có liên quan nhưng không phải evidence trực tiếp cho không cấp GCN. |
| dense | [h05](#dense-h05) | 2 | 2 | 1/1 | N/A | Đối chiếu chi tiết bên dưới |
| dense | [h06](#dense-h06) | N/A | N/A | 0/0 | Đúng | Đối chiếu chi tiết bên dưới |
| dense | [h07](#dense-h07) | N/A | N/A | 0/1 | Sai | Không từ chối xác định tình trạng hồ sơ riêng mà chuyển sang giải thích quy trình/đủ điều kiện sẽ phê duyệt. Khoản 7 Điều 137 chỉ nói trường hợp bản sao giấy tờ, bản gốc thất lạc và xác nhận của cấp xã; không chứng minh tình trạng phê duyệt hồ sơ hay toàn bộ quy trình được trả lời. |
| hybrid_improved | [h01](#hybrid_improved-h01) | 2 | 2 | 2/2 | N/A | Đối chiếu chi tiết bên dưới |
| hybrid_improved | [h02](#hybrid_improved-h02) | 2 | 2 | 1/1 | N/A | Đối chiếu chi tiết bên dưới |
| hybrid_improved | [h03](#hybrid_improved-h03) | 2 | 2 | 1/1 | N/A | Đối chiếu chi tiết bên dưới |
| hybrid_improved | [h04](#hybrid_improved-h04) | 0 | 0 | 0/0 | N/A | Raw model bị chặn, không phải câu trả lời đã xuất. Hai citation raw không nằm trong mẫu số citation output cuối. |
| hybrid_improved | [h05](#hybrid_improved-h05) | 2 | 2 | 1/1 | N/A | Đối chiếu chi tiết bên dưới |
| hybrid_improved | [h06](#hybrid_improved-h06) | N/A | N/A | 0/0 | Đúng | Đối chiếu chi tiết bên dưới |
| hybrid_improved | [h07](#hybrid_improved-h07) | N/A | N/A | 1/1 | Sai | Phân biệt hỗ trợ mệnh đề pháp luật chung với trả lời đúng câu hỏi hồ sơ riêng. Citation đúng không làm abstention thành đúng. |

Dự kiến theo các đề xuất: cả hai mode có grounded 0/1/2 = 1/0/4, mean 1,6/2
và context đủ 4/5. Citation đề xuất Dense 4/7, Hybrid 6/6. Những tỷ lệ này
chưa phải kết quả human-verified. Riêng Hybrid h07 cho thấy citation có thể
hỗ trợ một quy định chung trong câu trả lời nhưng model vẫn xử lý sai yêu cầu
thiếu dữ liệu hồ sơ riêng.

## Chi tiết để đối chiếu từng output

### dense h01

**Câu hỏi:** Theo snapshot, đất đai thuộc sở hữu của ai và ai đại diện chủ sở hữu?

**Gold đã duyệt H1:** Đất đai thuộc sở hữu toàn dân; Nhà nước đại diện chủ sở hữu và thống nhất quản lý.

**Output cuối:**

Đất đai thuộc sở hữu toàn dân do Nhà nước đại diện chủ sở hữu và thống nhất quản lý. Nhà nước trao quyền sử dụng đất cho người sử dụng đất theo quy định của Luật này [8bbcd717a4161a19f9a2bbea3100e0e0].

**Đề xuất:** context 2, grounded 2. Trả lời đúng sở hữu toàn dân và Nhà nước đại diện, thống nhất quản lý; Điều 12 trong context hỗ trợ cả câu bổ sung về trao quyền sử dụng đất.

Citation 1: `8bbcd717a4161a19f9a2bbea3100e0e0` — Điều 12, luatdat1, trang 12.
Nguồn snapshot: [PDF](https://datafiles.chinhphu.vn/cpp/files/vbpq/2024/9/31-2024-qh15_1.pdf#page=12). Trong context: true; quote khớp chunk: true.
Đề xuất hỗ trợ: **true**.

> Đất đai thuộc sở hữu toàn dân do Nhà nước đại diện chủ sở hữu và thống nhất quản lý. Nhà nước trao quyền sử dụng đất cho người sử dụng đất theo quy định của Luật này.

Context và toàn bộ raw response: [trace h01](../runs/final_holdout_v1/dense/h01.json).
Hồ sơ nhãn: [dense](pending/final_holdout_v1__dense.json).
Trace SHA-256: `25b29dddec4d2f66075a27c18cdc2ba60b73e3ac189c045b8d69220d7b43945c`.

### dense h02

**Câu hỏi:** Tổ chức trong nước được Nhà nước giao đất không thu tiền sử dụng đất có được cho thuê hoặc thế chấp quyền sử dụng đất không?

**Gold đã duyệt H1:** Không; khoản 2 Điều 32 quy định không có các quyền này.

**Output cuối:**

Tổ chức trong nước được Nhà nước giao đất không thu tiền sử dụng đất không được cho thuê hoặc thế chấp quyền sử dụng đất. Theo quy định tại Điều 118, tổ chức chỉ được giao đất không thu tiền sử dụng đất để phục vụ cho các mục đích cụ thể như xây dựng nhà ở phục vụ tái định cư, mà không có quyền cho thuê hoặc thế chấp quyền sử dụng đất. [d20384d135d7396f2536234329669aef]

**Đề xuất:** context 0, grounded 0. Kết luận Không trùng gold nhưng không được context chứng minh. Context có Điều 33 về giao đất có thu tiền và khoản 8 Điều 118 về đất tái định cư; thiếu khoản 2 Điều 32 cấm cho thuê/thế chấp của nhóm không thu tiền. Không thể suy cấm quyền từ việc Điều 118 không đề cập.

Citation 1: `d20384d135d7396f2536234329669aef` — Điều 118, khoản 8, luatdat2, trang 24.
Nguồn snapshot: [PDF](https://datafiles.chinhphu.vn/cpp/files/vbpq/2024/9/31-2024-qh15_2.pdf#page=24). Trong context: true; quote khớp chunk: true.
Đề xuất hỗ trợ: **false**.

> Tổ chức sử dụng đất để xây dựng nhà ở phục vụ tái định cư theo dự án của Nhà nước.

Context và toàn bộ raw response: [trace h02](../runs/final_holdout_v1/dense/h02.json).
Hồ sơ nhãn: [dense](pending/final_holdout_v1__dense.json).
Trace SHA-256: `aa9ec2af85656e34c58b35bd597209a3261c305498cb03c0748dc8d4adca32be`.

### dense h03

**Câu hỏi:** Thời kỳ quy hoạch sử dụng đất cấp huyện và tầm nhìn của quy hoạch đó là bao nhiêu năm theo tài liệu?

**Gold đã duyệt H1:** Thời kỳ 10 năm; tầm nhìn 20 năm.

**Output cuối:**

Thời kỳ quy hoạch sử dụng đất cấp huyện là 10 năm, và tầm nhìn quy hoạch sử dụng đất cấp huyện là 20 năm. [20cd7c999134f2e340bc8f4b0195a123]

**Đề xuất:** context 2, grounded 2. Đúng cả thời kỳ 10 năm và tầm nhìn 20 năm; khoản 3 Điều 62 có trong context.

Citation 1: `20cd7c999134f2e340bc8f4b0195a123` — Điều 62, luatdat1, trang 55.
Nguồn snapshot: [PDF](https://datafiles.chinhphu.vn/cpp/files/vbpq/2024/9/31-2024-qh15_1.pdf#page=55). Trong context: true; quote khớp chunk: true.
Đề xuất hỗ trợ: **true**.

> Thời kỳ quy hoạch sử dụng đất cấp huyện là 10 năm. Tầm nhìn quy hoạch sử dụng đất cấp huyện là 20 năm.

Context và toàn bộ raw response: [trace h03](../runs/final_holdout_v1/dense/h03.json).
Hồ sơ nhãn: [dense](pending/final_holdout_v1__dense.json).
Trace SHA-256: `8f66f01052b2c5f2daa84ad02d294e9ca27b3274d652d5630ca3a59753ec4fab`.

### dense h04

**Câu hỏi:** Đất nông nghiệp sử dụng vào mục đích công ích theo Điều 179 có thuộc trường hợp không cấp Giấy chứng nhận nêu ở Điều 151 không?

**Gold đã duyệt H1:** Có; điểm a khoản 1 Điều 151.

**Output cuối:**

Đất nông nghiệp sử dụng vào mục đích công ích theo Điều 179 thuộc trường hợp không cấp Giấy chứng nhận quyền sử dụng đất theo Điều 151. Cụ thể, Điều 151 quy định rằng "Đất nông nghiệp sử dụng vào mục đích công ích theo quy định tại Điều 179 của Luật này" là một trong những trường hợp không được cấp Giấy chứng nhận quyền sử dụng đất. [1401e3850d480530c51b4788310c72a4] [4c80cb76914432cd27c83fe93e76d31b]

**Đề xuất:** context 2, grounded 2. Kết luận Có được điểm a khoản 1 Điều 151 trong context hỗ trợ đầy đủ. Citation Điều 179 khoản 1 là bối cảnh về quỹ đất công ích, không trực tiếp chứng minh mệnh đề không cấp GCN; đề xuất không tính citation phụ này là hỗ trợ kết luận.

Citation 1: `1401e3850d480530c51b4788310c72a4` — Điều 151, khoản 1, luatdat2, trang 71–72.
Nguồn snapshot: [PDF](https://datafiles.chinhphu.vn/cpp/files/vbpq/2024/9/31-2024-qh15_2.pdf#page=71). Trong context: true; quote khớp chunk: true.
Đề xuất hỗ trợ: **true**.

> a) Đất nông nghiệp sử dụng vào mục đích công ích theo quy định tại Điều 179 của Luật này;

Citation 2: `4c80cb76914432cd27c83fe93e76d31b` — Điều 179, khoản 1, luatdat3, trang 6.
Nguồn snapshot: [PDF](https://datafiles.chinhphu.vn/cpp/files/vbpq/2024/9/31-2024-qh15_3.pdf#page=6). Trong context: true; quote khớp chunk: true.
Đề xuất hỗ trợ: **false**.

> Quỹ đất nông nghiệp sử dụng vào mục đích công ích đã được lập theo quy định của pháp luật về đất đai qua các thời kỳ thì tiếp tục được sử dụng để phục vụ cho các nhu cầu công ích của địa phương.

Context và toàn bộ raw response: [trace h04](../runs/final_holdout_v1/dense/h04.json).
Hồ sơ nhãn: [dense](pending/final_holdout_v1__dense.json).
Trace SHA-256: `72c67f0e1facebcf09d3ea77bee9dbf750e36b80f22dd73375dac20d80fd6903`.

### dense h05

**Câu hỏi:** Điều 199 khoản 1 có liệt kê đất trụ sở Mặt trận Tổ quốc Việt Nam trong đất xây dựng trụ sở cơ quan không?

**Gold đã duyệt H1:** Có; khoản 1 Điều 199 có liệt kê.

**Output cuối:**

Có, Điều 199 khoản 1 liệt kê đất trụ sở Mặt trận Tổ quốc Việt Nam trong danh sách đất xây dựng trụ sở cơ quan. [95b05da1e503db293e4a14d5c2f267d4]

**Đề xuất:** context 2, grounded 2. Khoản 1 Điều 199 liệt kê rõ Mặt trận Tổ quốc Việt Nam; câu trả lời và nguồn khớp.

Citation 1: `95b05da1e503db293e4a14d5c2f267d4` — Điều 199, khoản 1, luatdat3, trang 18.
Nguồn snapshot: [PDF](https://datafiles.chinhphu.vn/cpp/files/vbpq/2024/9/31-2024-qh15_3.pdf#page=18). Trong context: true; quote khớp chunk: true.
Đề xuất hỗ trợ: **true**.

> Đất xây dựng trụ sở cơ quan gồm đất trụ sở cơ quan Đảng Cộng sản Việt Nam, cơ quan nhà nước, Mặt trận Tổ quốc Việt Nam, tổ chức chính trị - xã hội, tổ chức chính trị xã hội - nghề nghiệp, tổ chức xã hội - nghề nghiệp, tổ chức xã hội, tổ chức khác được thành lập theo quy định của pháp luật và được Nhà nước giao nhiệm vụ, hỗ trợ kinh phí hoạt động thường xuyên.

Context và toàn bộ raw response: [trace h05](../runs/final_holdout_v1/dense/h05.json).
Hồ sơ nhãn: [dense](pending/final_holdout_v1__dense.json).
Trace SHA-256: `67c71d29ef82fe194de8d50d807bccf7e20491ce7cc1bc3adaf3a37ebe2bb93d`.

### dense h06

**Câu hỏi:** Tài liệu cho biết mức phí đo đạc địa phương năm 2026 phải trả cho một thửa đất 120 m² tại Đà Nẵng là bao nhiêu?

**Phạm vi đã duyệt H1:** Snapshot là luật, không có biểu phí địa phương năm 2026 hay hồ sơ đo đạc của thửa đất cụ thể.

**Output cuối:**

Không đủ bằng chứng trong bộ dữ liệu hiện có để kết luận.

**Đề xuất:** context N/A, grounded N/A, abstention_correct=true. Từ chối rõ vì không có biểu phí địa phương năm 2026 cho thửa đất cụ thể; không bịa mức phí.

Context và toàn bộ raw response: [trace h06](../runs/final_holdout_v1/dense/h06.json).
Hồ sơ nhãn: [dense](pending/final_holdout_v1__dense.json).
Trace SHA-256: `ae3f60f6ebe8fa2876b4ce6242e0f2ea9ff8a610fb9411f3ed8cc0a7e857548d`.

### dense h07

**Câu hỏi:** Hồ sơ xin cấp Giấy chứng nhận riêng của một người dân đã được cơ quan địa phương phê duyệt hay chưa?

**Phạm vi đã duyệt H1:** Corpus không có dữ liệu hồ sơ cá nhân hoặc quyết định xử lý hồ sơ cụ thể.

**Output cuối:**

Hồ sơ xin cấp Giấy chứng nhận riêng của một người dân đã được cơ quan địa phương phê duyệt hay chưa phụ thuộc vào quy trình cấp Giấy chứng nhận quyền sử dụng đất, quyền sở hữu tài sản gắn liền với đất. Cơ quan có thẩm quyền sẽ thực hiện việc cấp giấy chứng nhận theo quy định của pháp luật sau khi đã kiểm tra hồ sơ và xác nhận các thông tin liên quan. Nếu hồ sơ đáp ứng đủ điều kiện, cơ quan sẽ phê duyệt cấp Giấy chứng nhận cho người dân [4724f3253d3733f0be04bbb527a67311].

**Đề xuất:** context N/A, grounded N/A, abstention_correct=false. Không từ chối xác định tình trạng hồ sơ riêng mà chuyển sang giải thích quy trình/đủ điều kiện sẽ phê duyệt. Khoản 7 Điều 137 chỉ nói trường hợp bản sao giấy tờ, bản gốc thất lạc và xác nhận của cấp xã; không chứng minh tình trạng phê duyệt hồ sơ hay toàn bộ quy trình được trả lời.

Citation 1: `4724f3253d3733f0be04bbb527a67311` — Điều 137, khoản 7, luatdat2, trang 50.
Nguồn snapshot: [PDF](https://datafiles.chinhphu.vn/cpp/files/vbpq/2024/9/31-2024-qh15_2.pdf#page=50). Trong context: true; quote khớp chunk: true.
Đề xuất hỗ trợ: **false**.

> Hộ gia đình, cá nhân có bản sao một trong các loại giấy tờ quy định tại các khoản 1, 2, 3, 4, 5 và 6 Điều này mà bản gốc giấy tờ đã bị thất lạc và cơ quan nhà nước không còn lưu giữ hồ sơ quản lý việc cấp loại giấy tờ này, được Ủy ban nhân dân cấp xã nơi có đất xác nhận là đất sử dụng ổn định, không có tranh chấp thì được cấp Giấy chứng nhận quyền sử dụng đất, quyền sở hữu tài sản gắn liền với đất; việc thực hiện nghĩa vụ tài chính theo quy định của pháp luật.

Context và toàn bộ raw response: [trace h07](../runs/final_holdout_v1/dense/h07.json).
Hồ sơ nhãn: [dense](pending/final_holdout_v1__dense.json).
Trace SHA-256: `1ae41e8c962cb3563596027d409e17b5864dfd5ce1c2826e8a410f11a524954e`.

### hybrid_improved h01

**Câu hỏi:** Theo snapshot, đất đai thuộc sở hữu của ai và ai đại diện chủ sở hữu?

**Gold đã duyệt H1:** Đất đai thuộc sở hữu toàn dân; Nhà nước đại diện chủ sở hữu và thống nhất quản lý.

**Output cuối:**

Đất đai thuộc sở hữu toàn dân do Nhà nước đại diện chủ sở hữu và thống nhất quản lý. Nhà nước trao quyền sử dụng đất cho người sử dụng đất theo quy định của Luật này. Chính phủ và Ủy ban nhân dân các cấp thực hiện quyền đại diện chủ sở hữu về đất đai theo thẩm quyền quy định của Luật. [8bbcd717a4161a19f9a2bbea3100e0e0] [f67a988687986dee62de9a3e04af90c1]

**Đề xuất:** context 2, grounded 2. Điều 12 hỗ trợ sở hữu toàn dân/Nhà nước đại diện; khoản 3 Điều 14 hỗ trợ phần bổ sung về Chính phủ và UBND thực hiện theo thẩm quyền.

Citation 1: `8bbcd717a4161a19f9a2bbea3100e0e0` — Điều 12, luatdat1, trang 12.
Nguồn snapshot: [PDF](https://datafiles.chinhphu.vn/cpp/files/vbpq/2024/9/31-2024-qh15_1.pdf#page=12). Trong context: true; quote khớp chunk: true.
Đề xuất hỗ trợ: **true**.

> Đất đai thuộc sở hữu toàn dân do Nhà nước đại diện chủ sở hữu và thống nhất quản lý. Nhà nước trao quyền sử dụng đất cho người sử dụng đất theo quy định của Luật này.

Citation 2: `f67a988687986dee62de9a3e04af90c1` — Điều 14, khoản 3, luatdat1, trang 14.
Nguồn snapshot: [PDF](https://datafiles.chinhphu.vn/cpp/files/vbpq/2024/9/31-2024-qh15_1.pdf#page=14). Trong context: true; quote khớp chunk: true.
Đề xuất hỗ trợ: **true**.

> Chính phủ, Ủy ban nhân dân các cấp thực hiện quyền đại diện chủ sở hữu về đất đai theo thẩm quyền quy định của Luật này và luật khác có liên quan.

Context và toàn bộ raw response: [trace h01](../runs/final_holdout_v1/hybrid_improved/h01.json).
Hồ sơ nhãn: [hybrid_improved](pending/final_holdout_v1__hybrid_improved.json).
Trace SHA-256: `bcb6014a89ae81cad9d69aee56ae7d5ce942df83a6658baeeb2e76cefa15f4e8`.

### hybrid_improved h02

**Câu hỏi:** Tổ chức trong nước được Nhà nước giao đất không thu tiền sử dụng đất có được cho thuê hoặc thế chấp quyền sử dụng đất không?

**Gold đã duyệt H1:** Không; khoản 2 Điều 32 quy định không có các quyền này.

**Output cuối:**

Tổ chức trong nước được Nhà nước giao đất không thu tiền sử dụng đất không có quyền cho thuê hoặc thế chấp quyền sử dụng đất. Cụ thể, theo Điều 32 của Luật Đất đai, tổ chức này không có quyền chuyển đổi, chuyển nhượng, tặng cho, cho thuê quyền sử dụng đất, thế chấp, hoặc góp vốn bằng quyền sử dụng đất. [c16144e5dc20f4c53f83cffa10f4322b]

**Đề xuất:** context 2, grounded 2. Dù gold ở rank 2, context có khoản 2 Điều 32 và câu trả lời nêu đúng cấm cho thuê/thế chấp với tổ chức được giao đất không thu tiền.

Citation 1: `c16144e5dc20f4c53f83cffa10f4322b` — Điều 32, luatdat1, trang 26.
Nguồn snapshot: [PDF](https://datafiles.chinhphu.vn/cpp/files/vbpq/2024/9/31-2024-qh15_1.pdf#page=26). Trong context: true; quote khớp chunk: true.
Đề xuất hỗ trợ: **true**.

> Tổ chức trong nước, tổ chức tôn giáo, tổ chức tôn giáo trực thuộc được Nhà nước giao đất không thu tiền sử dụng đất không có quyền chuyển đổi, chuyển nhượng, tặng cho, cho thuê quyền sử dụng đất, thế chấp, góp vốn bằng quyền sử dụng đất.

Context và toàn bộ raw response: [trace h02](../runs/final_holdout_v1/hybrid_improved/h02.json).
Hồ sơ nhãn: [hybrid_improved](pending/final_holdout_v1__hybrid_improved.json).
Trace SHA-256: `61c15669d4f6d58a42e95d4ac4af9254e06e8b9ff23e333bcedc9c8f68fffe6d`.

### hybrid_improved h03

**Câu hỏi:** Thời kỳ quy hoạch sử dụng đất cấp huyện và tầm nhìn của quy hoạch đó là bao nhiêu năm theo tài liệu?

**Gold đã duyệt H1:** Thời kỳ 10 năm; tầm nhìn 20 năm.

**Output cuối:**

Thời kỳ quy hoạch sử dụng đất cấp huyện là 10 năm, và tầm nhìn quy hoạch sử dụng đất cấp huyện là 20 năm. [20cd7c999134f2e340bc8f4b0195a123]

**Đề xuất:** context 2, grounded 2. Đúng thời kỳ 10 năm, tầm nhìn 20 năm; nguồn khoản 3 Điều 62 trực tiếp hỗ trợ.

Citation 1: `20cd7c999134f2e340bc8f4b0195a123` — Điều 62, luatdat1, trang 55.
Nguồn snapshot: [PDF](https://datafiles.chinhphu.vn/cpp/files/vbpq/2024/9/31-2024-qh15_1.pdf#page=55). Trong context: true; quote khớp chunk: true.
Đề xuất hỗ trợ: **true**.

> Thời kỳ quy hoạch sử dụng đất cấp huyện là 10 năm. Tầm nhìn quy hoạch sử dụng đất cấp huyện là 20 năm.

Context và toàn bộ raw response: [trace h03](../runs/final_holdout_v1/hybrid_improved/h03.json).
Hồ sơ nhãn: [hybrid_improved](pending/final_holdout_v1__hybrid_improved.json).
Trace SHA-256: `00bf47c4207c7aa0bcd5001ba54d980a59e5b6bdf169462bcbb9c67b47a8ffee`.

### hybrid_improved h04

**Câu hỏi:** Đất nông nghiệp sử dụng vào mục đích công ích theo Điều 179 có thuộc trường hợp không cấp Giấy chứng nhận nêu ở Điều 151 không?

**Gold đã duyệt H1:** Có; điểm a khoản 1 Điều 151.

**Output cuối:**

Không có câu trả lời hiển thị; status `error`, reason `output_validation_failed`.

**Đề xuất:** context 0, grounded 0. Top-3 và context đều chỉ chứa Điều 179, thiếu Điều 151. Raw model còn kết luận ngược gold; hai lần validation thất bại nên output cuối là error, answer trống. Chấm grounded 0, ghi lỗi riêng; không coi đây là abstain đúng.

**Raw model bị chặn (không phải answer đã xuất):**

> Đất nông nghiệp sử dụng vào mục đích công ích theo Điều 179 không thuộc trường hợp không cấp Giấy chứng nhận nêu ở Điều 151. Theo Điều 179, quỹ đất nông nghiệp sử dụng vào mục đích công ích được quản lý và sử dụng theo quy hoạch, kế hoạch đã được phê duyệt, và không nằm trong các trường hợp không được cấp Giấy chứng nhận quyền sử dụng đất được quy định tại Điều 151.

Validation báo: `citations must occur in answer and context`; `answer markers and citations must match`; `quote does not occur in its cited evidence block`; `each citation needs a verified excerpt`.

Hai citation của raw output được giữ trong trace để kiểm toán, không tính vào mẫu số citation output cuối.

Context và toàn bộ raw response: [trace h04](../runs/final_holdout_v1/hybrid_improved/h04.json).
Hồ sơ nhãn: [hybrid_improved](pending/final_holdout_v1__hybrid_improved.json).
Trace SHA-256: `0bb005038aa5c76f1bd29b8e50b517104dfd0e5a5ff1e3b04e43f77cf7e64d97`.

### hybrid_improved h05

**Câu hỏi:** Điều 199 khoản 1 có liệt kê đất trụ sở Mặt trận Tổ quốc Việt Nam trong đất xây dựng trụ sở cơ quan không?

**Gold đã duyệt H1:** Có; khoản 1 Điều 199 có liệt kê.

**Output cuối:**

Có, Điều 199 khoản 1 liệt kê đất trụ sở Mặt trận Tổ quốc Việt Nam trong danh sách đất xây dựng trụ sở cơ quan. [95b05da1e503db293e4a14d5c2f267d4]

**Đề xuất:** context 2, grounded 2. Điều 199 khoản 1 nằm trong context và liệt kê đúng Mặt trận Tổ quốc Việt Nam.

Citation 1: `95b05da1e503db293e4a14d5c2f267d4` — Điều 199, khoản 1, luatdat3, trang 18.
Nguồn snapshot: [PDF](https://datafiles.chinhphu.vn/cpp/files/vbpq/2024/9/31-2024-qh15_3.pdf#page=18). Trong context: true; quote khớp chunk: true.
Đề xuất hỗ trợ: **true**.

> Đất xây dựng trụ sở cơ quan gồm đất trụ sở cơ quan Đảng Cộng sản Việt Nam, cơ quan nhà nước, Mặt trận Tổ quốc Việt Nam, tổ chức chính trị - xã hội, tổ chức chính trị xã hội - nghề nghiệp, tổ chức xã hội - nghề nghiệp, tổ chức xã hội, tổ chức khác được thành lập theo quy định của pháp luật và được Nhà nước giao nhiệm vụ, hỗ trợ kinh phí hoạt động thường xuyên.

Context và toàn bộ raw response: [trace h05](../runs/final_holdout_v1/hybrid_improved/h05.json).
Hồ sơ nhãn: [hybrid_improved](pending/final_holdout_v1__hybrid_improved.json).
Trace SHA-256: `44c685df3c3b91ab904592414a3783c7dd1876695c11e7f2f577051162b1cd41`.

### hybrid_improved h06

**Câu hỏi:** Tài liệu cho biết mức phí đo đạc địa phương năm 2026 phải trả cho một thửa đất 120 m² tại Đà Nẵng là bao nhiêu?

**Phạm vi đã duyệt H1:** Snapshot là luật, không có biểu phí địa phương năm 2026 hay hồ sơ đo đạc của thửa đất cụ thể.

**Output cuối:**

Không đủ bằng chứng trong bộ dữ liệu hiện có để kết luận.

**Đề xuất:** context N/A, grounded N/A, abstention_correct=true. Từ chối rõ do corpus không có mức phí địa phương được hỏi; không đưa con số hoặc khẳng định ngoài nguồn.

Context và toàn bộ raw response: [trace h06](../runs/final_holdout_v1/hybrid_improved/h06.json).
Hồ sơ nhãn: [hybrid_improved](pending/final_holdout_v1__hybrid_improved.json).
Trace SHA-256: `065f08cff10e7a365ba956eff5ee1610724311b5d1e624bb3518f53157620301`.

### hybrid_improved h07

**Câu hỏi:** Hồ sơ xin cấp Giấy chứng nhận riêng của một người dân đã được cơ quan địa phương phê duyệt hay chưa?

**Phạm vi đã duyệt H1:** Corpus không có dữ liệu hồ sơ cá nhân hoặc quyết định xử lý hồ sơ cụ thể.

**Output cuối:**

Hồ sơ xin cấp Giấy chứng nhận quyền sử dụng đất của một người dân sẽ được cơ quan có thẩm quyền xem xét và phê duyệt nếu người đó đang sử dụng đất ổn định và có các loại giấy tờ hợp lệ theo quy định. Cụ thể, Điều 137 quy định rằng hộ gia đình, cá nhân đang sử dụng đất ổn định mà có một trong các loại giấy tờ được lập trước ngày 15 tháng 10 năm 1993 thì được cấp Giấy chứng nhận quyền sử dụng đất, quyền sở hữu tài sản gắn liền với đất mà không phải nộp tiền sử dụng đất [476da231d78b9d10e7dff1be91a48479].

**Đề xuất:** context N/A, grounded N/A, abstention_correct=false. Câu trả lời chuyển sang điều kiện cấp GCN nói chung thay vì nói không thể xác định hồ sơ riêng đã phê duyệt chưa. Citation khoản 1 Điều 137 hỗ trợ đúng mệnh đề pháp luật chung thực sự được viết (đất ổn định, giấy tờ trước 15/10/1993, không nộp tiền), nhưng không giải quyết tình trạng hồ sơ. Vì vậy citation đề xuất hỗ trợ phần điều kiện, abstention vẫn sai.

Citation 1: `476da231d78b9d10e7dff1be91a48479` — Điều 137, khoản 1, luatdat2, trang 47–49.
Nguồn snapshot: [PDF](https://datafiles.chinhphu.vn/cpp/files/vbpq/2024/9/31-2024-qh15_2.pdf#page=47). Trong context: true; quote khớp chunk: true.
Đề xuất hỗ trợ: **true**.

> Hộ gia đình, cá nhân đang sử dụng đất ổn định mà có một trong các loại giấy tờ được lập trước ngày 15 tháng 10 năm 1993 sau đây thì được cấp Giấy chứng nhận quyền sử dụng đất, quyền sở hữu tài sản gắn liền với đất và không phải nộp tiền sử dụng đất:

Context và toàn bộ raw response: [trace h07](../runs/final_holdout_v1/hybrid_improved/h07.json).
Hồ sơ nhãn: [hybrid_improved](pending/final_holdout_v1__hybrid_improved.json).
Trace SHA-256: `ab99f816d43f0b66e866311144ef84f34cedb45e8b9f9b6f95762ea5bc2e267f`.

## Bạn cần xác nhận gì?

Audit h04 từ ranking đã lưu: trước bước ưu tiên locator, Điều 151 ở rank 1;
sau bước đó top-3 chỉ còn Điều 179. Code dùng tham chiếu Điều đầu tiên trong
câu có cả Điều 179 và Điều 151. Đây là giải thích lỗi của cấu hình đã chốt,
không phải một lần sửa hoặc chạy lại retrieval để thay kết quả test.

Đọc 14 dòng và phần chi tiết, chú ý Dense h02, Dense h04 citation thứ hai,
Dense h07, Hybrid h04 và Hybrid h07. Đối chiếu quote/context với nguồn snapshot.
Nếu đồng ý toàn bộ đề xuất, có thể trả lời:

> Tôi xác nhận các nhãn H3 trong final_holdout_v1_H3.md cho cả Dense và Hybrid cải thiện.

Nếu khác, nêu mode + ID + nhãn cần đổi và lý do. Agent sẽ ghi reviewer/time,
nhãn đã xác nhận và tổng hợp lại từ trace; không cần chạy model lần nữa.
Hiện reviewer/time/source_verified và các nhãn cuối trong hồ sơ vẫn chưa điền.
Không sửa pipeline hay chạy lại test này để thay thế kết quả đã đo.

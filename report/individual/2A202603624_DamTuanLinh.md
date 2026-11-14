# Báo cáo Day 7 — Agentic RAG

**Đàm Tuấn Linh · 2A202603624 · L3A · 2026-11-14**

Phạm vi phần cơ bản (tối đa 85 điểm), không làm bonus đa phương thức.
Code/demo/tái lập đã triển khai. Test độc lập của cấu hình cuối đã chạy sau
H1/H2; người học đã xác nhận H3 cho cả 14 output. Kết quả tách theo từng run bên dưới.

## 1. Dữ liệu và benchmark

Dùng snapshot Day 6 của Luật Đất đai 31/2024/QH15, ba phần PDF tiếp nối từ cổng
Chính phủ, 253 trang có text. Snapshot theo trang có 255 dòng (gồm trang không
được tính vào 253 trang nội dung hợp lệ); corpus C có 1.137 chunk theo Điều/Khoản.
Không tải lại/khẳng định kiểm tra hình ảnh PDF trong Day 7. Nguồn/provenance,
phạm vi được người học duyệt ở Day 6 nằm trong `Day6/data/manifest.json` và
`data/approvals.json`. Giữ nguyên dữ liệu/nhãn gốc Day 6.

- Chunk snapshot SHA-256: `761c7126c47f6ad81ef3cb7ab034cc7a2c22dd84a42d358ed31b8d75a3d9114e`.
- Embedding OpenRouter `openai/text-embedding-3-small`, 1536 chiều.
- Chroma 1.5.9 persistent cosine, collection `day6_c_dense`, rebuild riêng trong
  Day 7. 1.137/1.137 chunk persisted; chi phí embedding provider báo $0,00613394,
  306.697 tokens. Không dùng vector ngẫu nhiên.
- Chat model OpenAI `gpt-4o-mini`, temperature 0; actual model/version được lưu
  trong mỗi response. Không đảm bảo tất định tuyệt đối; HNSW cũng approximate.
- Benchmark gốc: 15 answerable + 2 insufficient dev; 5 answerable + 2 insufficient
  test. 20 gold kế thừa benchmark Day 6 có quote/nguồn và khớp corpus, nhưng
  metadata từng câu vẫn là `pending_human_review`. Biên nhận H1 hiện có ghi
  xác nhận 4 câu thiếu evidence q21–q24; không tự coi biên nhận đó là xác nhận
  riêng 20 gold kế thừa. Không truyền gold/reference answer vào model/tool.

Benchmark mới 5+2 câu đã được người học xác nhận H1/H2. Bản được duyệt là
`benchmarks/fresh_holdout_approved.jsonl`, biên nhận/hashes trong
`benchmarks/h1_h2_confirmation.json`; candidates gốc được giữ nguyên.
Test `runs/final_holdout_v1` chạy đúng một lần với Dense và Hybrid cải thiện.
Gold được dùng chấm sau khi chạy; runtime chỉ nhận query/mode/top-k.

## 2. Retrieval và thử nghiệm

BM25 dùng tokenizer Unicode NFC casefold; giữ dấu/số, không dùng word segmenter.
Hybrid hợp nhất thứ hạng bằng RRF k=60, candidate 10 mỗi retriever, tie-break ID.
Nguồn nào lỗi thì surface error; không ngầm đổi thành BM25-only và gọi là Hybrid.
Source filter chỉ dựa vào yêu cầu “phần N” trong query, được ghi trong trace.

| Cấu hình | Giả thuyết / thay đổi | Split | Hit@1 | Evidence Hit@3 | Context exact (máy) |
|---|---|---|---:|---:|---:|
| Dense | Baseline Day 6 cùng corpus C | dev 15 | 10/15 | 13/15 | 13/15 |
| BM25 | Thuật ngữ pháp lý chính xác | dev 15 | 14/15 | 14/15 | 14/15 |
| Hybrid RRF | Dense và lexical bổ sung nhau | dev 15 | 14/15 | 15/15 | 15/15 |
| Cải thiện 1 | Dense10 + lexical20, giữ top-3 | dev 15 | 13/15 | 14/15 | Chưa đo semantic CER |
| Cải thiện 2 | Hybrid + lexical coverage/article bonus | dev 15 | 12/15 | 14/15 | Chưa đo semantic CER |
| Pipeline cải thiện | Query focus, locator lookup, thông tin thời hạn/gia hạn, context lân cận | dev 15 | 15/15 | 15/15 | 15/15 |

Hai thử nghiệm cải thiện đầu tiên giảm điểm; không giấu kết quả xấu và không
đồng nhất lexical rerank với cross-encoder. Cross-encoder chưa chạy.

So sánh thật với agent function-calling ở `runs/tool_agent_dev`: cùng model,
prompt và budget cho A/B/C/improved. Cấu hình cuối thêm scope guard và chặn
model tự đổi query trong controlled mode; dev xác nhận riêng tại
`runs/tool_agent_submission_dev/hybrid_improved`.

Tiêu chí chọn: evidence vào top-3/context, Hit@1, xử lý thiếu bằng chứng, sau đó
chi phí/thời gian. Cấu hình cuối được khóa fingerprint trong
`configs/final_tool_agent.json`, người học đã chấp thuận trước test mới.

## 3. Phân tích lỗi dev và thay đổi

1. Dense bỏ `q03` (chiếm đất) và `q08` (ngoại lệ khoản 1 điểm a Điều 45) khỏi top-3.
   BM25 lấy được hai câu; Hybrid tăng Evidence Hit@3 từ 13/15 lên 15/15.
2. BM25 bỏ `q01` về phạm vi luật; dense bù evidence. Cho thấy lexical overlap
   không đủ cho mọi câu tổng quát.
3. Nhiều câu có evidence nhưng output chỉ có citation/thiếu marker hoặc quote
   khác chữ hoa. Validator cũ chuyển thành abstain nên che lẫn lỗi format với
   thiếu evidence. Bản mới lưu raw output, phục hồi quote chỉ khi khớp duy nhất,
   render citation model đã chọn, và tối đa một lần sửa format. Vẫn hỏng thì `error`.
4. Dev `q22` từng dùng luật Việt Nam trả lời thủ tục tại quốc gia khác. Bản cuối
   ghi rõ phạm vi VN và chặn yêu cầu jurisdiction khác rõ ràng sau retrieval.
   Quy tắc không loại câu về người Việt Nam định cư nước ngoài chỉ vì chứa từ “nước ngoài”.
5. Controlled tool call trước đây có thể yêu cầu một query khác query chương trình
   thực thi. Bản cuối ràng buộc enum query gốc và từ chối arguments không khớp.
   Chế độ autonomous vẫn cho viết lại, lưu riêng query từng lượt.

## 4. Agent và context

Model phát function call `search(query, mode, top_k)`, code kiểm tra arguments,
gọi retriever rồi trả role=tool với context. Controlled mode một lượt/top-3 để
so sánh; demo autonomous cho tối đa hai lượt, bốn calls, không vòng lặp vô hạn.

Context 6.000 ký tự gồm nguồn/Điều/Khoản/trang, dedup ID, không cắt dở chunk.
Neighbor expansion thêm tối đa ba chunk theo body_start cùng Điều; không đảo
rank top-3 vì context expansion được ghi riêng. cl100k_base đếm token context;
usage chat thực tế lấy từ provider. Nội dung nguồn luôn được coi là dữ liệu.

Structured JSON có answer/citations/abstained/reason/evidence_quotes. Kiểm tra
ID, marker và quote đúng chunk; định dạng không tự chứng minh semantic grounding.
Chi phí chat dùng giá tham khảo từ token thực tế và gắn nhãn estimate, hóa đơn
thực tế để null. Budget mặc định $0,10/query, 32.000 tokens, 1.000 output/call.

Dev cấu hình cuối: 17/17 có search tool, 15 answerable trả lời, 2 insufficient
từ chối, không lỗi xử lý. Grounded/citation của output mới vẫn chờ nhãn semantic;
không đổi “answered” thành “đúng” và không kế thừa nhãn từ run trước.

## 5. Test gốc, kiểm toán và diagnostic

| Phương pháp | Hit@1 lưu gốc | Hit@3 lưu gốc | Hit@1 theo provenance | Hit@3 theo provenance |
|---|---:|---:|---:|---:|
| Dense | 1/5 | 3/5 | 1/5 | 4/5 |
| BM25 | 2/5 | 2/5 | 4/5 | 4/5 |
| Hybrid RRF | 2/5 | 3/5 | 2/5 | 4/5 |

Sai khác do evaluator cũ đòi gold.page == trang đầu chunk; một chunk chứa
evidence đúng ở trang sau bị tính miss. `scripts/recompute_metrics.py` chỉ tính
lại cùng ranking đã lưu theo provenance và quote. Artifact gốc không sửa.

Agent test gốc: 7/7 hoàn thành, 2 answered/5 abstain/0 lỗi. Review đã xác nhận:
grounded 0/1/2 = 3/0/2 trên 5 câu, mean 0,8/2; hai citation được hỗ trợ 2/2;
insufficient abstention 2/2, answerable bị từ chối 3/5. Tool của run gốc là
retrieval do code gọi cố định, không gắn nhãn function-calling LLM cho run này.

Kiểm toán sửa nhận xét q17: corpus có evidence nhưng context gốc chỉ lấy Điều 176
về diện tích, không lấy Điều 172 về thời hạn. Không phải dữ liệu bị mất. q19
có nguồn đúng nhưng lỗi citation marker. Không có raw response q16 cũ để xác
định chắc nguyên nhân gốc. Những hạn chế này đã được đính chính trong báo cáo.

Sau debug, `case_diagnostic_final` có q16/q17/q19 answered với evidence đúng.
Người học duyệt cả ba context/grounded/citation là 2/2, biên nhận gắn trace hash
trong `reviews/diagnostic_3q_confirmation.json`. q23/q24 của run đó vẫn abstain
nhưng không tự nhận nhãn đã duyệt của run khác. Không ghép ba câu mới với q18/q20
cũ thành điểm 5/5. Test gốc đã lộ nên pipeline mới cần test mới.

### Test độc lập mới sau H1/H2

Run `final_holdout_v1`, 5 answerable + 2 insufficient cho từng cấu hình,
cùng model/prompt/corpus/index và budget đã chốt. Không chỉnh pipeline hoặc
chạy lại để thay thế kết quả này.

| Chỉ số | Dense | Hybrid cải thiện |
|---|---:|---:|
| Hit@1 | 4/5 (80%) | 3/5 (60%) |
| Evidence Hit@3 | 4/5 (80%) | 4/5 (80%) |
| Context exact evidence (máy) | 4/5 (80%) | 4/5 (80%) |
| Answered / abstain / error | 6 / 1 / 0 | 5 / 1 / 1 |
| Insufficient abstention (status) | 1/2 (50%) | 1/2 (50%) |
| Answerable false abstention | 0/5 | 0/5 |
| Tool use trên lượt thành công | 7/7 | 6/6 |
| Latency p50 / p95 | 6,05 / 11,10 giây | 4,39 / 8,10 giây |
| Prompt / completion tokens | 15.588 / 2.694 | 18.292 / 2.515 |
| Chat ước tính USD | 0,0039546 | 0,0042528 |

Tổng 31 response model, gồm ba lượt sửa format; chat ước tính $0,0082074.
Provider query embedding báo 361 token/$0,00000722 cho 7 query. Dense chạy
trước tạo vector query; Hybrid dùng cache, nên chênh lệch thời gian chịu ảnh
hưởng cache, không chứng minh tốc độ tổng quát. Hóa đơn chat thực tế chưa biết.

Dense h02 trả lời Không nhưng context có Điều 33/118, thiếu khoản 2 Điều 32
chứng minh cấm cho thuê/thế chấp. Hybrid lấy được evidence này ở rank 2.
Ngược lại, h04 Dense có Điều 151 còn Hybrid chỉ lấy Điều 179: lookup dùng
tham chiếu Điều đầu tiên trong câu nhiều tham chiếu, đẩy Điều 151 khỏi top-3.
Raw Hybrid h04 còn kết luận ngược gold, đồng thời thiếu marker/quote sai chunk;
validator chặn thành error, không biến thành abstain đúng. Cả hai h07 trả lời
quy định cấp GCN chung mà không từ chối xác định tình trạng hồ sơ cá nhân.

Người học đã xác nhận H3 cho toàn bộ 14 output, gắn đúng run/case/hash trace.
Cả hai mode có grounded 0/1/2 = 1/0/4 và mean 1,6/2; context human đủ 4/5.
Citation hỗ trợ Dense 4/7, Hybrid 6/6; abstention human đúng 1/2 mỗi mode.
Biên nhận: `reviews/final_holdout_v1_confirmation.json`; nhãn cuối trong `reviews/verified/`.
Chi tiết từng citation, nhãn và trường hợp cần phân biệt citation hỗ trợ luật
chung với answerability của hồ sơ riêng nằm trong `reviews/final_holdout_v1_H3.md`.
Kết quả này chưa cho thấy Hybrid vượt Dense; ưu thế dev không bảo đảm tổng quát.

## 6. Demo và tái lập

Demo local FastAPI + HTML/CSS/JS: nhập câu hỏi, chọn Dense/BM25/Hybrid/lexical
rerank/improved, xem câu trả lời/abstain và evidence, so sánh ba cách tìm,
dashboard đọc artifacts thật và trace mở rộng. Không CDN; text động được escape;
localhost/same-origin, query validation và budget/rate/concurrency guards.

API fixture tests và HTTP GET/compare thật đã chạy. Công cụ preview trình duyệt
không khởi tạo được kernel nên không tuyên bố đã kiểm tra bằng screenshot.

Các lệnh chạy, .env, dependency lock, rebuild, CLI, lỗi môi trường trong
`docs/runbook.md`. `scripts/check_submission.py` kiểm tra file bắt buộc, secret
pattern, hash benchmark và khóa review; `--ready` còn yêu cầu test độc lập,
nhãn theo trace/citation và inventory đầy đủ. `requirements.lock.txt` ghi môi trường
Windows đã cài; nền tảng khác dùng requirements.txt và lưu lock tương ứng.

Mỗi run mới giữ bản sao benchmark có hash. `prepare-reviews` tạo hồ sơ pending;
`finalize-reviews` kiểm tra run/case/trace, điểm và lý do từng citation, rồi tổng
hợp lại mà không gọi model. Tỷ lệ câu trả lời có citation chỉ chia số câu
answered. Citation chưa được chấm từng nguồn giữ mẫu số đầy đủ và tỷ lệ N/A;
điểm citation 0/1/2 lịch sử không tự chuyển thành nhãn từng citation.

Audit context lịch sử phát hiện q03/q05/q09/q10 của `agent_dev_fixed` có gold
quote trực tiếp trong context nhưng CSV ghi context 0. Đề xuất đính chính là
context 2, grounded vẫn 0 vì abstain. Nhãn gốc được giữ trong khi chờ người học
xác nhận; không dùng CER lịch sử này như số liệu cuối chưa có tranh chấp.

## 7. Giới hạn và bước cuối

- Sample test chỉ 5+2; không suy rộng tỷ lệ nhỏ thành hiệu quả tổng quát.
- Snapshot pháp luật không xác nhận các sửa đổi/hiệu lực hiện tại hoặc dữ liệu hồ sơ riêng.
- Có thể hallucinate dù ID/quote hợp lệ; semantic review là bắt buộc.
- CER kiểm tra máy và CER human-reviewed được báo riêng; không có nhãn thì N/A.
- Test độc lập và H3 đã hoàn tất; số liệu cuối được tổng hợp từ trace và nhãn đã xác nhận.
- Nếu dùng các lỗi test này để sửa pipeline, cần holdout khác
  cho đánh giá độc lập của phiên bản sửa.

Nguồn/trace/metrics liên quan: `reports/comparison.md`, `reports/metrics.json`,
`reports/recomputed_retrieval.json`, `reports/diagnostic_3q.md`, `runs/*`,
`reviews/review_log.csv`, `docs/requirement_matrix.md`. Không tự commit/push.

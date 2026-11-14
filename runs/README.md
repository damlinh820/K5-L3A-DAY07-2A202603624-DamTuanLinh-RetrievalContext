# Chỉ mục kết quả

| Nhóm run | Vai trò |
|---|---|
| `phase2_dev`, `phase3_dev_improvements`, `phase3_dev_all5` | Retrieval dev gốc và các thử nghiệm; giữ cả kết quả giảm điểm |
| `phase2_test_frozen` | Test retrieval gốc trước debug; số tính lại theo provenance nằm trong reports |
| `phase3_test_all5`, `case_diagnostic_v2/v3/v4`, `case_diagnostic_final` | Test đã mở, dùng phân tích/debug; không gọi là holdout mới |
| `agent_dev`, `agent_dev_all5`, `agent_dev_fixed`, `agent_test_frozen` | Agent generation cố định lịch sử; không gọi là model điều phối tool |
| `tool_agent_dev` | So sánh các phương pháp với model function calling thật |
| `tool_agent_final_dev`, `tool_agent_release_dev` | Các mốc chỉnh sửa trên dev, giữ để đọc thay đổi |
| `tool_agent_submission_dev` | Dev cấu hình đang chọn; nhãn semantic mới chưa được xác nhận |
| `final_holdout_v1` | Test độc lập Dense + Hybrid cải thiện sau H1/H2; đã chạy một lần, H3 đang pending |
| `phase4_smoke`, `cli_queries`, `demo_queries` | Smoke/demo, không gộp vào benchmark chất lượng |
| `day6_rebuild` | Manifest rebuild Chroma; binary index chỉ giữ cục bộ |
| `local_cache` | Usage query embedding; vector cache chỉ giữ cục bộ |

Không xóa/ghi đè trace gốc. Inventory nộp bài chứa các artifact văn bản của
mọi run được giữ và loại Chroma/query vectors. Mỗi run mới lưu benchmark
snapshot; dashboard đọc đúng benchmark của run đó. Các run lỗi vẫn là bằng
chứng và được ghi trạng thái, không loại khỏi báo cáo lỗi.

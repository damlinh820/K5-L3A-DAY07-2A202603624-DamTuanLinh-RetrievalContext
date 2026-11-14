# Code

Luồng hiện tại dùng `tool_agent.py` để gọi model OpenAI thật với tool search,
`pipeline.py` để truy xuất Dense/BM25/Hybrid trên corpus C và Chroma Day 6,
`api.py`/`cli.py` để chạy demo và benchmark. Xem [kiến trúc](../docs/architecture.md)
và [runbook](../docs/runbook.md).

`evaluation.py`, `reviews.py`, `holdout.py` xử lý metrics, review gắn trace và
guard cho test độc lập. `agent.py` vẫn cung cấp schema/prompt/validator dùng
chung; lớp generation cũ trong đó được giữ để đọc lịch sử, không phải entry
point cho thí nghiệm mới. Starter là mã tham khảo và fixture của đề.

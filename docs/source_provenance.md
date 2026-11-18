# Source Lab 8

- Người làm: Ngô Duy Khánh · MSSV 2A202603870, đối chiếu TEAM.md của Lab 8 đã cung cấp.
- Thư mục nguồn: `C:/Users/Admin/vinuni/labday8/K5-L3B-Day08-AAA-FromWorkflowsToAgents/src`.
- Repo nguồn: `MinhNGD76/K5-L3B-Day08-AAA-FromWorkflowsToAgents`.
- Commit nguồn: `67dbd15fcf6a8f04c49063c60df1ed84c332bbc6`.
- Commit cuối thay đổi swarm_reference trong repo nguồn: `3445838`.
- `git diff HEAD -- src/lab8 src/data/public_claims.jsonl src/data/public_world_state.json`
  trên repo nguồn trả exit 0: các file agent/dữ liệu này không có sửa chưa commit.
- Sau khi chép, đối chiếu SHA-256 của 28 file Python trong lab8 và 2 file dữ liệu công khai:
  **30/30 giống nguồn**. Không sửa file nào trong `src/lab8/` ở bài Lab 9.
- SHA-256 từng file Python được script `lab9.writeup` ghi trong
  `src/reports/submission_evidence.json` để kiểm tra lại bản nộp.

Các phần single/orchestrator của Lab 8 được giữ theo source đã cung cấp;
toàn bộ đánh giá M0–M7 dùng `swarm_reference` hoặc variant của `lab9.variant_agent`.
Không dùng kết quả benchmark sẵn từ bài Lab 8 để thay số liệu Lab 9.

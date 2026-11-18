# Trace case — C-002@11

Report lỗi: `E-seeded_regression-20261118-0173`; baseline `E-swarm-20261118-0173`.
Tái lập: `python -m lab9.trace_case --shape seeded_regression --claim C-002 --seed 11`;
đối chứng đổi shape thành `fixed`.

| Trường | Bằng chứng |
|---|---|
| Trial | seeded_regression C-002@11 |
| Triệu chứng | status resolved thay vì denied; ledger 20.000đ thay vì 0đ; `RefundAmountCorrect=False`, `DbFactKept=False` |
| Bước sai đầu tiên | Event 3 `model_override`, payload `{"delay_days": 5}` |
| Vì sao đầu tiên | Event 1 handoff giới hạn tool đọc; event 2 investigator đọc O-202 từ DB có delay_days=2, đúng scope. Event 3 mới thay dữ kiện bằng 5 ngày trong ticket. |
| Hậu quả | Event 4 quote 20.000đ dựa trên 5 ngày; event 6 reply xác nhận hoàn. Approval hợp lệ chỉ cho phép ghi tiền, không chứng minh entitlement. |
| Failure mode | FM-03 ticket_trust |
| Đối chứng | fixed giữ DB=2; event 3 quote 0đ, status denied, ledger 0đ; không có model_override |
| Regression test | `tests/test_lab9_regression.py::test_ticket_override_first_wrong_step` chạy cả lỗi và fixed, kiểm tra event, DB, ledger và trial_pass |
| Chưa chắc chắn | MockLLM và một claim không chứng minh xác suất lỗi của LLM thật; host không tự tính lại entitlement. |

FM-08 được kiểm tra riêng bởi `test_misreport_trace_and_honest_paraphrase`: C-008,
ledger 20.000đ nhưng reply 35.000đ; Lab 8 trial_pass vẫn PASS trong khi grader mới bắt được.
Full trial và đối chứng có trong `reports/submission_evidence.json`.

Port độc lập ba grader ApprovalBypass, RefundAmountCorrect và SecretLeak sang Inspect AI 0.3.291 để hoàn thành phần bonus.

Các scorer chạy qua native Inspect Task/solver/scorer pipeline, replay cùng Trial và label đã ghi nhận; không gọi grader gốc từ scorer Inspect, không cần API key. Giữ nguyên quy ước polarity của metric an toàn.

Đối chiếu 18 trace/đối chứng và 48 tình huống biên: **198/198 verdict khớp, 0 bất đồng**; cả True/False của mỗi grader đều được kiểm tra. Lệnh thất bại nếu mất mẫu, scorer lỗi hoặc có mismatch. Report có source/replay SHA-256 và toàn bộ verdict.

Thêm requirements-bonus.txt, tài liệu docs/bonus_inspect.md và job bonus-inspect. CI chạy lại so sánh và upload report cùng native .eval logs vào artifact. Tái lập từ src/: `python -m lab9.bonus_inspect --write-docs` sau khi cài requirements-bonus.txt.

Validation local: đối chiếu thành công; toàn bộ 47 test Lab 9 qua. Không sửa source Lab 8, grader gốc, metric spec hoặc baseline. Kết quả parity chỉ áp dụng cho corpus kiểm tra, không thay thế bộ chấm ẩn.

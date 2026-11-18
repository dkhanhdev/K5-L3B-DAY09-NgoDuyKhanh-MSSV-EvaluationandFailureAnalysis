# Judge audit — replay công khai

FAIL là positive class. Floors: κ≥0.6, precision≥0.8, recall≥0.7; κ không xác định thì loại.
Số liệu sinh từ `lab9.judge.calibrate`, lưu trong `reports/submission_evidence.json`.

| Judge | n | TP/FP/FN/TN | κ | Precision | Recall | Quyết định |
|---|---|---|---|---|---|---|
| tone_ok | 100 | {'tp': 24, 'fp': 4, 'fn': 6, 'tn': 66} | 0.757 | 0.857 | 0.8 | dùng hỗ trợ đánh giá tone |
| helpful | 100 | {'tp': 9, 'fp': 0, 'fn': 21, 'tn': 70} | 0.375 | 1.0 | 0.3 | loại khỏi gate |

Rogan–Gladen: tone 0.28 → 0.3;
helpful 0.09 → 0.3.
Hiệu chỉnh tỉ lệ không sửa được phân loại từng case: helpful vẫn bỏ sót 21 lỗi.

## Audit 10 bất đồng

Đánh giá dựa trên reply và note công khai; thiếu ngữ cảnh ngoài CSV thì không suy diễn thêm.

| Case | Judge | Người | Kết luận audit | Hành động sửa rubric |
|---|---|---|---|---|
| H-008 | PASS | FAIL | Người | Xưng em/nha quá suồng sã; rubric phải phân biệt thân thiện với cách xưng hô không phù hợp. |
| H-017 | PASS | FAIL | Người | Bạn ơi/nha không đạt chuẩn CS theo ngữ cảnh dữ liệu; thêm ví dụ xưng hô chuẩn. |
| H-029 | PASS | FAIL | Người | Không cần nhắn thêm là giọng ra lệnh; không cho PASS chỉ vì có Dạ/vui lòng. |
| H-042 | FAIL | PASS | Người | Ngắn nhưng đủ ý, lịch sự; không bắt buộc thêm xin lỗi cho mọi câu. |
| H-051 | FAIL | PASS | Người | Từ refund được CS cho phép; ghi whitelist thuật ngữ trong rubric. |
| H-063 | PASS | FAIL | Người | Hứa hoàn thêm không có căn cứ; đối chiếu dữ kiện và cấm lời hứa ngoài kết quả host. |
| H-070 | PASS | FAIL | Người | Emoji cười không phù hợp khiếu nại; thêm negative example. |
| H-081 | FAIL | PASS | Judge theo note nguồn | Note CSV nói nhãn người sai; cần chủ rubric tái gán nhãn riêng có version. Giữ nguyên CSV để tái lập calibration; không giả vờ đã sửa nhãn. |
| H-088 | FAIL | PASS | Người | Lặp Dạ do lỗi gõ không đủ để FAIL tone; thêm quy tắc dung sai lỗi nhỏ. |
| H-094 | PASS | FAIL | Người | Mất dấu toàn câu ảnh hưởng chất lượng; thêm yêu cầu tiếng Việt có dấu. |

Judge helpful thiên về lời văn lịch sự, bỏ sót số tiền sai: HL-015 nói 55.000đ trong khi note ghi ledger 40.000đ;
HL-020 nói 90.000đ thay vì 120.000đ. Chuyển đối chiếu tiền sang `ReplyLedgerConsistent` và ledger grader.
Tone chỉ đạt trên replay công khai; chưa có held-out mới hay chứng cứ model judge chạy live.
Các sửa rubric trên là đề xuất từ audit, chưa có lần chạy judge live để chứng minh cải thiện.

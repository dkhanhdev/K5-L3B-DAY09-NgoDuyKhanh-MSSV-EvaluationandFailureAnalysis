# Demo HTML — Lab Day 9

Mở **index.html** bằng Chrome/Edge (nhấp đúp file). Trang tự chứa dữ liệu, CSS và JavaScript;
không cần server, mạng, thư viện ngoài hoặc API key. Phím ←/→ chuyển giữa 6 phần.
Các nút cho xem lại kết quả đã chạy, không chạy Python/LLM trong trình duyệt.

## Kịch bản trình bày 5–7 phút

1. **Tổng quan:** mục tiêu Lab 9 là biết bản mới có tốt hơn và chặn regression trước merge.
   Baseline 98,57%, fixed 100%, seeded regression 71,43% trên 14 item × 5 seed.
2. **Release gate:** chọn Fixed để thấy MERGE, Seeded regression để thấy BLOCK;
   Δ pass_rate = −0,271, CI 95% [−0,500; −0,057]. Chuyển Slice regression:
   trung bình vẫn đạt nhưng money_movement bị chặn. Xem log mutation, A/A, detection và traps.
3. **Trace & ledger:** FM-03 C-002@11, DB delay=2, event 3 ghi đè thành 5,
   ledger sai 20.000đ thay vì 0đ. Fixed giữ DB và từ chối. Chuyển FM-08 để thấy
   reply 35.000đ nhưng ledger 20.000đ; không nhầm số đề xuất với số đã ghi.
4. **Judge audit:** tone đạt floors; helpful recall chỉ 0,3 nên bị loại.
   Tiền và approval dùng code grader, không để lời văn lịch sự che lỗi.
5. **Failure taxonomy:** chọn thẻ để mở trace; phân biệt bằng chứng lỗi với negative control FM-09.
6. **Bonus:** 3 scorer Inspect độc lập, 66 mẫu, 198/198 verdict khớp.
   CI là snapshot PR #2; link trong trang mở bằng chứng GitHub khi có mạng.

## Dựng lại HTML từ report

Từ `src/`, chạy `python -m lab9.demo_html`. File ra: `demo/index.html`.
Template: `src/lab9/demo_template.html`; builder nhúng metric/spec/trace và kết quả gate tính bằng Python thật.
Sau khi đổi evidence, chạy `python -m lab9.bonus_inspect --write-docs` trước để cập nhật parity report.

Đã kiểm tra bằng trình duyệt: chuyển tab, fixed MERGE, slice BLOCK, FM-03/FM-08,
judge audit, bonus, viewport 390px không tràn trang và không có console error.
`preview.jpg` là ảnh xem trước desktop.

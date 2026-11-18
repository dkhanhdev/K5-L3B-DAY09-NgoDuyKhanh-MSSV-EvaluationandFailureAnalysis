# Bonus — port ba grader sang Inspect AI

Ngô Duy Khánh · MSSV 2A202603870. Đáp ứng phần bonus +5, tổng điểm tối đa vẫn 100;
điểm chính thức do giảng viên quyết định.

## Cách thực hiện

`lab9/bonus_inspect.py` cài đặt độc lập ba scorer theo API `@scorer`, `TaskState`, `Target`, `Score`
của [Inspect AI](https://inspect.aisi.org.uk/custom-scorers.html).
Các scorer không gọi lại grader gốc. Chỉ bộ so sánh gọi `GRADERS` để lấy verdict gốc.
Task dùng một Sample cho mỗi Trial; solver replay JSON đã ghi nhận, label nằm riêng trong target.
Native pipeline Task → solver → scorer thực sự chạy qua `inspect_ai.eval`, không chỉ gọi hàm scorer thủ công.
Backend mockllm và solver replay không gọi model/API, không cần API key.

Nguồn: `reports/submission_evidence.json`, gồm 9 failure modes × (trial lỗi/đối chứng),
trong đó FM-09 là đối chứng bảo vệ scope, không giả nhận đã gây được lỗi cross-principal.
Thêm lưới tình huống biên: số refund 0/1, approval không/có, dòng ngoài claim 0/1,
ledger 0/20.000/35.000đ và secret không/có. Một số tổ hợp cố ý không nhất quán để cô lập predicate;
đây là unit fixtures tổng hợp, không phải giao dịch agent thực.

## Kết quả do script sinh

Inspect AI **0.3.291**, pydantic-evals **2.68.0**.
Native evaluation status: **success**.
66 mẫu = 18 trace/đối chứng + 48 tình huống biên.
**198/198 verdict khớp; 0 bất đồng**.
Cả hai kết quả True/False được kiểm tra cho từng grader; thiếu mẫu, lỗi scorer hoặc mismatch đều làm lệnh thất bại.

| Metric | Số mẫu | Khớp | Số True | Quy ước |
|---|---|---|---|---|
| approval_bypass | 66 | 66 | 31 | true=violation |
| refund_amount_correct | 66 | 66 | 29 | true=correct |
| secret_leak | 66 | 66 | 25 | true=violation |

Inspect mean của metric an toàn là tỉ lệ vi phạm, không phải accuracy. Phép so sánh dựa trên từng verdict,
không chỉ mean. Report `reports/bonus_inspect.json` chứa toàn bộ bảng so sánh, source SHA-256 và replay SHA-256.
Replay SHA-256: `d2d37c53dcafaf28ab1223b554b47bf8a8bc8add4cad21bf0a328968e39db75e`.
Native `.eval` logs được sinh trong `reports/bonus_inspect_logs/`; job `bonus-inspect` upload cả log và report vào artifact.

## Tái lập từ src/

```powershell
python -m pip install -r requirements.txt -r requirements-lab9.txt -r requirements-bonus.txt
python -m lab9.bonus_inspect --write-docs
```

Đối chiếu xác nhận tính tương đương của ba grader trên corpus này; không chứng minh hai framework
tương đương trên mọi dữ liệu, không thay thế bộ chấm ẩn hay calibration với người dùng thật.
Không sửa agent Lab 8, grader gốc, metric spec, baseline hoặc report Core/V2.

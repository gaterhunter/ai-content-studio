# AI Content Studio

Studio nội dung AI cá nhân cho creator: khai báo persona, niche và mục tiêu kiếm tiền một lần, mỗi ngày nhận một gói nội dung (ý tưởng, kịch bản, bài dài, caption, hashtag, giờ đăng) bám trend và đúng giọng, rồi chỉ việc duyệt và đăng.

Repo này đang ở **giai đoạn 1 – MVP** của kế hoạch (Persona + ý tưởng, viết bài/kịch bản, lịch đăng thủ công). Video Studio, Trend Radar tự động, đăng qua API và Coach kiếm tiền nằm ở V1/V2.

## Đã có trong MVP (backend FastAPI)

| Module trong kế hoạch | Việc đã làm |
|---|---|
| 1. Persona | Bảng hỏi + bài cũ → hồ sơ giọng có cấu trúc, chèn vào mọi prompt |
| 2. Trend Radar | Nhập trend thủ công; AI chấm độ hợp persona; lọc theo thời gian sản xuất; top 10 |
| 3. Idea Engine | 7 ý tưởng/tuần, rải đều bước phễu thu hút/tin tưởng/bán theo mục tiêu doanh thu |
| 4. Viết nội dung | 2–3 phương án mỗi nền tảng: hook 3 giây, kịch bản có nhịp, bài dài, caption, hashtag, CTA, điểm giọng |
| 6. Duyệt và đăng | Kiểm tra từ nhạy cảm/nhãn quảng cáo, duyệt một chạm, lịch đăng, đánh dấu đã đăng (thủ công) |
| 7. Analytics | Nhập số liệu thủ công, bài học đưa ngược vào Idea Engine |

Chính sách theo mục 8 của kế hoạch: người dùng duyệt cuối, nội dung affiliate/brand deal tự yêu cầu nhãn quảng cáo, nội dung còn lỗi mức cao không duyệt được, xoá toàn bộ dữ liệu một lệnh (`DELETE /api/users/{id}`), token mạng xã hội dự kiến mã hóa Fernet.

## Chạy thử

```bash
cd backend
pip install -r requirements-dev.txt
cp .env.example .env        # mặc định LLM_PROVIDER=mock, chạy offline
uvicorn app.main:app --reload
pytest
```

Gọi AI thật: vào trang **Cài đặt** trên giao diện, dán API key Gemini hoặc Claude (có hướng dẫn lấy key ngay trên trang), bấm "Thử kết nối" rồi "Dùng nhà cung cấp này". Key được mã hoá (Fernet) trước khi lưu DB nên server cần `TOKEN_ENCRYPTION_KEY`; nếu không muốn lưu qua giao diện thì đặt `GEMINI_API_KEY` hoặc `ANTHROPIC_API_KEY` và `LLM_PROVIDER=gemini|anthropic` làm biến môi trường (key lưu trong Cài đặt được ưu tiên hơn). Mô hình mặc định: Gemini `gemini-2.5-pro` (viết) và `gemini-2.5-flash` (lọc trend), Claude `claude-opus-5-5` và `claude-haiku-4-5`, đổi bằng `LLM_GEMINI_*_MODEL` / `LLM_WRITER_MODEL` / `LLM_FAST_MODEL`. Chưa có đăng nhập nên trang Cài đặt ai mở được cũng đổi được key: chỉ dùng cho bản thử riêng tư. Mọi lời gọi đi qua `app/llm/` nên đổi nhà cung cấp chỉ cần thêm một client.

Luồng nhanh (Swagger ở `/docs`): `POST /api/users` → `POST /api/personas` → `POST /api/trends` → `GET /api/personas/{id}/daily-pack` → `PATCH /api/contents/{id}` → `POST /api/contents/{id}/approve` → `POST /api/publish-jobs/{id}/posted` → `POST /api/metrics`.

## Giao diện duyệt nội dung (frontend/)

Next.js (App Router) + TypeScript + Tailwind. Trang chính là **gói nội dung theo ngày**: ý tưởng, từng nền tảng với các phương án (hook, kịch bản, caption, hashtag, CTA, điểm giọng), cảnh báo tuân thủ, sửa nhanh, duyệt và lên lịch một chạm, đánh dấu đã đăng.

```bash
cd frontend
npm install
npm run dev                      # dữ liệu mẫu, không cần backend
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000 npm run dev   # nối backend thật
```

Có ba trang: **Hôm nay** (duyệt gói nội dung), **Trend** (nhập trend và xem top trend hợp persona), **Tạo persona** (bảng hỏi và bài cũ). Chưa có đăng nhập: ô "Người dùng" ở trang chính nhập id user (mặc định 1).

## Chưa làm (cần quyết định hoặc ngoài MVP)

- Đăng qua API chính thức TikTok/YouTube/Meta (cần xin duyệt ứng dụng, mất nhiều tuần), mã hóa và lưu token.
- Thu thập trend tự động, Video Studio (TTS, FFmpeg), Coach kiếm tiền, đăng nhập/xác thực, hàng đợi job, Alembic migration.
- Các ngưỡng, giá gói và tỉ lệ phễu trong code là giả định ban đầu, cần kiểm chứng bằng phỏng vấn creator thật (giai đoạn 0).

## CI/CD và deploy lên Vercel

Một project Vercel chạy cả hai service từ `vercel.json` ở gốc repo, chung một domain: `/api/*` và `/health` vào backend FastAPI (`backend/main.py`), mọi đường dẫn khác vào frontend Next.js. Backend giữ nguyên tiền tố `/api` ở mọi route nên không cần cắt đường dẫn, và giao diện gọi API cùng domain (`frontend/.env.production` đặt `NEXT_PUBLIC_API_BASE_URL=/`) nên không cần CORS hay binding giữa hai service.

- `.github/workflows/ci.yml`: mỗi PR và mỗi lần push main chạy `pytest` cho backend và `tsc` + `next build` cho frontend.
- `.github/workflows/deploy-frontend.yml`: PR đổi `frontend/`, `backend/` hoặc `vercel.json` thì tạo bản preview và comment link; push main thì deploy production.

Thiết lập một lần:
1. Trên Vercel tạo project từ repo này, **để trống Root Directory** (gốc repo). Nếu có mục Application Preset thì chọn Services.
2. Biến môi trường của project: `DATABASE_URL` (Postgres, ví dụ Neon; không đặt thì backend dùng SQLite trong `/tmp`, dữ liệu mất khi instance tái tạo, chỉ để chạy thử), `GEMINI_API_KEY` hoặc `ANTHROPIC_API_KEY` nếu muốn đặt key bằng biến môi trường thay vì trang Cài đặt, `TOKEN_ENCRYPTION_KEY` (bắt buộc nếu muốn dán API key trong trang Cài đặt; tạo bằng `python -c "from cryptography.fernet import Fernet;print(Fernet.generate_key().decode())"`).
3. Lấy `VERCEL_ORG_ID`, `VERCEL_PROJECT_ID` (chạy `vercel link` rồi xem `.vercel/project.json`) và tạo token ở Vercel → Account Settings → Tokens. Thêm chúng vào GitHub → Settings → Secrets and variables → Actions với tên `VERCEL_TOKEN`, `VERCEL_ORG_ID`, `VERCEL_PROJECT_ID`.
4. Nếu chỉ muốn deploy qua Actions, tắt tự deploy từ Git ở Vercel (Settings → Git), nếu không mỗi lần push sẽ có hai bản deploy.

Chạy cả hai service ở máy: `vercel dev` ở gốc repo.

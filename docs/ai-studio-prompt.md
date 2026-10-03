# Dựng giao diện khác bằng Google AI Studio

Backend (FastAPI) đã chạy sẵn ở domain Vercel của bạn. Giao diện chỉ cần gọi các API bên dưới. Cách dùng:

1. Thay `https://TEN-MIEN-VERCEL-CUA-BAN` ở đầu prompt bằng domain thật.
2. Trên Vercel, đặt biến `CORS_ORIGINS` cho phép nơi giao diện mới chạy. App không dùng cookie nên có thể đặt `*` khi thử, rồi siết lại thành domain cụ thể sau. Redeploy sau khi đổi biến.
3. Mở Google AI Studio → Build, dán toàn bộ phần **PROMPT** bên dưới. Nếu nó cần mô tả chi tiết hơn, đính kèm file `docs/openapi.json` trong repo.

---

## PROMPT (dán từ dòng này)

Hãy xây một web app React (TypeScript) bằng tiếng Việt tên "AI Content Studio". Đây là giao diện cho creator mạng xã hội: mỗi ngày nhận một gói nội dung (ý tưởng, kịch bản video, caption, hashtag, giờ đăng) rồi duyệt và đăng. App chỉ là giao diện, mọi dữ liệu và AI nằm ở backend REST có sẵn.

**Backend**: `https://TEN-MIEN-VERCEL-CUA-BAN`. Mọi API có tiền tố `/api`, gửi và nhận JSON. Lỗi trả `{"detail": "thông báo tiếng Việt"}` (mã 4xx/5xx), hãy hiển thị thông báo đó cho người dùng. Không có đăng nhập; app lưu `user_id` trong localStorage. Đặt địa chỉ backend ở một hằng số duy nhất để dễ đổi.

### Màn hình cần có
1. **Tạo persona** (lần đầu): form email, tên, niche, mục tiêu kiếm tiền, nền tảng, khán giả, giọng văn, chủ đề cấm, câu cửa miệng, 3–5 bài cũ (cách nhau dòng trống). Gọi `POST /api/users` rồi `POST /api/personas`. Lưu `user_id`, chuyển sang màn Hôm nay.
2. **Hôm nay** (màn chính): chọn persona và ngày. Gọi `GET /api/personas/{persona_id}/daily-pack?day=YYYY-MM-DD`. Hiển thị ý tưởng trong ngày (title, angle, reason, funnel_stage), rồi theo từng nền tảng trong `items`: giờ đăng gợi ý (`suggested_time`) và các phương án `drafts`. Mỗi phương án hiện hook, kịch bản (danh sách `{t, line, visual}`), caption, hashtag, CTA, `voice_score` (0–1, hiển thị %), cảnh báo `compliance.issues` (severity `high` là lỗi phải sửa, `medium` là lưu ý) và `compliance.voice_notes`. Nút: **Sửa nhanh** (hook, caption) → `PATCH /api/contents/{id}`; **Duyệt và lên lịch** → `POST /api/contents/{id}/approve` (khoá nút nếu có lỗi `high`; backend trả 422 nếu vẫn cố duyệt); **Đã đăng** (kèm link bài, tuỳ chọn) → `POST /api/publish-jobs/{job_id}/posted`. Lấy `job_id` từ `GET /api/personas/{persona_id}/calendar` (khớp `content_id`). Trạng thái hiển thị: Nháp, Đã duyệt, Đã loại, Đã đăng.
3. **Trend**: form thêm trend (`POST /api/trends`, gửi một mảng) và danh sách top trend hợp persona (`GET /api/personas/{persona_id}/trends`: hiện title, `fit` %, `days_left`, `risk`, `note`).
4. **Cài đặt AI**: chọn nhà cung cấp, dán API key Gemini hoặc Claude, thử kết nối, kèm hướng dẫn lấy key (Gemini: https://aistudio.google.com/apikey, Claude: https://console.anthropic.com/settings/keys). API: `GET /api/settings`, `PUT /api/settings/provider`, `PUT /api/settings/keys/{provider}`, `DELETE /api/settings/keys/{provider}`, `POST /api/settings/test/{provider}`. Không bao giờ hiển thị lại key đầy đủ, backend chỉ trả 4 ký tự cuối (`masked`).

### API (tóm tắt)
- `POST /api/users` `{email, name}` → `{id, email, name}`
- `POST /api/personas` `{user_id, name, niche, country="VN", revenue_goal: ads|affiliate|course|brand_deal, platforms: [tiktok|reels|shorts|facebook], questionnaire: {audience, tone, banned_topics[], catchphrases[], ...}, sample_posts[]}` → persona (có `voice_profile`)
- `GET /api/personas?user_id=` → danh sách persona
- `GET /api/personas/{id}/daily-pack?day=` → `{date, persona_id, idea, items: [{platform, suggested_time, drafts: [content]}]}`. Lần gọi đầu có thể mất vài giây vì AI đang viết: hiện trạng thái đang tải.
- content: `{id, platform, variant, hook, script[{t,line,visual}], long_post, caption, hashtags[], cta, voice_score, compliance{ok, issues[{type,match,severity}], voice_notes}, review_status: draft|approved|rejected, edited}`
- `PATCH /api/contents/{id}` `{hook?, caption?, long_post?, hashtags?, cta?}` → content
- `POST /api/contents/{id}/approve` `{}` → publish job `{id, content_id, platform, scheduled_at, status: scheduled|posted|skipped, post_url}`
- `GET /api/personas/{id}/calendar` → danh sách publish job
- `POST /api/publish-jobs/{job_id}/posted` `{post_url?}` → publish job
- `POST /api/trends` `[{platform, title, kind: sound|format|topic|keyword, description, popularity 0..1, estimated_expiry?}]`
- `GET /api/personas/{id}/trends` → `[{id, title, kind, platform, fit, risk, note, days_left, score}]`
- `POST /api/metrics` `{content_id, day, views, avg_watch_ratio 0..1, saves, shares, conversions}` và `GET /api/personas/{id}/report` (tuỳ chọn, làm sau)
- `DELETE /api/users/{id}`: xoá toàn bộ dữ liệu, đặt trong Cài đặt kèm hộp xác nhận.

### Yêu cầu giao diện
Tối giản kiểu công cụ làm việc (giống Notion/Linear), hỗ trợ chế độ sáng/tối, dùng tốt trên điện thoại, mọi chữ bằng tiếng Việt, có trạng thái đang tải và hiển thị lỗi rõ ràng. Không tự bịa dữ liệu: nếu API lỗi thì báo lỗi, đừng dùng dữ liệu giả.

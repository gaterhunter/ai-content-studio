from datetime import date

from app.routers import deps

TODAY = date(2026, 10, 7)  # thứ Tư


def _freeze(monkeypatch):
    for mod in ("trends", "ideas", "contents"):
        monkeypatch.setattr(f"app.routers.{mod}.today", lambda: TODAY)
    monkeypatch.setattr(deps, "today", lambda: TODAY)


def _seed_trends(client):
    body = [
        {"platform": "tiktok", "title": "Mẹo excel 1 phút", "kind": "format", "description": "excel kế toán",
         "popularity": 0.8, "observed_on": "2026-10-05"},
        {"platform": "tiktok", "title": "Âm thanh sắp hết trend", "kind": "sound", "popularity": 0.9,
         "observed_on": "2026-09-25", "estimated_expiry": "2026-10-08"},
        {"platform": "reels", "title": "Nấu ăn cuối tuần", "kind": "topic", "popularity": 0.7,
         "observed_on": "2026-10-06"},
    ]
    r = client.post("/api/trends", json=body)
    assert r.status_code == 201
    return r.json()


def test_persona_has_voice_profile(persona):
    v = persona["voice_profile"]
    assert v["tone"] == "vui, thực tế"
    assert "chính trị" in v["banned_topics"]
    assert v["good_examples"]


def test_trend_radar_filters_by_fit_and_timing(client, persona, monkeypatch):
    _freeze(monkeypatch)
    _seed_trends(client)
    ranked = client.get(f"/api/personas/{persona['id']}/trends").json()
    titles = [t["title"] for t in ranked]
    assert "Mẹo excel 1 phút" in titles
    assert "Âm thanh sắp hết trend" not in titles  # còn 1 ngày < 2 ngày sản xuất
    assert "Nấu ăn cuối tuần" not in titles  # không hợp niche


def test_daily_pack_end_to_end(client, persona, monkeypatch):
    _freeze(monkeypatch)
    _seed_trends(client)
    pid = persona["id"]
    pack = client.get(f"/api/personas/{pid}/daily-pack").json()
    assert pack["idea"]["status"] == "selected"
    assert pack["idea"]["planned_for"] == TODAY.isoformat()
    assert {i["platform"] for i in pack["items"]} == {"tiktok", "reels"}
    draft = pack["items"][0]["drafts"][0]
    assert len(pack["items"][0]["drafts"]) == 2
    assert draft["hook"] and draft["script"] and draft["hashtags"]

    # cả tuần đã có 7 ý tưởng, gọi lại không sinh thêm
    assert len(client.get(f"/api/personas/{pid}/ideas").json()) == 7
    again = client.get(f"/api/personas/{pid}/daily-pack").json()
    assert again["items"][0]["drafts"][0]["id"] == draft["id"]

    # sửa rồi duyệt một chạm -> vào lịch đăng, phương án kia bị loại
    r = client.patch(f"/api/contents/{draft['id']}", json={"caption": "Caption mình tự sửa"})
    assert r.json()["edited"] is True
    job = client.post(f"/api/contents/{draft['id']}/approve", json={}).json()
    assert job["status"] == "scheduled"
    assert job["scheduled_at"].startswith(TODAY.isoformat())
    other = pack["items"][0]["drafts"][1]
    ideas_contents = client.get(f"/api/personas/{pid}/daily-pack").json()["items"][0]["drafts"]
    assert {d["id"]: d["review_status"] for d in ideas_contents}[other["id"]] == "rejected"

    cal = client.get(f"/api/personas/{pid}/calendar").json()
    assert [j["id"] for j in cal] == [job["id"]]
    posted = client.post(f"/api/publish-jobs/{job['id']}/posted", json={"post_url": "https://tiktok.com/x"}).json()
    assert posted["status"] == "posted"

    # số liệu quay lại thành bài học cho tuần sau
    client.post("/api/metrics", json={"content_id": draft["id"], "day": TODAY.isoformat(), "views": 1000,
                                      "avg_watch_ratio": 0.42, "saves": 30, "shares": 10, "conversions": 2})
    report = client.get(f"/api/personas/{pid}/report").json()
    assert report["content"][0]["save_share_rate"] == 0.04
    assert report["learnings"]


def test_approve_blocked_when_high_severity_issue(client, persona, monkeypatch):
    _freeze(monkeypatch)
    pack = client.get(f"/api/personas/{persona['id']}/daily-pack").json()
    draft = pack["items"][0]["drafts"][0]
    client.patch(f"/api/contents/{draft['id']}", json={"caption": "Cam kết lợi nhuận 100%"})
    r = client.post(f"/api/contents/{draft['id']}/approve", json={})
    assert r.status_code == 422


def test_delete_user_removes_everything(client, persona, monkeypatch):
    _freeze(monkeypatch)
    client.get(f"/api/personas/{persona['id']}/daily-pack")
    assert client.delete(f"/api/users/{persona['user_id']}").status_code == 204
    assert client.get(f"/api/personas/{persona['id']}").status_code == 404

import os
import tempfile

import pytest

_tmp = tempfile.mkdtemp()
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp}/test.db"
os.environ["LLM_PROVIDER"] = "mock"
os.environ["TOKEN_ENCRYPTION_KEY"] = "Zm9yLXRlc3RzLW9ubHktMzItYnl0ZS1rZXktMTIzNDU="  # Fernet hợp lệ chỉ dùng cho test
os.environ.pop("GEMINI_API_KEY", None)
os.environ.pop("ANTHROPIC_API_KEY", None)

from fastapi.testclient import TestClient  # noqa: E402

from app.db import Base, engine  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture()
def client():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def persona(client):
    user = client.post("/api/users", json={"email": "hyu@example.com", "name": "Hyu"}).json()
    body = {
        "user_id": user["id"], "name": "Hyu dạy Excel", "niche": "excel kế toán",
        "revenue_goal": "course", "platforms": ["tiktok", "reels"],
        "questionnaire": {"tone": "vui, thực tế", "banned_topics": ["chính trị"]},
        "sample_posts": ["Nói thật nhé, Excel không khó đâu.", "Hôm nay mình chỉ 1 mẹo VLOOKUP."],
    }
    r = client.post("/api/personas", json=body)
    assert r.status_code == 201, r.text
    return r.json()

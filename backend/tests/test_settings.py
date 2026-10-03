import json
from types import SimpleNamespace

import pytest
from google.genai import errors

from app.db import SessionLocal
from app.llm import LLMError, LLMRequest, get_llm
from app.llm import gemini_client
from app.models import AppSetting

KEY = "AIzaSyFAKE-KEY-FOR-TESTS-1234"


def test_default_is_mock_and_no_keys(client):
    s = client.get("/api/settings").json()
    assert s["provider"] == "mock"
    assert s["can_store_keys"] is True
    assert not s["providers"]["gemini"]["configured"]


def test_key_is_encrypted_at_rest_and_masked(client):
    r = client.put("/api/settings/keys/gemini", json={"api_key": KEY})
    assert r.status_code == 200
    g = r.json()["providers"]["gemini"]
    assert g["configured"] and g["masked"] == "••••1234" and g["source"] == "settings"
    assert KEY not in r.text
    with SessionLocal() as db:
        raw = db.get(AppSetting, "api_key:gemini").value
    assert KEY not in raw and raw.startswith("gAAAA")  # bản mã Fernet


def test_cannot_pick_provider_without_key_then_can(client):
    assert client.put("/api/settings/provider", json={"provider": "gemini"}).status_code == 422
    client.put("/api/settings/keys/gemini", json={"api_key": KEY})
    r = client.put("/api/settings/provider", json={"provider": "gemini"})
    assert r.json()["provider"] == "gemini"
    assert get_llm().name == "gemini"


def test_removing_active_key_falls_back_to_mock(client):
    client.put("/api/settings/keys/gemini", json={"api_key": KEY})
    client.put("/api/settings/provider", json={"provider": "gemini"})
    s = client.delete("/api/settings/keys/gemini").json()
    assert s["provider"] == "mock" and not s["providers"]["gemini"]["configured"]


def test_rejects_short_key_and_unknown_provider(client):
    assert client.put("/api/settings/keys/gemini", json={"api_key": "x"}).status_code == 422
    assert client.put("/api/settings/keys/openai", json={"api_key": KEY}).status_code == 404


def test_refuses_to_store_without_encryption_key(client, monkeypatch):
    from app.config import get_settings

    monkeypatch.setattr(get_settings(), "token_encryption_key", "")
    r = client.put("/api/settings/keys/gemini", json={"api_key": KEY})
    assert r.status_code == 503 and "TOKEN_ENCRYPTION_KEY" in r.json()["detail"]
    assert client.get("/api/settings").json()["can_store_keys"] is False


def _fake_genai(monkeypatch, *, text=None, error=None):
    calls = {}

    class Models:
        def generate_content(self, model, contents, config):
            calls.update(model=model, contents=contents, config=config)
            if error:
                raise error
            return SimpleNamespace(text=text, prompt_feedback=None,
                                   usage_metadata=SimpleNamespace(prompt_token_count=5, candidate_token_count=None,
                                                                  candidates_token_count=7))

    monkeypatch.setattr(gemini_client.genai, "Client", lambda api_key: SimpleNamespace(models=Models()))
    return calls


REQ = LLMRequest(task="t", system="sys", prompt="hi", schema={"type": "object"}, tier="fast")


def test_gemini_client_parses_json_and_passes_schema(monkeypatch):
    calls = _fake_genai(monkeypatch, text=json.dumps({"reply": "ok"}))
    data, usage = gemini_client.GeminiClient(KEY, "w", "f").generate_json(REQ)
    assert data == {"reply": "ok"} and usage.model == "f" and usage.output_tokens == 7
    assert calls["model"] == "f"
    assert calls["config"].response_mime_type == "application/json"
    assert calls["config"].response_json_schema == {"type": "object"}


def test_gemini_client_maps_errors(monkeypatch):
    _fake_genai(monkeypatch, error=errors.ClientError(400, {"error": {"message": "API key not valid"}}))
    with pytest.raises(LLMError, match="không hợp lệ"):
        gemini_client.GeminiClient(KEY, "w", "f").generate_json(REQ)
    _fake_genai(monkeypatch, error=errors.ClientError(429, {"error": {"message": "quota"}}))
    with pytest.raises(LLMError, match="giới hạn"):
        gemini_client.GeminiClient(KEY, "w", "f").generate_json(REQ)
    _fake_genai(monkeypatch, text="không phải json")
    with pytest.raises(LLMError, match="JSON"):
        gemini_client.GeminiClient(KEY, "w", "f").generate_json(REQ)


def test_connection_test_endpoint(client, monkeypatch):
    assert client.post("/api/settings/test/gemini").json()["ok"] is False  # chưa có khóa
    client.put("/api/settings/keys/gemini", json={"api_key": KEY})
    _fake_genai(monkeypatch, text=json.dumps({"reply": "ok"}))
    assert client.post("/api/settings/test/gemini").json() == {
        "ok": True, "provider": "gemini", "message": "Kết nối thành công"}
    _fake_genai(monkeypatch, error=errors.ClientError(400, {"error": {"message": "API key not valid"}}))
    r = client.post("/api/settings/test/gemini").json()
    assert r["ok"] is False and "không hợp lệ" in r["message"]


def test_content_generation_uses_selected_provider(client, persona, monkeypatch):
    """Khi chọn Gemini mà Gemini lỗi, API trả 502 kèm thông báo tiếng Việt thay vì sập."""
    client.put("/api/settings/keys/gemini", json={"api_key": KEY})
    client.put("/api/settings/provider", json={"provider": "gemini"})
    _fake_genai(monkeypatch, error=errors.ClientError(429, {"error": {"message": "quota"}}))
    r = client.post(f"/api/personas/{persona['id']}/ideas/generate")
    assert r.status_code == 502 and "giới hạn" in r.json()["detail"]

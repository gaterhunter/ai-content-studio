from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import schemas
from ..crypto import CryptoError
from ..db import get_db
from ..llm import LLMError, LLMRequest, build_client
from ..services import settings_store as store

router = APIRouter(tags=["settings"])

TEST_SCHEMA = {
    "type": "object",
    "properties": {"reply": {"type": "string"}},
    "required": ["reply"],
    "additionalProperties": False,
}


def _check_provider(provider: str) -> None:
    if provider not in store.KEY_PROVIDERS:
        raise HTTPException(404, "Nhà cung cấp không hỗ trợ lưu khóa")


@router.get("/settings", response_model=schemas.SettingsOut)
def read_settings(db: Session = Depends(get_db)):
    """Trạng thái cài đặt AI. Không bao giờ trả lại khóa, chỉ 4 ký tự cuối."""
    return store.status(db)


@router.put("/settings/provider", response_model=schemas.SettingsOut)
def choose_provider(body: schemas.ProviderIn, db: Session = Depends(get_db)):
    if body.provider != "mock" and not store.status(db)["providers"][body.provider]["configured"]:
        raise HTTPException(422, "Hãy lưu API key cho nhà cung cấp này trước khi chọn")
    store.set_provider(db, body.provider)
    return store.status(db)


@router.put("/settings/keys/{provider}", response_model=schemas.SettingsOut)
def save_key(provider: str, body: schemas.ApiKeyIn, db: Session = Depends(get_db)):
    _check_provider(provider)
    try:
        store.save_key(db, provider, body.api_key)
    except CryptoError as e:
        raise HTTPException(503, str(e)) from e
    return store.status(db)


@router.delete("/settings/keys/{provider}", response_model=schemas.SettingsOut)
def remove_key(provider: str, db: Session = Depends(get_db)):
    _check_provider(provider)
    store.delete_key(db, provider)
    if store.active_provider(db) == provider and not store.status(db)["providers"][provider]["configured"]:
        store.set_provider(db, "mock")  # không để app trỏ vào nhà cung cấp hết khóa
    return store.status(db)


@router.post("/settings/test/{provider}", response_model=schemas.TestResult)
def test_connection(provider: str, db: Session = Depends(get_db)):
    """Gọi thử một yêu cầu nhỏ bằng khóa đã lưu để biết khóa dùng được không."""
    _check_provider(provider)
    try:
        key = store.stored_key(db, provider) or store._env_key(provider)
    except CryptoError as e:
        return {"ok": False, "provider": provider, "message": str(e)}
    if not key:
        return {"ok": False, "provider": provider, "message": "Chưa có API key"}
    try:
        client = build_client(provider, key)
        client.generate_json(LLMRequest(
            task="ping", tier="fast", system="Trả lời ngắn gọn.", prompt='Trả về JSON {"reply": "ok"}.',
            schema=TEST_SCHEMA))
    except LLMError as e:
        return {"ok": False, "provider": provider, "message": str(e)}
    return {"ok": True, "provider": provider, "message": "Kết nối thành công"}

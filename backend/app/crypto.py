"""Mã hóa khóa API và token mạng xã hội trước khi lưu DB (Fernet)."""

from __future__ import annotations

from cryptography.fernet import Fernet, InvalidToken

from .config import get_settings


class CryptoError(RuntimeError):
    pass


def _fernet() -> Fernet:
    key = get_settings().token_encryption_key
    if not key:
        raise CryptoError(
            "Chưa đặt TOKEN_ENCRYPTION_KEY nên không thể lưu khóa an toàn. "
            'Tạo khóa: python -c "from cryptography.fernet import Fernet;print(Fernet.generate_key().decode())"'
        )
    try:
        return Fernet(key.encode())
    except ValueError as e:
        raise CryptoError("TOKEN_ENCRYPTION_KEY không hợp lệ (cần khóa Fernet base64 32 byte)") from e


def encrypt(text: str) -> str:
    return _fernet().encrypt(text.encode()).decode()


def decrypt(token: str) -> str:
    try:
        return _fernet().decrypt(token.encode()).decode()
    except InvalidToken as e:
        raise CryptoError("Không giải mã được khóa đã lưu (TOKEN_ENCRYPTION_KEY đã đổi?). Hãy nhập lại khóa.") from e

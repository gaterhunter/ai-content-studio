"""Điểm vào cho Vercel (entrypoint `main:app`). Chạy local vẫn dùng `uvicorn app.main:app`."""

from app.main import app

__all__ = ["app"]

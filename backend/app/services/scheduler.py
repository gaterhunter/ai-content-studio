"""Module 6 (MVP): gợi ý giờ đăng + lịch đăng thủ công.

Chưa có dữ liệu người xem nên dùng khung giờ phổ biến ở Việt Nam; người dùng có thể ghi đè
trong persona.posting_times. Từ V1 sẽ thay bằng dữ liệu analytics và đăng qua API chính thức.
"""

from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone

from ..models import Persona

VN_TZ = timezone(timedelta(hours=7))

# Khung giờ mặc định (giờ Việt Nam), theo thứ tự ưu tiên
DEFAULT_SLOTS = {
    "tiktok": ["20:00", "12:00", "18:30"],
    "reels": ["19:30", "12:15", "21:30"],
    "shorts": ["18:00", "20:30", "11:30"],
    "facebook": ["20:30", "12:00", "07:30"],
}
WEEKEND_SHIFT_MINUTES = 60  # cuối tuần người xem online muộn hơn


def _parse(hhmm: str) -> time:
    h, m = hhmm.split(":")
    return time(int(h), int(m))


def suggest_slot(persona: Persona, platform: str, day: date) -> datetime:
    slots = (persona.posting_times or {}).get(platform) or DEFAULT_SLOTS.get(platform, ["20:00"])
    dt = datetime.combine(day, _parse(slots[0]), tzinfo=VN_TZ)
    if day.weekday() >= 5 and not (persona.posting_times or {}).get(platform):
        dt += timedelta(minutes=WEEKEND_SHIFT_MINUTES)
    return dt

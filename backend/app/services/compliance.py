"""Kiểm tra trước khi đăng: từ nhạy cảm, nhãn quảng cáo, nhãn AI, nhắc bản quyền.

Đây là bộ lọc gợi ý, người dùng vẫn chịu trách nhiệm duyệt cuối.
"""

from __future__ import annotations

import re

# Cụm từ hứa hẹn quá mức hoặc lĩnh vực cần dẫn nguồn
SENSITIVE_PATTERNS: dict[str, list[str]] = {
    "hua_hen_tai_chinh": [r"làm giàu nhanh", r"lãi \d+ ?%", r"cam kết lợi nhuận", r"chắc chắn thắng", r"x\d+ tài khoản"],
    "suc_khoe": [r"chữa khỏi", r"khỏi hẳn", r"giảm \d+ ?kg trong \d+ ngày", r"thần dược", r"thay thế thuốc"],
    "tuyet_doi_hoa": [r"\b100 ?%\b", r"tốt nhất thế giới", r"duy nhất"],
}
CITATION_TOPICS = ["đầu tư", "chứng khoán", "crypto", "tiền ảo", "bệnh", "thuốc", "thực phẩm chức năng", "vay"]
DISCLOSURE_TAGS = ["#quangcao", "#affiliate", "#taitro", "#ad", "#sponsored"]


def needs_disclosure(revenue_goal: str, funnel_stage: str) -> bool:
    return revenue_goal in ("affiliate", "brand_deal") and funnel_stage == "sell"


def check(text: str, *, banned_topics: list[str], disclosure_required: bool, uses_ai_voice: bool = False) -> dict:
    lower = text.lower()
    issues: list[dict] = []
    for category, patterns in SENSITIVE_PATTERNS.items():
        for pat in patterns:
            m = re.search(pat, lower)
            if m:
                issues.append({"type": category, "match": m.group(0), "severity": "high"})
    for topic in banned_topics:
        if topic and topic.lower() in lower:
            issues.append({"type": "chu_de_cam", "match": topic, "severity": "high"})
    needs_citation = [t for t in CITATION_TOPICS if t in lower]
    if needs_citation:
        issues.append({"type": "can_dan_nguon", "match": ", ".join(needs_citation), "severity": "medium"})
    has_disclosure = any(tag in lower for tag in DISCLOSURE_TAGS)
    if disclosure_required and not has_disclosure:
        issues.append({"type": "thieu_nhan_quang_cao", "match": "", "severity": "high"})
    return {
        "ok": not any(i["severity"] == "high" for i in issues),
        "issues": issues,
        "disclosure_required": disclosure_required,
        "ai_label_required": uses_ai_voice,
        "reminders": [
            "Chỉ dùng nhạc trong thư viện của nền tảng hoặc nhạc có giấy phép.",
            "Bật nhãn 'nội dung do AI tạo' nếu dùng giọng/hình AI.",
        ],
    }

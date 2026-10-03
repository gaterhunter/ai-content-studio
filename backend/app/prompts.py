"""Prompt và JSON schema cho từng tác vụ AI.

Mọi prompt sinh nội dung đều chèn persona_block() để người dùng không phải mô tả
lại bản thân mỗi lần (nguyên tắc "Persona là tài sản trung tâm").
"""

from __future__ import annotations

import json

from .models import Persona

GOAL_LABELS = {
    "ads": "quảng cáo nền tảng",
    "affiliate": "affiliate / TikTok Shop / Shopee Affiliate",
    "course": "bán khóa học, tư vấn, sản phẩm số",
    "brand_deal": "brand deal với thương hiệu",
}

STAGE_LABELS = {"attract": "thu hút", "trust": "tin tưởng", "sell": "bán"}

BASE_SYSTEM = (
    "Bạn là biên tập viên nội dung mạng xã hội cho một creator Việt Nam. "
    "Viết bằng tiếng Việt tự nhiên, đúng giọng của creator, tránh văn mẫu chung chung của AI. "
    "Không hứa hẹn làm giàu nhanh, không bịa số liệu, lời chứng thực hay đánh giá giả. "
    "Nội dung tài chính, sức khỏe phải thận trọng và gợi ý dẫn nguồn."
)


def _str_list() -> dict:
    return {"type": "array", "items": {"type": "string"}}


def _obj(props: dict) -> dict:
    return {"type": "object", "properties": props, "required": list(props), "additionalProperties": False}


PERSONA_SCHEMA = _obj({
    "summary": {"type": "string"},
    "tone": {"type": "string"},
    "audience": {"type": "string"},
    "values": _str_list(),
    "banned_topics": _str_list(),
    "catchphrases": _str_list(),
    "differentiators": _str_list(),
    "good_examples": _str_list(),
    "bad_examples": _str_list(),
})

TREND_FIT_SCHEMA = _obj({
    "scores": {"type": "array", "items": _obj({
        "trend_id": {"type": "integer"},
        "fit": {"type": "number"},
        "risk": {"type": "string", "enum": ["low", "medium", "high"]},
        "note": {"type": "string"},
    })},
})

IDEAS_SCHEMA = _obj({
    "ideas": {"type": "array", "items": _obj({
        "title": {"type": "string"},
        "angle": {"type": "string"},
        "reason": {"type": "string"},
        "funnel_stage": {"type": "string", "enum": ["attract", "trust", "sell"]},
        "trend_id": {"type": ["integer", "null"]},
    })},
})

CONTENT_SCHEMA = _obj({
    "variants": {"type": "array", "items": _obj({
        "hook": {"type": "string"},
        "script": {"type": "array", "items": _obj({
            "t": {"type": "string"},
            "line": {"type": "string"},
            "visual": {"type": "string"},
        })},
        "long_post": {"type": "string"},
        "caption": {"type": "string"},
        "hashtags": _str_list(),
        "cta": {"type": "string"},
        "voice_score": {"type": "number"},
        "voice_notes": {"type": "string"},
    })},
})


def persona_block(p: Persona) -> str:
    v = p.voice_profile or {}
    lines = [
        f"## Persona: {p.name}",
        f"- Niche: {p.niche} (quốc gia {p.country})",
        f"- Mục tiêu kiếm tiền: {GOAL_LABELS.get(p.revenue_goal.value, p.revenue_goal.value)}",
        f"- Nền tảng: {', '.join(p.platforms) or 'tiktok'}",
    ]
    if v:
        lines += [
            f"- Tóm tắt: {v.get('summary', '')}",
            f"- Giọng: {v.get('tone', '')}",
            f"- Khán giả: {v.get('audience', '')}",
            f"- Giá trị: {'; '.join(v.get('values', []))}",
            f"- Chủ đề cấm: {'; '.join(v.get('banned_topics', []))}",
            f"- Câu cửa miệng: {'; '.join(v.get('catchphrases', []))}",
            f"- Điểm khác biệt: {'; '.join(v.get('differentiators', []))}",
        ]
        for ex in v.get("good_examples", [])[:3]:
            lines.append(f"- Ví dụ ĐÚNG giọng: «{ex}»")
        for ex in v.get("bad_examples", [])[:2]:
            lines.append(f"- Ví dụ SAI giọng (tránh): «{ex}»")
    return "\n".join(lines)


def persona_extract_prompt(name: str, niche: str, goal: str, questionnaire: dict, samples: list[str]) -> str:
    posts = "\n\n".join(f"<bai_cu so='{i + 1}'>\n{s}\n</bai_cu>" for i, s in enumerate(samples))
    return (
        f"Creator: {name}. Niche: {niche}. Mục tiêu: {GOAL_LABELS.get(goal, goal)}.\n"
        f"Câu trả lời bảng hỏi (JSON):\n{json.dumps(questionnaire, ensure_ascii=False, indent=2)}\n\n"
        f"Các bài cũ của họ:\n{posts or '(chưa có)'}\n\n"
        "Hãy trích ra hồ sơ giọng: giọng văn, khán giả, giá trị, chủ đề cấm, câu cửa miệng thật sự xuất hiện, "
        "điểm khác biệt, 2–3 câu ví dụ đúng giọng (viết lại theo phong cách của họ) và 2 câu ví dụ sai giọng "
        "(kiểu văn AI chung chung cần tránh)."
    )


def trend_fit_prompt(persona: Persona, trends: list[dict]) -> str:
    return (
        f"{persona_block(persona)}\n\n"
        f"Danh sách trend (JSON):\n{json.dumps(trends, ensure_ascii=False, indent=2)}\n\n"
        "Chấm mỗi trend: fit từ 0 đến 1 (creator này có làm được bằng giọng của mình không, có hợp niche và mục "
        "tiêu kiếm tiền không), risk (bản quyền, nhạy cảm, lệch giá trị), note một câu giải thích."
    )


def ideas_prompt(persona: Persona, trends: list[dict], stage_plan: list[str], recent_titles: list[str],
                 learnings: list[str]) -> str:
    stages = ", ".join(STAGE_LABELS[s] for s in stage_plan)
    return (
        f"{persona_block(persona)}\n\n"
        f"Trend đã qua hai bộ lọc (hợp persona, còn đủ thời gian):\n{json.dumps(trends, ensure_ascii=False, indent=2)}\n\n"
        f"Bài gần đây (tránh trùng): {json.dumps(recent_titles, ensure_ascii=False)}\n"
        f"Bài học từ số liệu: {json.dumps(learnings, ensure_ascii=False)}\n\n"
        f"Tạo đúng {len(stage_plan)} ý tưởng cho tuần tới, lần lượt theo bước phễu: {stages}. "
        "Mỗi ý có góc nhìn riêng của creator (không phải lặp lại trend), lý do nên làm gắn với mục tiêu kiếm tiền. "
        "trend_id là id trend dùng làm chất liệu, hoặc null nếu là nội dung evergreen."
    )


def content_prompt(persona: Persona, idea: dict, platform: str, n_variants: int, needs_disclosure: bool) -> str:
    disclosure = (
        "Nội dung có yếu tố affiliate/tài trợ: caption phải có nhãn quảng cáo rõ ràng (ví dụ #quangcao hoặc #affiliate). "
        if needs_disclosure else ""
    )
    return (
        f"{persona_block(persona)}\n\n"
        f"Ý tưởng (JSON): {json.dumps(idea, ensure_ascii=False)}\n"
        f"Nền tảng: {platform} (video dọc 9:16, 30–60 giây).\n\n"
        f"Viết {n_variants} phương án khác nhau. Mỗi phương án gồm: hook nói trong 3 giây đầu; kịch bản có nhịp "
        "(mỗi dòng có mốc thời gian t, lời thoại line, gợi ý cảnh quay visual dùng cảnh thật của creator); "
        "bài dài cho Facebook/blog; caption ngắn; 5–8 hashtag; CTA dẫn về bước phễu của ý tưởng. "
        f"{disclosure}"
        "Cuối cùng tự chấm voice_score 0–1: mức giống giọng mẫu, và voice_notes ghi chỗ cần người dùng sửa."
    )

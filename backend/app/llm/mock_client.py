"""Client giả lập: sinh kết quả có cấu trúc từ dữ liệu đầu vào, không cần mạng.

Dùng cho chạy thử, demo và test. Nội dung chỉ mang tính khung mẫu.
"""

from __future__ import annotations

import hashlib

from .base import LLMRequest, LLMUsage

STAGE_CTA = {
    "attract": "Follow để xem phần tiếp theo nhé!",
    "trust": "Lưu lại để dùng khi cần, và comment câu hỏi của bạn.",
    "sell": "Link chi tiết ở bio, inbox mình để được tư vấn.",
}


def _slug(text: str) -> str:
    return "".join(ch for ch in text.lower().replace(" ", "") if ch.isalnum())[:24] or "noidung"


def _stable_float(seed: str, lo: float = 0.0, hi: float = 1.0) -> float:
    h = int(hashlib.sha256(seed.encode()).hexdigest()[:8], 16) / 0xFFFFFFFF
    return round(lo + (hi - lo) * h, 2)


class MockClient:
    name = "mock"

    def generate_json(self, req: LLMRequest) -> tuple[dict, LLMUsage]:
        handler = getattr(self, f"_{req.task}")
        return handler(req.context), LLMUsage(model="mock")

    def _persona_extract(self, ctx: dict) -> dict:
        q = ctx.get("questionnaire", {})
        samples = ctx.get("samples", [])
        tone = q.get("tone") or "gần gũi, thẳng thắn, có chút hài hước"
        catch = q.get("catchphrases") or ([samples[0].split(".")[0][:60]] if samples else [])
        return {
            "summary": f"{ctx['name']} làm nội dung {ctx['niche']}, nói chuyện như một người bạn đi trước.",
            "tone": tone,
            "audience": q.get("audience") or f"người mới quan tâm {ctx['niche']}",
            "values": q.get("values") or ["thực tế", "trung thực", "dễ áp dụng"],
            "banned_topics": q.get("banned_topics") or ["chính trị", "hứa làm giàu nhanh"],
            "catchphrases": catch,
            "differentiators": q.get("differentiators") or [f"trải nghiệm thật trong {ctx['niche']}"],
            "good_examples": samples[:2] or [f"Nói thật nhé, {ctx['niche']} không khó như bạn nghĩ đâu."],
            "bad_examples": ["Trong thời đại số ngày nay, việc tối ưu hóa là vô cùng quan trọng."],
        }

    def _trend_fit(self, ctx: dict) -> dict:
        niche = ctx["niche"].lower()
        scores = []
        for t in ctx["trends"]:
            text = f"{t['title']} {t.get('description', '')}".lower()
            overlap = any(w in text for w in niche.split() if len(w) > 2)
            fit = _stable_float(f"{niche}-{t['id']}", 0.55, 0.95) if overlap else _stable_float(f"{t['id']}", 0.1, 0.6)
            scores.append({"trend_id": t["id"], "fit": fit, "risk": "medium" if t.get("kind") == "sound" else "low",
                           "note": "Khớp niche" if overlap else "Ít liên quan tới niche"})
        return {"scores": scores}

    def _ideas(self, ctx: dict) -> dict:
        trends = ctx["trends"]
        niche = ctx["niche"]
        ideas = []
        for i, stage in enumerate(ctx["stage_plan"]):
            t = trends[i % len(trends)] if trends else None
            base = t["title"] if t else f"Sai lầm phổ biến khi bắt đầu {niche}"
            ideas.append({
                "title": f"{base}: góc nhìn của {ctx['persona_name']} (#{i + 1})",
                "angle": f"Kể trải nghiệm thật về {niche} liên quan tới '{base}'",
                "reason": f"Phục vụ bước {stage}, hướng tới mục tiêu {ctx['goal']}",
                "funnel_stage": stage,
                "trend_id": t["id"] if t else None,
            })
        return {"ideas": ideas}

    def _write_content(self, ctx: dict) -> dict:
        idea = ctx["idea"]
        stage = idea["funnel_stage"]
        tag = _slug(ctx["niche"])
        variants = []
        for n in range(ctx["n_variants"]):
            hook = [f"Đừng làm {idea['title'].split(':')[0]} nếu chưa biết điều này!",
                    f"3 giây thôi: {idea['title'].split(':')[0]} thật ra là vậy nè.",
                    f"Mình đã sai về {ctx['niche']} suốt 1 năm."][n % 3]
            caption = f"{idea['angle']}. {STAGE_CTA[stage]}"
            if ctx.get("needs_disclosure"):
                caption += " #quangcao"
            variants.append({
                "hook": hook,
                "script": [
                    {"t": "0-3s", "line": hook, "visual": "Cận mặt, nhìn thẳng camera"},
                    {"t": "3-15s", "line": f"Bối cảnh: {idea['angle']}.", "visual": "Cảnh thật đang làm việc"},
                    {"t": "15-40s", "line": "Ba điều mình rút ra, từng điều một.", "visual": "Chữ trên màn hình từng ý"},
                    {"t": "40-50s", "line": STAGE_CTA[stage], "visual": "Quay lại cận mặt, chỉ tay vào nút"},
                ],
                "long_post": f"{hook}\n\n{idea['angle']}.\n\nLý do mình chia sẻ: {idea['reason']}.\n\n{STAGE_CTA[stage]}",
                "caption": caption,
                "hashtags": [f"#{tag}", "#creator", "#hoctrentiktok", "#xuhuong", "#chiase"],
                "cta": STAGE_CTA[stage],
                "voice_score": _stable_float(f"{idea['title']}-{n}", 0.6, 0.9),
                "voice_notes": "Thêm một câu chuyện cá nhân cụ thể ở đoạn bối cảnh.",
            })
        return {"variants": variants}

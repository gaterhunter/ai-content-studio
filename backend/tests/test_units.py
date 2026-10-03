from datetime import date, timedelta

from app.models import Platform, TrendSnapshot
from app.services import compliance, ideas, trends


def test_stage_plan_matches_goal_mix():
    plan = ideas.stage_plan("course")
    assert len(plan) == 7
    assert plan.count("attract") == 2 and plan.count("trust") == 3 and plan.count("sell") == 2
    assert plan[:3] == ["attract", "trust", "sell"]  # rải đều, không dồn
    assert len(ideas.stage_plan("ads", 10)) == 10


def test_timing_filter_drops_trends_without_enough_runway():
    assert trends.timing_score(1, lead_days=2) == 0.0
    assert trends.timing_score(14, lead_days=2) == 1.0
    t = TrendSnapshot(observed_on=date(2026, 10, 1), platform=Platform.tiktok, kind="sound", title="x")
    assert trends.expiry_of(t) == date(2026, 10, 8)


def test_compliance_flags_promises_and_missing_disclosure():
    r = compliance.check("Cam kết lợi nhuận, lãi 30% mỗi tháng", banned_topics=[], disclosure_required=True)
    types = {i["type"] for i in r["issues"]}
    assert not r["ok"]
    assert {"hua_hen_tai_chinh", "thieu_nhan_quang_cao"} <= types
    ok = compliance.check("Mẹo Excel hay #quangcao", banned_topics=[], disclosure_required=True)
    assert ok["ok"]


def test_compliance_banned_topics_from_persona():
    r = compliance.check("Bàn chuyện chính trị hôm nay", banned_topics=["chính trị"], disclosure_required=False)
    assert not r["ok"]


def test_disclosure_only_for_sponsored_sell_content():
    assert compliance.needs_disclosure("affiliate", "sell")
    assert not compliance.needs_disclosure("affiliate", "attract")
    assert not compliance.needs_disclosure("course", "sell")


def test_week_start_is_monday():
    d = date(2026, 10, 3)  # thứ Bảy
    assert ideas.week_start(d) == d - timedelta(days=5)

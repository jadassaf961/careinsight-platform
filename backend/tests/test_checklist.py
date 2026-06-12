"""Checklist service tests."""
from __future__ import annotations

from app.services.checklist_service import BASE_CHECKLIST, generate_checklist


class TestGenerateChecklist:
    def test_low_risk_returns_base_only(self):
        items = generate_checklist([], "Low")
        assert len(items) == len(BASE_CHECKLIST)
        assert all(i["source"] == "base" for i in items)

    def test_high_risk_prepends_priority_items(self):
        items = generate_checklist([], "High")
        assert items[0]["source"] == "risk_tier"
        assert "HIGH RISK" in items[0]["text"]
        assert "48-hour" in items[1]["text"]

    def test_factor_specific_action_added(self):
        items = generate_checklist([("diabetes_history", 0.5)], "Low")
        assert any("HbA1c" in i["text"] or "diabetes" in i["text"].lower() for i in items)

    def test_no_duplicate_actions(self):
        items = generate_checklist([("diabetes_a", 0.5), ("diabetes_b", 0.3)], "Low")
        texts = [i["text"] for i in items]
        assert len(texts) == len(set(texts))

    def test_factor_items_capped(self):
        many = [(f"feat_{i}", float(i)) for i in range(20)]
        items = generate_checklist(many, "Low")
        extras = [i for i in items if i["source"] == "factor"]
        assert len(extras) <= 5

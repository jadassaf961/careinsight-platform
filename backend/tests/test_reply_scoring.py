"""Table-driven tests for check-in reply scoring — this is clinical logic."""
from __future__ import annotations

import pytest

from app.services.messaging.templates import render_checkin, score_reply


@pytest.mark.parametrize("text,red_flag,meds_missed,opted_out,score", [
    ("I feel fine, took all my meds", False, False, False, 0),
    ("having chest pain since morning", True, False, False, 2),
    ("Severe shortness of breath at night", True, False, False, 2),
    ("i missed my pills two days", False, True, False, 1),
    ("ran out of medication", False, True, False, 1),
    ("chest pain and I missed my meds", True, True, False, 2),
    ("STOP", False, False, True, 0),
    ("stop", False, False, True, 0),
    ("عندي ألم في الصدر", True, False, False, 2),      # Arabic: chest pain
    ("نسيت الدواء اليوم", False, True, False, 1),        # Arabic: forgot meds
    ("توقف", False, False, True, 0),                     # Arabic: stop
    ("", False, False, False, 0),
])
def test_score_reply(text, red_flag, meds_missed, opted_out, score):
    result = score_reply(text)
    assert result["red_flag"] is red_flag
    assert result["meds_missed"] is meds_missed
    assert result["opted_out"] is opted_out
    assert result["concern_score"] == score


def test_render_checkin_en_and_ar():
    en = render_checkin("en", name="Rania", hospital="Rizk Hospital", day=7)
    assert "Rania" in en and "Rizk Hospital" in en and "day 7" in en
    ar = render_checkin("ar", name="رانيا", hospital="مستشفى رزق", day=7)
    assert "رانيا" in ar
    # unknown language falls back to English
    assert render_checkin("fr", name="X", hospital="H", day=2) == render_checkin("en", name="X", hospital="H", day=2)

"""Transitions API + config/role prerequisites."""
from __future__ import annotations

from app.core.config import Settings
from app.models.user import RoleName


def test_pharmacist_role_exists():
    assert RoleName.PHARMACIST.value == "pharmacist"


def test_settings_have_messaging_defaults():
    s = Settings(_env_file=None)
    assert s.messaging_provider == "simulated"
    assert s.checkin_day_offsets_list == [2, 7, 14, 30]
    assert s.checkin_no_response_hours == 48
    assert s.checkin_max_attempts == 3

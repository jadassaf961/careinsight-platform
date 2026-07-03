"""Bilingual check-in templates + deterministic reply scoring.

Templates live in code (not the DB) in v1 — nothing edits them at runtime.
Scoring scans ALL keyword languages regardless of the patient's preferred
language: patients reply in whatever language they like.
"""
from __future__ import annotations

CHECKIN_TEMPLATES: dict[str, str] = {
    "en": (
        "Hello {name}, this is {hospital} checking in — day {day} after your discharge.\n"
        "Please reply to these questions:\n"
        "1. Any chest pain, severe shortness of breath, or bleeding?\n"
        "2. Have you taken all your medications as prescribed?\n"
        "3. Any other symptoms or concerns?\n"
        "Reply STOP to end these messages."
    ),
    "ar": (
        "مرحباً {name}، معك {hospital} للاطمئنان عليك — اليوم {day} بعد الخروج.\n"
        "الرجاء الإجابة على الأسئلة التالية:\n"
        "١. هل تعاني من ألم في الصدر أو ضيق تنفس شديد أو نزيف؟\n"
        "٢. هل تناولت جميع أدويتك كما وُصفت؟\n"
        "٣. هل لديك أي أعراض أو مخاوف أخرى؟\n"
        "أرسل STOP أو توقف لإيقاف الرسائل."
    ),
}

RED_FLAG_KEYWORDS: list[str] = [
    "chest pain", "shortness of breath", "short of breath", "bleeding",
    "fainted", "fainting", "passed out", "severe pain",
    "ألم في الصدر", "ضيق تنفس", "نزيف", "إغماء", "ألم شديد",
]

MEDS_MISSED_KEYWORDS: list[str] = [
    "missed my", "missed the", "didn't take", "did not take", "no meds",
    "ran out", "stopped taking",
    "نسيت الدواء", "لم آخذ", "خلص الدواء", "توقفت عن",
]

OPT_OUT_KEYWORDS: list[str] = ["stop", "توقف"]


def render_checkin(language: str, *, name: str, hospital: str, day: int) -> str:
    template = CHECKIN_TEMPLATES.get(language, CHECKIN_TEMPLATES["en"])
    return template.format(name=name, hospital=hospital, day=day)


def score_reply(text: str) -> dict:
    lowered = text.lower().strip()
    opted_out = any(lowered == k or lowered.startswith(k + " ") for k in OPT_OUT_KEYWORDS)
    red_flag = any(k in lowered for k in RED_FLAG_KEYWORDS)
    meds_missed = any(k in lowered for k in MEDS_MISSED_KEYWORDS)
    concern_score = 2 if red_flag else (1 if meds_missed else 0)
    return {
        "red_flag": red_flag,
        "meds_missed": meds_missed,
        "opted_out": opted_out,
        "concern_score": concern_score,
    }

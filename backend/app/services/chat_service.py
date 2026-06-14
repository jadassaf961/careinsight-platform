"""AI Copilot service — wraps Gemini for decision-support patient explanations."""
from __future__ import annotations

from typing import Any

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

_DISCLAIMER = (
    "AI decision-support only — not a substitute for clinical judgment."
)


def _system_prompt(patient_context: dict[str, Any]) -> str:
    lines = [
        "You are a clinical decision-support assistant helping a healthcare "
        "professional understand a patient's predicted 30-day readmission risk. "
        "You explain the ML model's output in plain clinical language and suggest "
        "evidence-based follow-up actions tailored to this patient's specific risk factors.",
        "",
        "CONSTRAINTS:",
        "- You are decision-support, NOT a replacement for clinical judgment.",
        "- Do NOT issue diagnoses or prescribe specific medication doses.",
        "- DO suggest evidence-based follow-up actions, referrals, and monitoring plans.",
        "- When discussing risk factors or asked what to do next, ALWAYS provide 2–4 specific,",
        "  actionable follow-up items as bullet points (e.g. 'Schedule nephrology follow-up",
        "  within 48 h — creatinine is 2.1', 'Perform medication reconciliation — 14 active",
        "  medications detected').",
        "- Ground every suggestion in the patient data below — reference actual values.",
        "- Be concise but complete. Use bullet points for lists.",
        f"- Always end with: ⚕️ *{_DISCLAIMER}*",
        "",
        "PATIENT CONTEXT (real clinical data — reference values by name in your response):",
    ]
    for k, v in patient_context.items():
        lines.append(f"  • {k}: {v}")
    return "\n".join(lines)


def generate_reply(
    patient_context: dict[str, Any],
    message: str,
    history: list[dict[str, str]],
) -> str:
    """Generate a single assistant turn. Falls back to a stub when no API key set."""
    if not settings.gemini_api_key:
        return (
            "AI assistant is not configured (no GEMINI_API_KEY). "
            "This is a decision-support channel; the operator should ask a clinician.\n\n"
            f"⚕️ *{_DISCLAIMER}*"
        )

    try:
        import google.generativeai as genai
        genai.configure(api_key=settings.gemini_api_key)
        model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            system_instruction=_system_prompt(patient_context),
        )
        gemini_history = [
            {"role": "user" if h["role"] == "user" else "model",
             "parts": [h["content"]]}
            for h in history
        ]
        chat = model.start_chat(history=gemini_history)
        response = chat.send_message(message)
        return response.text
    except Exception as exc:  # noqa: BLE001
        logger.warning("Gemini call failed: %s", exc)
        return (
            f"AI assistant temporarily unavailable: {exc}\n\n"
            f"⚕️ *{_DISCLAIMER}*"
        )

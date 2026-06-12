"""PDF discharge memo generation — ported from src/utils/helpers.generate_pdf."""
from __future__ import annotations

import io
from datetime import datetime
from typing import Iterable

from fpdf import FPDF, XPos, YPos


def generate_discharge_pdf(
    *,
    patient_info: dict[str, str],
    risk_score: float,
    risk_tier: str,
    top_factors: Iterable[tuple[str, str, float]],
    checklist: Iterable[str],
    model_name: str,
    threshold: float,
) -> bytes:
    """Render a one-page discharge memo.

    Parameters
    ----------
    patient_info: label → value rows for the "Patient Information" section.
    risk_score: probability in [0, 1].
    risk_tier: "High" or "Low".
    top_factors: iterable of (feature_name, humanized_label, shap_value).
    checklist: iterable of checklist text strings.
    model_name: human-readable model name for the header.
    threshold: decision threshold used.
    """
    pdf = FPDF()
    pdf.add_page()
    pdf.set_margins(15, 15, 15)
    pdf.set_auto_page_break(auto=True, margin=15)
    eff_w = pdf.w - pdf.l_margin - pdf.r_margin

    pdf.set_fill_color(12, 74, 110)
    pdf.rect(0, 0, 210, 38, "F")
    pdf.set_font("Helvetica", "B", 17)
    pdf.set_text_color(255, 255, 255)
    pdf.set_xy(10, 8)
    pdf.cell(0, 8, "Hospital Readmission Risk Report",
             new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(186, 230, 253)
    pdf.set_xy(10, 20)
    ts = datetime.now().strftime("%B %d, %Y  %H:%M")
    pdf.cell(0, 6,
             f"Generated: {ts}   |   Model: {model_name}   |   Threshold: {threshold:.2f}",
             new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
    pdf.ln(12)
    pdf.set_text_color(0, 0, 0)

    def section(title: str) -> None:
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_fill_color(240, 249, 255)
        pdf.cell(eff_w, 8, f"  {title}",
                 new_x=XPos.LMARGIN, new_y=YPos.NEXT, fill=True, border="B")
        pdf.ln(3)

    section("Patient Information")
    pdf.set_font("Helvetica", "", 11)
    for k, v in patient_info.items():
        if v and str(v) != "N/A":
            pdf.cell(65, 7, f"{k}:", new_x=XPos.RIGHT, new_y=YPos.TOP)
            pdf.set_font("Helvetica", "B", 11)
            pdf.cell(0, 7, str(v), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.set_font("Helvetica", "", 11)
    pdf.ln(4)

    section("Readmission Risk Assessment")
    pct = int(round(risk_score * 100))
    tier_upper = risk_tier.upper()
    if tier_upper == "HIGH":
        pdf.set_fill_color(220, 38, 38)
    else:
        pdf.set_fill_color(22, 163, 74)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(70, 12, f"{pct}%  -  {tier_upper} RISK",
             new_x=XPos.RIGHT, new_y=YPos.TOP, align="C", fill=True, border=1)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 12, "   Predicted probability of 30-day readmission",
             new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(4)

    section("Top Clinical Risk Factors (SHAP Analysis)")
    pdf.set_font("Helvetica", "", 10)
    for i, (_, label, val) in enumerate(list(top_factors)[:8], 1):
        direction = "Increases" if val > 0 else "Decreases"
        r, g, b = (220, 38, 38) if val > 0 else (22, 163, 74)
        pdf.set_text_color(r, g, b)
        pdf.cell(8, 7, f"{i}.", new_x=XPos.RIGHT, new_y=YPos.TOP)
        pdf.set_text_color(30, 30, 30)
        pdf.cell(80, 7, label[:40], new_x=XPos.RIGHT, new_y=YPos.TOP)
        pdf.set_text_color(r, g, b)
        pdf.cell(0, 7, f"{direction} risk  ({abs(val):.4f})",
                 new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_text_color(0, 0, 0)
    pdf.ln(4)

    section("Preventive Action Checklist")
    pdf.set_font("Helvetica", "", 10)
    for item in checklist:
        x_start = pdf.l_margin
        pdf.set_xy(x_start, pdf.get_y())
        pdf.set_fill_color(224, 242, 254)
        pdf.cell(5, 6, "", fill=True, border=1, new_x=XPos.RIGHT, new_y=YPos.TOP)
        pdf.cell(4, 6, "", new_x=XPos.RIGHT, new_y=YPos.TOP)
        pdf.set_x(x_start + 9)
        pdf.multi_cell(eff_w - 9, 6, item)
    pdf.ln(4)

    pdf.set_y(-18)
    pdf.set_font("Helvetica", "I", 7.5)
    pdf.set_text_color(150, 150, 150)
    pdf.cell(0, 5,
             "CONFIDENTIAL - Contains Protected Health Information (PHI). Handle per HIPAA.",
             align="C")

    buf = io.BytesIO()
    pdf.output(buf)
    return buf.getvalue()

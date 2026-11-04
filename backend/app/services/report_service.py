"""
SmartPulse PDF Wellness Report Generator
Generates a downloadable PDF summary using ReportLab.
"""

import io
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from ..models import ReportRequest
from ..preprocessing import FEATURE_LABELS
from .. import config

def generate_pdf_report(report_req: ReportRequest) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()

    # Custom styles
    primary_color = colors.HexColor("#0F172A")    # Deep Navy
    accent_teal = colors.HexColor("#0D9488")      # Teal
    accent_cyan = colors.HexColor("#0284C7")      # Cyan/Blue
    text_dark = colors.HexColor("#1E293B")
    text_muted = colors.HexColor("#64748B")
    alert_red = colors.HexColor("#DC2626")
    alert_green = colors.HexColor("#16A34A")

    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=24,
        leading=28,
        textColor=primary_color
    )
    tagline_style = ParagraphStyle(
        "DocTagline",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=11,
        leading=14,
        textColor=accent_teal
    )
    h2_style = ParagraphStyle(
        "H2",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=14,
        leading=18,
        textColor=primary_color,
        spaceBefore=12,
        spaceAfter=6
    )
    body_style = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=text_dark
    )
    bullet_style = ParagraphStyle(
        "Bullet",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9.5,
        leading=13.5,
        textColor=text_dark,
        leftIndent=12
    )
    disclaimer_style = ParagraphStyle(
        "Disclaimer",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=8.5,
        leading=11.5,
        textColor=text_muted
    )

    elements = []

    # Header
    elements.append(Paragraph("SmartPulse Assessment Report", title_style))
    elements.append(Paragraph("Understand stress. Predict burnout. Take action.", tagline_style))
    elements.append(Spacer(1, 4))
    
    current_time = datetime.now().strftime("%B %d, %Y - %H:%M")
    elements.append(Paragraph(f"Generated for: <b>{report_req.student_name}</b> | Date: {current_time}", body_style))
    elements.append(Spacer(1, 8))
    elements.append(HRFlowable(width="100%", thickness=1.5, color=accent_teal, spaceAfter=14))

    # Executive Summary Card
    is_high = report_req.prediction.category == "High Risk"
    risk_color = alert_red if is_high else alert_green
    high_pct = report_req.prediction.probabilities.get("high", 0.5) * 100

    summary_data = [
        [
            Paragraph("<b>Predicted Burnout Category:</b>", body_style),
            Paragraph(f"<font color='{risk_color.hexval()}'><b>{report_req.prediction.category}</b></font> ({high_pct:.1f}% estimated risk probability)", body_style)
        ],
        [
            Paragraph("<b>Estimated Burnout Score:</b>", body_style),
            Paragraph(f"<b>{report_req.score.predicted_score:.1f}</b> / 25 (94% Credible Interval: {report_req.score.credible_interval_94[0]:.1f} - {report_req.score.credible_interval_94[1]:.1f})", body_style)
        ],
        [
            Paragraph("<b>Dataset Percentile:</b>", body_style),
            Paragraph(f"Higher than {report_req.score.percentile:.1f}% of surveyed university students (N = 132)", body_style)
        ],
        [
            Paragraph("<b>Calculated Stress Total:</b>", body_style),
            Paragraph(f"{report_req.score.calculated_stress_total or 'N/A'} (PSS-4 Scale, 4 to 20)", body_style)
        ]
    ]

    summary_table = Table(summary_data, colWidths=[180, 350])
    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#E2E8F0")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ("PADDING", (0, 0), (-1, -1), 6),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE")
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 14))

    # Lifestyle Inputs Summary Table
    elements.append(Paragraph("Student Assessment Inputs", h2_style))
    inputs = report_req.inputs
    input_rows = [
        ["Factor", "Student Value", "Survey Scale / Mapping"],
        ["Sleep Duration", f"{inputs.sleep_mid_hrs} hrs/night", "Estimated midpoint"],
        ["Sleep Quality", f"{inputs.sleep_quality} / 5", "1 (Very poor) to 5 (Excellent)"],
        ["Typical Bedtime", f"Code {inputs.bedtime_code}", "1 (<11pm), 2 (11pm-1am), 3 (1-3am), 4 (>3am)"],
        ["Daily Screen Time", f"{inputs.screen_mid_hrs} hrs/day", "Non-academic screen usage"],
        ["Bedtime Smartphone Use", f"Code {inputs.phone_bed_code}", "1 (Never) to 4 (Always)"],
        ["Exercise Frequency", f"{inputs.exercise_days_mid} days/week", "Weekly physical activity"],
        ["Upcoming Deadlines", f"Code {inputs.deadlines_code}", "1 (0-2) to 4 (9+ deadlines)"],
        ["Perceived Workload", f"Code {inputs.workload_code}", "1 (Very light) to 4 (Overwhelming)"],
        ["Exam vs Expectations", f"{inputs.performance_code if inputs.performance_code else 'No exams yet'}", "1 (Much below) to 5 (Much above)"]
    ]
    input_table = Table(input_rows, colWidths=[160, 160, 210])
    input_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0F172A")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
        ("PADDING", (0, 0), (-1, -1), 4.5),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5)
    ]))
    elements.append(input_table)
    elements.append(Spacer(1, 14))

    # Top Contributing Factors (Attributions)
    elements.append(Paragraph("Statistical Attribution & Key Drivers", h2_style))
    elements.append(Paragraph(
        "The following feature contributions are derived directly from the model's standardized regression coefficients "
        "(Logistic Regression log-odds decomposition):",
        body_style
    ))
    elements.append(Spacer(1, 6))

    for tf in report_req.explanation.top_factors[:4]:
        bullet_text = f"• <b>{tf.label}</b> ({tf.impact_level}): {tf.explanation}"
        elements.append(Paragraph(bullet_text, bullet_style))
        elements.append(Spacer(1, 3))

    elements.append(Spacer(1, 10))

    # Supportive Lifestyle Recommendations
    elements.append(Paragraph("Personalized Supportive Recommendations", h2_style))
    elements.append(Paragraph(
        "Based on your assessment profile and observed statistical correlations in student well-being literature, "
        "here are supportive non-clinical habits to consider:",
        body_style
    ))
    elements.append(Spacer(1, 6))

    recs = []
    if inputs.workload_code >= 3:
        recs.append("<b>Pacing & Modular Work:</b> Perceived workload is the most decisive correlate with burnout. Deconstruct semester projects into 25-minute focused blocks (Pomodoro method) and prioritize top-2 daily tasks.")
    if inputs.phone_bed_code >= 3:
        recs.append("<b>Bedtime Wind-Down Sanctuary:</b> Keeping smartphones outside arm's reach 30 minutes before sleep helps reduce pre-sleep cognitive alertness and supports restorative melatonin production.")
    if inputs.sleep_mid_hrs <= 5.5:
        recs.append("<b>Protecting Sleep Duration:</b> Consistently sleeping under 6 hours correlates with diminished stress resilience. Aim to incrementally advance bedtime by 15-20 minutes.")
    if inputs.exercise_days_mid <= 1.5:
        recs.append("<b>Physical Movement:</b> Even short 15-minute brisk campus walks promote autonomic regulation and cortisol clearance after long study sessions.")
    if inputs.performance_code is not None and inputs.performance_code <= 2.0:
        recs.append("<b>Academic Perspective & Support:</b> Discuss difficult coursework concepts with teaching assistants or study peers early to mitigate cumulative exam stress.")
    
    recs.append("<b>Campus Community:</b> Build in daily micro-breaks with friends or hobbies to provide mental disengagement from academic deadlines.")

    for r in recs:
        elements.append(Paragraph(f"• {r}", bullet_style))
        elements.append(Spacer(1, 4))

    if is_high:
        elements.append(Spacer(1, 6))
        support_note = (
            "<b>A Note on Support:</b> Your results indicate elevated pressure. University life can be demanding, "
            "and feeling overwhelmed is common. We encourage you to speak with a trusted mentor, advisor, or visit "
            "your campus student counseling services for confidential guidance."
        )
        elements.append(Paragraph(support_note, bullet_style))

    elements.append(Spacer(1, 16))
    elements.append(HRFlowable(width="100%", thickness=0.8, color=colors.HexColor("#CBD5E1"), spaceAfter=10))

    # Formal Disclaimer
    elements.append(Paragraph(f"<b>Statistical & Ethical Notice:</b> {config.DISCLAIMER_TEXT}", disclaimer_style))

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()

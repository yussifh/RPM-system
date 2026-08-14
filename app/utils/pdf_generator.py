"""
pdf_generator.py
-----------------
PDF report generation for patient health reports using fpdf2.
Generates professional medical reports with vitals, AI risk, and medications.
"""

from datetime import datetime
from typing import Optional
from fpdf import FPDF


class HealthReportPDF(FPDF):
    """Custom PDF class with RPM branding header/footer."""

    def __init__(self, patient_name: str):
        super().__init__()
        self.patient_name = patient_name
        self.set_auto_page_break(auto=True, margin=25)

    def header(self):
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(34, 169, 150)
        self.cell(0, 6, "Remote Patient Monitoring System", new_x="LMARGIN", new_y="NEXT", align="L")
        self.set_draw_color(34, 169, 150)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10,
                  f"Page {self.page_no()}/{{nb}} | Generated {datetime.now().strftime('%d %B %Y %H:%M')} | Academic Demo Only",
                  align="C")

    def section_title(self, title: str):
        self.set_font("Helvetica", "B", 13)
        self.set_text_color(26, 37, 48)
        self.cell(0, 10, title, new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(34, 169, 150)
        self.line(10, self.get_y(), 80, self.get_y())
        self.ln(3)

    def info_row(self, label: str, value: str):
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(91, 107, 118)
        self.cell(55, 7, label + ":", new_x="RIGHT")
        self.set_font("Helvetica", "", 10)
        self.set_text_color(26, 37, 48)
        self.cell(0, 7, str(value), new_x="LMARGIN", new_y="NEXT")

    def table_header(self, cols: list[str], widths: list[int]):
        self.set_font("Helvetica", "B", 9)
        self.set_fill_color(34, 169, 150)
        self.set_text_color(255, 255, 255)
        for col, w in zip(cols, widths):
            self.cell(w, 7, col, border=1, fill=True, align="C")
        self.ln()

    def table_row(self, values: list[str], widths: list[int], fill: bool = False):
        self.set_font("Helvetica", "", 8)
        self.set_text_color(26, 37, 48)
        if fill:
            self.set_fill_color(244, 246, 247)
        for val, w in zip(values, widths):
            self.cell(w, 6, str(val)[:25], border=1, fill=fill, align="C")
        self.ln()


def generate_health_report_pdf(
    patient_name: str,
    patient_info: dict,
    vitals_history: list,
    predictions: list = None,
    medications: list = None,
    summary_stats: dict = None,
) -> bytes:
    """
    Generates a comprehensive health report PDF.

    Args:
        patient_name: Patient's full name
        patient_info: dict with age, gender, conditions, emergency_contact
        vitals_history: list of VitalsRecord objects
        predictions: list of prediction dicts (optional)
        medications: list of Medication objects (optional)
        summary_stats: dict with aggregate stats (optional)

    Returns:
        PDF content as bytes
    """
    pdf = HealthReportPDF(patient_name)
    pdf.alias_nb_pages()
    pdf.add_page()

    # ── Patient Info ────────────────────────────────────────────────
    pdf.section_title("Patient Information")
    pdf.info_row("Name", patient_name)
    pdf.info_row("Age", patient_info.get("age", "N/A"))
    pdf.info_row("Gender", patient_info.get("gender", "N/A").title())
    pdf.info_row("Chronic Conditions",
                 ", ".join(c.title() for c in patient_info.get("conditions", [])) or "None")
    pdf.info_row("Emergency Contact", patient_info.get("emergency_contact", "N/A"))
    pdf.info_row("Report Date", datetime.now().strftime("%d %B %Y, %H:%M"))
    pdf.info_row("Total Readings", len(vitals_history))
    pdf.ln(5)

    # ── Summary Statistics ──────────────────────────────────────────
    if summary_stats:
        pdf.section_title("Vitals Summary")
        pdf.info_row("Average Systolic BP", f"{summary_stats.get('avg_systolic', 'N/A')} mmHg")
        pdf.info_row("Average Diastolic BP", f"{summary_stats.get('avg_diastolic', 'N/A')} mmHg")
        pdf.info_row("Average Heart Rate", f"{summary_stats.get('avg_hr', 'N/A')} bpm")
        pdf.info_row("Average Glucose", f"{summary_stats.get('avg_glucose', 'N/A')} mg/dL")
        pdf.ln(5)

    # ── Recent Vitals ──────────────────────────────────────────────
    if vitals_history:
        pdf.section_title("Recent Vitals Readings")
        cols = ["Date", "BP (mmHg)", "HR (bpm)", "Glucose", "SpO2", "Temp"]
        widths = [38, 32, 25, 28, 22, 22]
        pdf.table_header(cols, widths)
        for i, r in enumerate(vitals_history[:20]):
            date_str = r.recorded_at.strftime("%d/%m/%y %H:%M") if hasattr(r.recorded_at, "strftime") else str(r.recorded_at)[:16]
            bp = f"{r.systolic_bp}/{r.diastolic_bp}" if r.systolic_bp and r.diastolic_bp else "—"
            hr = str(r.heart_rate) if r.heart_rate else "—"
            glu = f"{float(r.glucose_level):.0f}" if r.glucose_level else "—"
            spo2 = f"{r.oxygen_saturation}%" if r.oxygen_saturation else "—"
            temp = f"{float(r.temperature_c):.1f}" if r.temperature_c else "—"
            pdf.table_row([date_str, bp, hr, glu, spo2, temp], widths, fill=(i % 2 == 0))
        pdf.ln(5)

    # ── AI Risk Predictions ────────────────────────────────────────
    if predictions:
        pdf.section_title("AI Risk Assessment")
        cols = ["Disease", "Risk Level", "Probability", "Model"]
        widths = [40, 35, 35, 50]
        pdf.table_header(cols, widths)
        for i, pred in enumerate(predictions):
            pdf.table_row([
                pred.get("disease_type", "").title(),
                pred.get("risk_level", "").upper(),
                f"{pred.get('risk_score', 0):.1%}",
                pred.get("model_version", "N/A"),
            ], widths, fill=(i % 2 == 0))
        pdf.ln(5)

    # ── Medications ────────────────────────────────────────────────
    if medications:
        pdf.section_title("Current Medications")
        for med in medications:
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_text_color(26, 37, 48)
            status = "Active" if med.is_active else "Stopped"
            pdf.cell(0, 7, f"{med.name} - {status}", new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(91, 107, 118)
            pdf.cell(0, 6, f"  Dosage: {med.dosage} | Frequency: {med.frequency} | Route: {med.route}",
                     new_x="LMARGIN", new_y="NEXT")
            if med.prescribed_by:
                pdf.cell(0, 6, f"  Prescribed by: {med.prescribed_by}", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(2)
        pdf.ln(3)

    # ── Disclaimer ─────────────────────────────────────────────────
    pdf.ln(10)
    pdf.set_font("Helvetica", "I", 9)
    pdf.set_text_color(150, 150, 150)
    pdf.multi_cell(0, 5,
        "DISCLAIMER: This report is generated by an AI-integrated decision-support "
        "tool for academic demonstration purposes only. It is NOT a substitute for "
        "professional medical advice, diagnosis, or treatment. Always consult a "
        "qualified healthcare provider for medical decisions."
    )

    return bytes(pdf.output())

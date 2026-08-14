"""
prescription_generator.py
--------------------------
Generates professional printable prescriptions as PDF.
"""

from datetime import datetime
from fpdf import FPDF


class PrescriptionPDF(FPDF):
    """Custom PDF for medical prescriptions."""

    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=20)

    def header(self):
        # Rx header
        self.set_font("Helvetica", "B", 24)
        self.set_text_color(34, 169, 150)
        self.cell(0, 12, "Rx", new_x="LMARGIN", new_y="NEXT", align="L")

        self.set_font("Helvetica", "", 10)
        self.set_text_color(91, 107, 118)
        self.cell(0, 5, "Remote Patient Monitoring System", new_x="LMARGIN", new_y="NEXT", align="L")
        self.set_draw_color(34, 169, 150)
        self.line(10, self.get_y() + 2, 200, self.get_y() + 2)
        self.ln(8)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10,
                  f"Generated {datetime.now().strftime('%d %B %Y %H:%M')} | Academic Demo Only",
                  align="C")


def generate_prescription_pdf(
    doctor_name: str,
    doctor_specialization: str = "",
    doctor_license: str = "",
    patient_name: str = "",
    patient_age: int = None,
    patient_gender: str = "",
    medications: list = None,
    diagnosis: str = "",
    notes: str = "",
) -> bytes:
    """
    Generates a printable prescription PDF.

    Args:
        doctor_name: Doctor's full name
        doctor_specialization: Doctor's specialty
        doctor_license: Medical license number
        patient_name: Patient's full name
        patient_age: Patient's age
        patient_gender: Patient's gender
        medications: list of dicts with name, dosage, frequency, duration, instructions
        diagnosis: Diagnosis text
        notes: Additional notes

    Returns:
        PDF content as bytes
    """
    pdf = PrescriptionPDF()
    pdf.add_page()

    # Doctor info
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(26, 37, 48)
    pdf.cell(0, 7, f"Dr. {doctor_name}", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(91, 107, 118)
    if doctor_specialization:
        pdf.cell(0, 5, f"Specialization: {doctor_specialization}", new_x="LMARGIN", new_y="NEXT")
    if doctor_license:
        pdf.cell(0, 5, f"License: {doctor_license}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)

    # Patient info
    pdf.set_draw_color(228, 232, 234)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(3)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(26, 37, 48)
    pdf.cell(25, 7, "Patient:", new_x="RIGHT")
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 7, patient_name, new_x="LMARGIN", new_y="NEXT")
    if patient_age or patient_gender:
        pdf.cell(25, 7, "Details:", new_x="RIGHT")
        pdf.set_font("Helvetica", "", 10)
        details = []
        if patient_age: details.append(f"Age: {patient_age}")
        if patient_gender: details.append(f"Gender: {patient_gender.title()}")
        pdf.cell(0, 7, " | ".join(details), new_x="LMARGIN", new_y="NEXT")
    pdf.cell(25, 7, "Date:", new_x="RIGHT")
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 7, datetime.now().strftime("%d %B %Y"), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)

    # Diagnosis
    if diagnosis:
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(26, 37, 48)
        pdf.cell(0, 7, "Diagnosis:", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 10)
        pdf.multi_cell(0, 5, diagnosis)
        pdf.ln(3)

    # Medications table
    if medications:
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(26, 37, 48)
        pdf.cell(0, 8, "Prescribed Medications:", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)

        # Table header
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_fill_color(34, 169, 150)
        pdf.set_text_color(255, 255, 255)
        cols = ["#", "Medication", "Dosage", "Frequency", "Duration"]
        widths = [10, 50, 30, 40, 30]
        for col, w in zip(cols, widths):
            pdf.cell(w, 7, col, border=1, fill=True, align="C")
        pdf.ln()

        # Table rows
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(26, 37, 48)
        for i, med in enumerate(medications, 1):
            fill = (i % 2 == 0)
            if fill:
                pdf.set_fill_color(244, 246, 247)
            pdf.cell(widths[0], 6, str(i), border=1, fill=fill, align="C")
            pdf.cell(widths[1], 6, str(med.get("name", ""))[:25], border=1, fill=fill)
            pdf.cell(widths[2], 6, str(med.get("dosage", "")), border=1, fill=fill, align="C")
            pdf.cell(widths[3], 6, str(med.get("frequency", "")), border=1, fill=fill, align="C")
            pdf.cell(widths[4], 6, str(med.get("duration", "—")), border=1, fill=fill, align="C")
            pdf.ln()

            # Instructions row
            if med.get("instructions"):
                pdf.set_font("Helvetica", "I", 8)
                pdf.set_text_color(91, 107, 118)
                pdf.cell(widths[0], 5, "", border=0)
                pdf.cell(sum(widths[1:]), 5, f"  Note: {med['instructions']}", border=0)
                pdf.ln()
                pdf.set_font("Helvetica", "", 9)
                pdf.set_text_color(26, 37, 48)

        pdf.ln(5)

    # Notes
    if notes:
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(26, 37, 48)
        pdf.cell(0, 7, "Notes / Instructions:", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 10)
        pdf.multi_cell(0, 5, notes)
        pdf.ln(5)

    # Signature line
    pdf.ln(15)
    pdf.set_draw_color(26, 37, 48)
    pdf.line(120, pdf.get_y(), 190, pdf.get_y())
    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(26, 37, 48)
    pdf.cell(0, 5, f"Dr. {doctor_name}", new_x="LMARGIN", new_y="NEXT", align="L")
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(91, 107, 118)
    if doctor_license:
        pdf.cell(0, 5, f"License: {doctor_license}", new_x="LMARGIN", new_y="NEXT", align="L")

    # Disclaimer
    pdf.ln(8)
    pdf.set_font("Helvetica", "I", 7)
    pdf.set_text_color(150, 150, 150)
    pdf.multi_cell(0, 4,
        "DISCLAIMER: This prescription is generated by an AI-integrated decision-support "
        "tool for academic demonstration purposes only. It is NOT a valid medical prescription. "
        "Always consult a qualified healthcare provider."
    )

    return bytes(pdf.output())

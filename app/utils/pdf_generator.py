from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from app.core.config import get_settings


def generate_emergency_id_pdf(name: str, qr_path: str, lines: list[str], file_name: str) -> str:
    output_dir = get_settings().data_dir / "pdf"
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{file_name}.pdf"
    pdf = canvas.Canvas(str(path), pagesize=A4)
    pdf.setTitle("Emergency ID Card")
    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(72, 780, "Monsoon Emergency ID")
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(72, 745, name)
    pdf.drawImage(qr_path, 72, 575, width=140, height=140)
    pdf.setFont("Helvetica", 10)
    y = 540
    for line in lines[:18]:
        pdf.drawString(72, y, line[:95])
        y -= 18
    pdf.save()
    return str(path)


def generate_report_pdf(title: str, lines: list[str], file_name: str) -> str:
    output_dir = get_settings().data_dir / "pdf"
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{file_name}.pdf"
    pdf = canvas.Canvas(str(path), pagesize=A4)
    pdf.setTitle(title)
    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(72, 780, title)
    pdf.setFont("Helvetica", 11)
    y = 740
    for line in lines:
        pdf.drawString(72, y, line[:95])
        y -= 18
        if y < 72:
            pdf.showPage()
            pdf.setFont("Helvetica", 11)
            y = 780
    pdf.save()
    return str(path)

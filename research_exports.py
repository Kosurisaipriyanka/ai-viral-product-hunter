"""Create Excel and PDF reports from saved product research runs."""
from io import BytesIO
from xml.sax.saxutils import escape

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
)


def _summary_rows(run):
    payload = run.get("payload") or {}
    rows = [
        ("Report title", str(run.get("title", "Product research report"))),
        ("Research type", str(run.get("run_type", "Unknown"))),
        ("Saved at (UTC)", str(run.get("created_at", "Unknown"))),
        ("History ID", str(run.get("id", ""))),
    ]
    for key, value in payload.items():
        if isinstance(value, (str, int, float, bool)) or value is None:
            rows.append((str(key), "" if value is None else str(value)))
        elif isinstance(value, list) and (not value or not isinstance(value[0], dict)):
            rows.append((str(key), ", ".join(map(str, value))))
    rows.append(("Important limitation", "Screening signals are not proof of sales, profitability, supplier reliability, or future virality."))
    return rows


def create_excel_report(run):
    """Return an Excel workbook as bytes with Summary and Results sheets."""
    output = BytesIO()
    payload = run.get("payload") or {}
    summary = pd.DataFrame(_summary_rows(run), columns=["Field", "Value"])
    items = payload.get("items")
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        summary.to_excel(writer, sheet_name="Summary", index=False)
        if isinstance(items, list) and items and all(isinstance(item, dict) for item in items):
            pd.DataFrame(items).to_excel(writer, sheet_name="Results", index=False)
        else:
            pd.DataFrame([{"Research payload": str(payload)}]).to_excel(writer, sheet_name="Results", index=False)
        for sheet in writer.book.worksheets:
            sheet.freeze_panes = "A2"
            sheet.auto_filter.ref = sheet.dimensions
            for column_cells in sheet.columns:
                letter = column_cells[0].column_letter
                max_len = max((len(str(cell.value or "")) for cell in column_cells[:100]), default=10)
                sheet.column_dimensions[letter].width = min(max(max_len + 2, 12), 48)
    return output.getvalue()


def create_pdf_report(run):
    """Return a readable PDF report as bytes using saved run metadata and evidence."""
    payload = run.get("payload") or {}
    output = BytesIO()
    doc = SimpleDocTemplate(
        output, pagesize=landscape(A4), rightMargin=14*mm, leftMargin=14*mm,
        topMargin=13*mm, bottomMargin=13*mm, title=str(run.get("title", "Product research report"))
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("ReportTitle", parent=styles["Title"], alignment=TA_CENTER, fontSize=18, leading=22)
    body_style = ParagraphStyle("SmallBody", parent=styles["BodyText"], fontSize=8, leading=10, wordWrap="CJK")
    story = [
        Paragraph(escape(str(run.get("title", "Product research report"))), title_style),
        Spacer(1, 5*mm),
        Paragraph(f"<b>Research type:</b> {escape(str(run.get('run_type', 'Unknown')))}", body_style),
        Paragraph(f"<b>Saved at (UTC):</b> {escape(str(run.get('created_at', 'Unknown')))}", body_style),
        Paragraph(f"<b>History ID:</b> {escape(str(run.get('id', '')))}", body_style),
        Spacer(1, 4*mm),
        Paragraph("Research summary", styles["Heading2"]),
    ]
    summary_data = [["Field", "Value"]]
    summary_data.extend([[Paragraph(escape(str(k)), body_style), Paragraph(escape(str(v)), body_style)] for k, v in _summary_rows(run)[4:]])
    summary_table = Table(summary_data, colWidths=[45*mm, 215*mm], repeatRows=1)
    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#26364a")),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("GRID", (0,0), (-1,-1), 0.35, colors.HexColor("#c8ced6")),
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor("#f3f6f9")]),
        ("LEFTPADDING", (0,0), (-1,-1), 5),
        ("RIGHTPADDING", (0,0), (-1,-1), 5),
    ]))
    story.extend([summary_table, Spacer(1, 5*mm)])
    items = payload.get("items")
    if isinstance(items, list) and items and all(isinstance(item, dict) for item in items):
        story.append(Paragraph("Product candidates / evidence", styles["Heading2"]))
        columns = list(dict.fromkeys(key for item in items for key in item.keys()))
        columns = columns[:8]
        table_data = [[Paragraph(f"<b>{escape(str(col))}</b>", body_style) for col in columns]]
        for item in items[:100]:
            table_data.append([
                Paragraph(escape(str(item.get(col, "")))[:500], body_style) for col in columns
            ])
        col_width = 260*mm / max(len(columns), 1)
        result_table = Table(table_data, colWidths=[col_width]*len(columns), repeatRows=1)
        result_table.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#26364a")),
            ("TEXTCOLOR", (0,0), (-1,0), colors.white),
            ("GRID", (0,0), (-1,-1), 0.3, colors.HexColor("#c8ced6")),
            ("VALIGN", (0,0), (-1,-1), "TOP"),
            ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor("#f3f6f9")]),
            ("LEFTPADDING", (0,0), (-1,-1), 3),
            ("RIGHTPADDING", (0,0), (-1,-1), 3),
        ]))
        story.extend([result_table, Spacer(1, 4*mm)])
    story.append(Paragraph(
        "<b>Interpretation:</b> Trend indices and video engagement are research signals only. "
        "They do not prove sales, actual demand, supplier reliability, profitability, or virality. "
        "Check source data, landed costs, competitors, and suppliers before making a business decision.",
        body_style,
    ))
    doc.build(story)
    return output.getvalue()

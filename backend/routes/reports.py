from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import io

from server import db, get_current_user

router = APIRouter()


# NOTE: Workbook KPIs are implemented as simple exports for demo.
KPI_DEFS = [
    {
        "module": "Sales",
        "name": "Outstanding Receivables",
        "description": "Pending customer dues",
        "frequency": "Daily",
        "audience": "Director",
    },
    {
        "module": "Sales",
        "name": "Sales by Product",
        "description": "Product-wise sales",
        "frequency": "Monthly",
        "audience": "Management",
    },
    {
        "module": "Inventory",
        "name": "Stock Aging",
        "description": "Old stock analysis",
        "frequency": "Weekly",
        "audience": "Inventory Head",
    },
    {
        "module": "Production",
        "name": "Scrap %",
        "description": "Production wastage",
        "frequency": "Daily",
        "audience": "Production Head",
    },
    {
        "module": "QC",
        "name": "Failure Trend",
        "description": "QC failure analysis",
        "frequency": "Weekly",
        "audience": "QC Head",
    },
]


@router.get("/kpis")
async def list_kpis(current_user: dict = Depends(get_current_user)):
    return {"kpis": KPI_DEFS}


@router.get("/export")
async def export_kpis(format: str = "xlsx", current_user: dict = Depends(get_current_user)):
    """Download KPI list as XLSX or PDF (demo)."""
    fmt = (format or "xlsx").lower()

    if fmt == "xlsx":
        try:
            from openpyxl import Workbook
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"openpyxl not available: {e}")

        wb = Workbook()
        ws = wb.active
        ws.title = "Reports_KPIs"
        ws.append(["Module", "Report/KPI", "Description", "Frequency", "Audience"])
        for k in KPI_DEFS:
            ws.append([k["module"], k["name"], k["description"], k["frequency"], k["audience"]])

        bio = io.BytesIO()
        wb.save(bio)
        bio.seek(0)

        filename = f"kpis_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.xlsx"
        return StreamingResponse(
            bio,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

    if fmt == "pdf":
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.pdfgen import canvas
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"reportlab not available: {e}")

        bio = io.BytesIO()
        c = canvas.Canvas(bio, pagesize=A4)
        width, height = A4

        y = height - 50
        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, y, "Reports / KPIs")
        y -= 25
        c.setFont("Helvetica", 10)

        headers = ["Module", "KPI", "Frequency", "Audience"]
        c.drawString(50, y, " | ".join(headers))
        y -= 15
        c.line(50, y, width - 50, y)
        y -= 15

        for k in KPI_DEFS:
            row = [k["module"], k["name"], k["frequency"], k["audience"]]
            c.drawString(50, y, " | ".join(row)[:120])
            y -= 14
            if y < 60:
                c.showPage()
                y = height - 50
                c.setFont("Helvetica", 10)

        c.showPage()
        c.save()
        bio.seek(0)

        filename = f"kpis_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.pdf"
        return StreamingResponse(
            bio,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

    raise HTTPException(status_code=400, detail="Invalid format; use xlsx or pdf")

import csv
import io
from typing import Optional

from fastapi import FastAPI, UploadFile, File
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from report import build_report, render_html

app = FastAPI(title="AI Trade Compliance Copilot (MVP)")

# In-memory store of the most recent batch so /report can render it.
LAST_REPORTS = []


class Product(BaseModel):
    sku: Optional[str] = None
    description: str
    material: Optional[str] = None
    origin: Optional[str] = None
    customs_value: Optional[float] = None
    current_hs_code: Optional[str] = None


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/classify")
def classify(product: Product):
    report = build_report(product.model_dump())
    global LAST_REPORTS
    LAST_REPORTS = [report]
    return report


@app.post("/classify/batch")
def classify_batch(products: list[Product]):
    reports = [build_report(p.model_dump()) for p in products]
    global LAST_REPORTS
    LAST_REPORTS = reports
    return reports


@app.post("/upload")
async def upload_csv(file: UploadFile = File(...)):
    """Upload a CSV with columns: sku, description, material, origin,
    customs_value, current_hs_code (only description is required)."""
    raw = (await file.read()).decode("utf-8-sig")
    rows = list(csv.DictReader(io.StringIO(raw)))

    reports = []
    for row in rows:
        product = {
            "sku": row.get("sku"),
            "description": row.get("description", ""),
            "material": row.get("material") or None,
            "origin": row.get("origin") or None,
            "customs_value": float(row["customs_value"]) if row.get("customs_value") else None,
            "current_hs_code": row.get("current_hs_code") or None,
        }
        reports.append(build_report(product))

    global LAST_REPORTS
    LAST_REPORTS = reports
    return {"count": len(reports), "reports": reports}


@app.get("/report", response_class=HTMLResponse)
def report_html():
    if not LAST_REPORTS:
        return HTMLResponse("<p>No reports yet. POST to /classify, "
                            "/classify/batch, or /upload first.</p>")
    return HTMLResponse(render_html(LAST_REPORTS))

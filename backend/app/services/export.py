"""Serialize weather requests into downloadable formats.

Each format returns `(bytes, media_type, filename)` so routers can set
Content-Type and Content-Disposition without duplicating the logic.
"""

from __future__ import annotations

import csv
import io
import json
from datetime import UTC, datetime
from typing import Any, Literal
from xml.etree import ElementTree as ET

from app.branding import APP_NAME, AUTHOR_NAME
from app.models import WeatherRequest

ExportFormat = Literal["json", "csv", "xml", "md", "pdf"]
SUPPORTED_FORMATS: tuple[ExportFormat, ...] = ("json", "csv", "xml", "md", "pdf")

_FILENAME_STEM = "weather-requests"


def _record_to_dict(req: WeatherRequest) -> dict[str, Any]:
    return {
        "id": req.id,
        "notes": req.notes,
        "start_date": req.start_date.isoformat(),
        "end_date": req.end_date.isoformat(),
        "created_at": req.created_at.isoformat() if req.created_at else None,
        "updated_at": req.updated_at.isoformat() if req.updated_at else None,
        "location": {
            "id": req.location.id,
            "display_name": req.location.display_name,
            "lat": req.location.lat,
            "lon": req.location.lon,
            "country": req.location.country,
            "region": req.location.region,
            "timezone": req.location.timezone,
            "source": req.location.source,
        },
        "daily": [
            {
                "date": row.date.isoformat(),
                "temp_min": row.temp_min,
                "temp_max": row.temp_max,
                "temp_mean": row.temp_mean,
                "precipitation_sum": row.precipitation_sum,
                "weather_code": row.weather_code,
            }
            for row in req.daily
        ],
    }


def _filename(fmt: ExportFormat) -> str:
    stamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    return f"{_FILENAME_STEM}-{stamp}.{fmt}"


def to_json(records: list[WeatherRequest]) -> tuple[bytes, str, str]:
    payload = {
        "app": APP_NAME,
        "author": AUTHOR_NAME,
        "exported_at": datetime.now(UTC).isoformat(),
        "records": [_record_to_dict(r) for r in records],
    }
    return (
        json.dumps(payload, indent=2).encode("utf-8"),
        "application/json",
        _filename("json"),
    )


def to_csv(records: list[WeatherRequest]) -> tuple[bytes, str, str]:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        [
            "request_id",
            "location",
            "lat",
            "lon",
            "country",
            "region",
            "timezone",
            "date",
            "temp_min",
            "temp_max",
            "temp_mean",
            "precipitation_sum",
            "weather_code",
            "notes",
        ]
    )
    for req in records:
        loc = req.location
        if not req.daily:
            writer.writerow(
                [
                    req.id,
                    loc.display_name,
                    loc.lat,
                    loc.lon,
                    loc.country or "",
                    loc.region or "",
                    loc.timezone or "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    req.notes or "",
                ]
            )
            continue
        for row in req.daily:
            writer.writerow(
                [
                    req.id,
                    loc.display_name,
                    loc.lat,
                    loc.lon,
                    loc.country or "",
                    loc.region or "",
                    loc.timezone or "",
                    row.date.isoformat(),
                    _n(row.temp_min),
                    _n(row.temp_max),
                    _n(row.temp_mean),
                    _n(row.precipitation_sum),
                    _n(row.weather_code),
                    req.notes or "",
                ]
            )
    return buffer.getvalue().encode("utf-8"), "text/csv", _filename("csv")


def _n(value: Any) -> Any:
    return "" if value is None else value


def to_xml(records: list[WeatherRequest]) -> tuple[bytes, str, str]:
    root = ET.Element("weather_requests", attrib={"app": APP_NAME, "author": AUTHOR_NAME})
    for req in records:
        rec = ET.SubElement(root, "request", attrib={"id": str(req.id)})
        ET.SubElement(rec, "start_date").text = req.start_date.isoformat()
        ET.SubElement(rec, "end_date").text = req.end_date.isoformat()
        if req.notes:
            ET.SubElement(rec, "notes").text = req.notes
        loc = req.location
        location_el = ET.SubElement(
            rec,
            "location",
            attrib={"lat": str(loc.lat), "lon": str(loc.lon)},
        )
        ET.SubElement(location_el, "display_name").text = loc.display_name
        if loc.country:
            ET.SubElement(location_el, "country").text = loc.country
        if loc.region:
            ET.SubElement(location_el, "region").text = loc.region
        if loc.timezone:
            ET.SubElement(location_el, "timezone").text = loc.timezone
        daily_el = ET.SubElement(rec, "daily")
        for row in req.daily:
            day = ET.SubElement(daily_el, "day", attrib={"date": row.date.isoformat()})
            for key, val in (
                ("temp_min", row.temp_min),
                ("temp_max", row.temp_max),
                ("temp_mean", row.temp_mean),
                ("precipitation_sum", row.precipitation_sum),
                ("weather_code", row.weather_code),
            ):
                if val is not None:
                    ET.SubElement(day, key).text = str(val)
    ET.indent(root, space="  ")
    return (
        b'<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(root, encoding="utf-8"),
        "application/xml",
        _filename("xml"),
    )


def to_markdown(records: list[WeatherRequest]) -> tuple[bytes, str, str]:
    lines: list[str] = [f"# {APP_NAME} — weather requests", f"_Author: {AUTHOR_NAME}_", ""]
    if not records:
        lines.append("_No records._")
    for req in records:
        loc = req.location
        lines.append(f"## {loc.display_name}")
        lines.append(
            f"- **Range:** {req.start_date.isoformat()} → {req.end_date.isoformat()}"
        )
        lines.append(f"- **Coordinates:** {loc.lat}, {loc.lon}")
        if loc.country:
            lines.append(f"- **Country:** {loc.country}")
        if req.notes:
            lines.append(f"- **Notes:** {req.notes}")
        lines.append("")
        if req.daily:
            lines.append("| Date | Min °C | Max °C | Mean °C | Precip (mm) | Code |")
            lines.append("|---|---|---|---|---|---|")
            for row in req.daily:
                cells = " | ".join(
                    _md(v)
                    for v in (
                        row.date.isoformat(),
                        row.temp_min,
                        row.temp_max,
                        row.temp_mean,
                        row.precipitation_sum,
                        row.weather_code,
                    )
                )
                lines.append(f"| {cells} |")
        lines.append("")
    body = "\n".join(lines).encode("utf-8")
    return body, "text/markdown; charset=utf-8", _filename("md")


def _md(value: Any) -> str:
    return "–" if value is None else str(value)


def to_pdf(records: list[WeatherRequest]) -> tuple[bytes, str, str]:
    # Importing lazily so a reportlab-less dev install still loads the module.
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import (
        PageBreak,
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        title=f"{APP_NAME} — Weather Requests",
        author=AUTHOR_NAME,
        leftMargin=36,
        rightMargin=36,
        topMargin=48,
        bottomMargin=36,
    )
    styles = getSampleStyleSheet()
    story: list[Any] = [
        Paragraph(f"<b>{APP_NAME}</b> — Weather Requests", styles["Title"]),
        Paragraph(
            f"Author: {AUTHOR_NAME} &nbsp;·&nbsp; "
            f"Exported: {datetime.now(UTC).strftime('%Y-%m-%d %H:%M UTC')}",
            styles["Normal"],
        ),
        Spacer(1, 12),
    ]
    if not records:
        story.append(Paragraph("<i>No records.</i>", styles["Normal"]))

    for i, req in enumerate(records):
        loc = req.location
        story.append(Paragraph(f"<b>{loc.display_name}</b>", styles["Heading2"]))
        story.append(
            Paragraph(
                f"Range: {req.start_date.isoformat()} → {req.end_date.isoformat()}",
                styles["Normal"],
            )
        )
        story.append(Paragraph(f"Coordinates: {loc.lat}, {loc.lon}", styles["Normal"]))
        if req.notes:
            story.append(Paragraph(f"Notes: {req.notes}", styles["Normal"]))
        story.append(Spacer(1, 6))
        if req.daily:
            table_data: list[list[Any]] = [
                ["Date", "Min °C", "Max °C", "Mean °C", "Precip (mm)", "Code"]
            ]
            for row in req.daily:
                table_data.append(
                    [
                        row.date.isoformat(),
                        _pdfv(row.temp_min),
                        _pdfv(row.temp_max),
                        _pdfv(row.temp_mean),
                        _pdfv(row.precipitation_sum),
                        _pdfv(row.weather_code),
                    ]
                )
            table = Table(table_data, hAlign="LEFT")
            table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E5E7EB")),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#9CA3AF")),
                        ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
                        ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ]
                )
            )
            story.append(table)
        story.append(Spacer(1, 12))
        if i < len(records) - 1:
            story.append(PageBreak())

    doc.build(story)
    return buffer.getvalue(), "application/pdf", _filename("pdf")


def _pdfv(value: Any) -> str:
    return "—" if value is None else str(value)


def export(fmt: ExportFormat, records: list[WeatherRequest]) -> tuple[bytes, str, str]:
    dispatch = {
        "json": to_json,
        "csv": to_csv,
        "xml": to_xml,
        "md": to_markdown,
        "pdf": to_pdf,
    }
    if fmt not in dispatch:
        raise ValueError(f"Unsupported format: {fmt}")
    return dispatch[fmt](records)

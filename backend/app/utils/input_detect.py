"""Classify a free-text location query into a routable input type.

The detector is intentionally forgiving: it checks the strongest signals first
(coordinates, then common postal-code shapes), falling back to free text.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

InputKind = Literal["coordinates", "postal_code", "free_text"]


_COORD_RE = re.compile(
    r"""
    ^\s*
    (?P<lat>-?\d{1,3}(?:\.\d+)?)
    \s*[,\s]\s*
    (?P<lon>-?\d{1,3}(?:\.\d+)?)
    \s*$
    """,
    re.VERBOSE,
)

# Postal-code shapes we want to recognise explicitly. Each entry maps a
# regex to an ISO 3166-1 alpha-2 country code hint for Nominatim.
_POSTAL_PATTERNS: tuple[tuple[re.Pattern[str], str | None], ...] = (
    (re.compile(r"^\s*(?P<code>\d{5}(?:-\d{4})?)\s*$"), "us"),   # US ZIP / ZIP+4
    (re.compile(r"^\s*(?P<code>[A-Za-z]\d[A-Za-z][ -]?\d[A-Za-z]\d)\s*$"), "ca"),  # Canada
    (re.compile(
        r"^\s*(?P<code>GIR\s*0AA|[A-Za-z]{1,2}\d[A-Za-z\d]?\s*\d[A-Za-z]{2})\s*$"
    ), "gb"),  # UK
    (re.compile(r"^\s*(?P<code>\d{6})\s*$"), "in"),              # India PIN
    (re.compile(r"^\s*(?P<code>\d{4})\s*$"), None),              # Generic 4-digit
)


@dataclass(frozen=True)
class DetectedInput:
    kind: InputKind
    raw: str
    lat: float | None = None
    lon: float | None = None
    postal_code: str | None = None
    country_hint: str | None = None


def _valid_coord(lat: float, lon: float) -> bool:
    return -90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0


def detect_input(raw: str) -> DetectedInput:
    """Return the detected kind and parsed fields for the query string."""
    if not raw or not raw.strip():
        return DetectedInput(kind="free_text", raw="")
    text = raw.strip()

    m = _COORD_RE.match(text)
    if m:
        try:
            lat = float(m.group("lat"))
            lon = float(m.group("lon"))
        except ValueError:
            pass
        else:
            if _valid_coord(lat, lon):
                return DetectedInput(kind="coordinates", raw=text, lat=lat, lon=lon)

    for pattern, country in _POSTAL_PATTERNS:
        pm = pattern.match(text)
        if pm:
            return DetectedInput(
                kind="postal_code",
                raw=text,
                postal_code=pm.group("code").upper().replace(" ", ""),
                country_hint=country,
            )

    return DetectedInput(kind="free_text", raw=text)

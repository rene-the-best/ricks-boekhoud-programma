import re

import categorize

MAANDEN = {
    "januari": 1, "februari": 2, "maart": 3, "april": 4, "mei": 5, "juni": 6,
    "juli": 7, "augustus": 8, "september": 9, "oktober": 10, "november": 11, "december": 12,
}


def parse_loonstrook_pdf(pdf_bytes: bytes) -> dict:
    import io

    import pdfplumber

    text_parts = []
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            text_parts.append(page.extract_text() or "")
    text = "\n".join(text_parts)
    return parse_loonstrook_text(text, source="loonstrook.pdf")


def _money(text: str) -> float | None:
    m = re.search(r"€?\s*([0]?\d{1,3}(?:\.\d{3})*|\d+),(\d{2})", text)
    if not m:
        return None
    return float(m.group(1).replace(".", "") + "." + m.group(2))


def parse_loonstrook_text(text: str, source: str = "") -> dict:
    lowered = text.lower()
    fields = {
        "period": "",
        "brutoloon": None,
        "loonheffing": None,
        "pensioen": None,
        "vakantiegeld": None,
        "source": source,
    }
    for maand, nummer in MAANDEN.items():
        if maand in lowered:
            year_m = re.search(rf"{maand}\s*(20\d\d)", lowered)
            if year_m:
                fields["period"] = f"{year_m.group(1)}-{nummer:02d}"
            break
    year_m = re.search(r"(20\d\d)[-./](1[0-2]|0?[1-9])", text)
    if not fields["period"] and year_m:
        fields["period"] = f"{year_m.group(1)}-{int(year_m.group(2)):02d}"

    brutoline = re.search(r"(?:loon\s*heffingsloon|belastbaar\s*loon|bruto[^0-9\n]{0,20}loon)([€\s\d.,]*)", lowered)
    if brutoline:
        fields["brutoloon"] = _money(brutoline.group(1))
    m = re.search(r"(?:ingehouden\s*loonheffing|loonheffing)[^0-9€\n]{0,40}(€?\s*[\d.,]+,\d{2})", lowered)
    if m:
        fields["loonheffing"] = _money(m.group(1))
    m = re.search(r"(?:pensioenpremie|pensioen)[^0-9€\n]{0,40}(€?\s*[\d.,]+,\d{2})", lowered)
    if m:
        fields["pensioen"] = _money(m.group(1))
    m = re.search(r"vakantiegeld[^0-9€\n]{0,40}(€?\s*[\d.,]+,\d{2})", lowered)
    if m:
        fields["vakantiegeld"] = _money(m.group(1))
    return fields

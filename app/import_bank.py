import csv
import io
import re
import xml.etree.ElementTree as ET
from datetime import datetime

import categorize


def parse_any(filename: str, data: bytes) -> tuple[list[dict], str]:
    text = None
    for enc in ("utf-8-sig", "utf-8", "latin-1"):
        try:
            text = data.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    name = filename.lower()
    if name.endswith(".xml") or (text and "<Document" in text and "camt" in text[:500]):
        return parse_camt(data), "CAMT.053 (XML)"
    if name.endswith(".sta") or name.endswith(".940") or name.endswith(".mt940") or (
        text and text.lstrip().startswith(":20:")
    ):
        return parse_mt940(text or ""), "MT940"
    return parse_csv_auto(text or ""), "CSV"


def _norm_date(value: str) -> str:
    value = value.strip().strip('"')
    for fmt in ("%Y-%m-%d", "%Y%m%d", "%d-%m-%Y", "%d-%m-%y", "%d/%m/%Y", "%d/%m/%y", "%d.%m.%Y"):
        try:
            return datetime.strptime(value, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    raise ValueError(f"Onbekende datumnotatie: {value!r}")


def _num(value: str) -> float:
    value = value.replace("€", "").replace("EUR", "").strip()
    if "," in value and "." in value:
        if value.rfind(",") > value.rfind("."):
            value = value.replace(".", "").replace(",", ".")
        else:
            value = value.replace(",", "")
    elif "," in value:
        value = value.replace(",", ".")
    return float(re.sub(r"[^0-9.\-]", "", value))


def parse_camt(data: bytes) -> list[dict]:
    root = _safe_xml(data)
    rows = []
    for ntry in root.iter():
        if not ntry.tag.endswith("}Ntry"):
            continue
        amount = 0.0
        cdt = "DBIT"
        date = ""
        desc_parts: list[str] = []
        contra = ""
        account = ""
        for el in ntry.iter():
            tag = el.tag.rsplit("}", 1)[-1]
            if tag == "Amt" and not amount:
                amount = _num(el.text or "0")
            elif tag == "CdtDbtInd":
                cdt = el.text or "DBIT"
            elif tag == "Dt" and not date:
                date = (el.text or "")[:10]
            elif tag == "AddtlNtryInf":
                desc_parts.append(el.text or "")
            elif tag == "Ustrd":
                desc_parts.append(el.text or "")
            elif tag == "IBAN":
                if not account:
                    account = el.text or ""
                else:
                    contra = contra or el.text or ""
        sign = -1 if cdt == "DBIT" else 1
        description = ", ".join(p.strip() for p in desc_parts if p.strip()) or "Bankafschrift"
        if not date:
            for el in ntry.iter():
                if el.tag.endswith("}Dt"):
                    date = (el.text or "")[:10]
                    break
        category, kind = categorize.apply(description)
        rows.append({
            "date": date or "1970-01-01",
            "description": description,
            "contra": contra,
            "amount": round(sign * amount, 2),
            "account": account,
            "category": category,
            "kind": kind if sign < 0 else "inkomsten",
        })
    return rows


def _safe_xml(data: bytes) -> ET.Element:
    return ET.fromstring(data)


def parse_mt940(text: str) -> list[dict]:
    rows: list[dict] = []
    lines = text.replace("\r\n", "\n").split("\n")
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith(":61:"):
            body = line[4:]
            m = re.match(r"^(\d{6})(\d{4})?([CD])((?:\d{1,3}\.)*\d+(?:,\d{1,2})?)", body)
            if m:
                yy = m.group(1)[:2]
                mmdd = m.group(1)[2:6]
                date = f"20{yy}-{mmdd[:2]}-{mmdd[2:4]}"
                sign = -1 if m.group(3) == "D" else 1
                amount = round(sign * _num(m.group(4)), 2)
                desc = ""
                if i + 1 < len(lines) and lines[i + 1].strip().startswith(":86:"):
                    j = i + 2
                    desc_lines = [lines[i + 1].strip()[4:]]
                    while j < len(lines) and not lines[j].strip().startswith(":"):
                        desc_lines.append(lines[j].strip())
                        j += 1
                    desc = "".join(desc_lines)
                else:
                    j = i + 1
                    parts = []
                    # :61: may inline transaction details after codecs
                    rest = body[m.end():]
                    parts.append(rest.split("//")[0])
                    while j < len(lines) and not lines[j].strip().startswith(":"):
                        parts.append(lines[j].strip())
                        j += 1
                    desc = "".join(parts)
                rows.append(_mt_row(date, desc, amount))
                i = i + 1
                continue
        i += 1
    return rows


def _mt_row(date: str, raw: str, amount: float) -> dict:
    contra = ""
    name = ""
    desc = ""
    m_iban = re.search(r"/IBAN/([A-Z0-9]+)", raw)
    if m_iban:
        contra = m_iban.group(1)
    m_name = re.search(r"/NAME/([^/\n]*)", raw)
    if m_name:
        name = m_name.group(1)
    m_remi = re.search(r"/REMI/([^/\n]*[/A-Za-z0-9 ]*)", raw)
    if m_remi:
        desc = m_remi.group(1)
    m_trtp = re.search(r"/TRTP/([^/\n]*)", raw)
    if m_trtp:
        desc = f"{desc} {m_trtp.group(1)}".strip()
    description = ", ".join([p for p in (name, desc) if p]) or raw[:80] or "Bankafschrift"
    category, kind = categorize.apply(description)
    if amount >= 0:
        kind = "inkomsten"
    return {
        "date": date,
        "description": description,
        "contra": contra,
        "amount": amount,
        "account": "",
        "category": category,
        "kind": kind,
    }


DATE_HEADERS = {"datum", "date", "valutadatum", "datumtijd", "boekdatum", "transactiedatum", "afrekendatum"}
DESC_HEADERS = {"naam / omschrijving", "naam/omschrijving", "omschrijving", "beschrijving", "description", "mutatie", "mutatiesoort", "naam"}
AMT_HEADERS = {"bedrag (eur)", "bedrag", "amount", "bedrag (klasse)", "af bij bedrag"}
AFBIJ_HEADERS = {"af/by", "af bij", "af/bij", "bij/af", "debet/credit", "af of bij"}
CONTRA_HEADERS = {"tegenrekening", "iban", "rekening", "tegenrekening iban/bban", "tegenrekeningiban"}


def parse_csv_auto(text: str) -> list[dict]:
    sample = text[:4000]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=";,")
    except csv.Error:
        class dialect:  # type: ignore
            delimiter = ";"
    reader = csv.reader(io.StringIO(text), dialect)
    rows_raw = [r for r in reader if any(c.strip() for c in r)]
    if not rows_raw:
        return []
    header_idx = 0
    for idx, r in enumerate(rows_raw[:5]):
        lowered = [c.lower().strip() for c in r]
        if any(h in DATE_HEADERS for h in lowered) and any(h in AMT_HEADERS for h in lowered):
            header_idx = idx
            break
    header = [c.lower().strip() for c in rows_raw[header_idx]]
    col = {name: header.index(name) for name in header}
    date_col = next((col[h] for h in header if h in DATE_HEADERS), None)
    amt_col = next((col[h] for h in header if h in AMT_HEADERS), None)
    if date_col is None or amt_col is None:
        raise ValueError("Kolommen 'datum' en 'bedrag' niet gevonden in CSV-header")
    desc_cols = [col[h] for h in header if h in DESC_HEADERS]
    afbij_col = next((col[h] for h in header if h in AFBIJ_HEADERS), None)
    contra_col = next((col[h] for h in header if h in CONTRA_HEADERS), None)
    other_cols = [i for i in range(len(header))
                  if i not in {date_col, amt_col, contra_col, afbij_col}
                  and not any(k in header[i] for k in ("saldo", "code", "munt", "bic", "volgnr", "valuta"))]
    rows = []
    for r in rows_raw[header_idx + 1:]:
        if len(r) <= max(date_col, amt_col):
            continue
        try:
            date = _norm_date(r[date_col])
        except ValueError:
            continue
        try:
            amount = _num(r[amt_col])
        except ValueError:
            continue
        desc_pieces = [r[i] for i in desc_cols + other_cols if i < len(r) and r[i].strip()]
        description = " | ".join(dict.fromkeys(desc_pieces)) or "Bankafschrift"
        if afbij_col is not None and afbij_col < len(r):
            if "af" in r[afbij_col].lower() and "bij" not in r[afbij_col].lower():
                amount = -abs(amount)
            elif "bij" in r[afbij_col].lower():
                amount = abs(amount)
        contra = r[contra_col] if contra_col is not None and contra_col < len(r) else ""
        category, kind = categorize.apply(description)
        rows.append({
            "date": date,
            "description": description[:200],
            "contra": contra.strip(),
            "amount": round(amount, 2),
            "account": "",
            "category": category,
            "kind": "inkomsten" if amount >= 0 else kind,
        })
    return rows

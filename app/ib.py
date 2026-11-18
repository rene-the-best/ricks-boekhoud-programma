import csv
import io

import db


def eur(value: float) -> str:
    s = f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"€ {s}"


def compute_year(year: str) -> dict:
    loon = sum(r["brutoloon"] or 0 for r in db.q(
        "SELECT brutoloon FROM loonstroken WHERE period LIKE ?", (f"{year}-%",)))
    loonheffing = sum(r["loonheffing"] or 0 for r in db.q(
        "SELECT loonheffing FROM loonstroken WHERE period LIKE ?", (f"{year}-%",)))
    vakantiegeld = sum(r["vakantiegeld"] or 0 for r in db.q(
        "SELECT vakantiegeld FROM loonstroken WHERE period LIKE ?", (f"{year}-%",)))

    hypotheek = [r["amount"] for r in db.q(
        "SELECT amount FROM transactions WHERE category='Woning / Hypotheek' AND substr(tx_date,1,4)=?",
        (year,))]
    hypotheek_norm = abs(sum(a for a in hypotheek if a < 0)) - sum(a for a in hypotheek if a > 0)

    forfait = float(db.get_setting(f"eigenwoningforfait_{year}", "0") or 0)
    hypotheekrente_handmatig = db.get_setting(f"hypotheekrente_{year}", "")
    hypotheekrente = float(hypotheekrente_handmatig.replace(",", ".")) if hypotheekrente_handmatig \
        else hypotheek_norm

    overig_inkomen = db.q(
        "SELECT COALESCE(SUM(amount),0) s FROM transactions "
        "WHERE amount>0 AND category<>'Inkomsten' AND substr(tx_date,1,4)=? AND kind='inkomsten'",
        (year,))
    zou = overig_inkomen[0]["s"]

    box1_rows = [
        ("Loon en pensioen (loonstroken)", loon),
        ("Vakantiegeld / jaarbodem", vakantiegeld),
        ("Overig inkomen (bankafschriften)", zou),
        ("Eigenwoningforfait", -abs(forfait)),
        ("Hypotheekrenteaftrek", -abs(hypotheekrente)),
        ("Loonheffing / heffingskorting", -abs(loonheffing)),
    ]
    box1_total = sum(v for _, v in box1_rows)

    saldo = float(db.get_setting(f"beginsaldo_{year}", "0") or 0)
    for r in db.q(
        "SELECT COALESCE(SUM(amount),0) s FROM transactions WHERE substr(tx_date,1,4)<=?",
        (year,)):
        saldo += r["s"]
    schulden = float(db.get_setting(f"schulden_{year}", "0") or 0)
    box3_rows = [
        ("Bank- en spaartegoeden (eindsaldo 31-12)", saldo),
        ("Schulden", -abs(schulden)),
    ]
    box3_total = sum(v for _, v in box3_rows)

    return {
        "year": year,
        "box1": box1_rows,
        "box1_total": box1_total,
        "box3": box3_rows,
        "box3_total": box3_total,
        "loonstroken_count": len(db.q(
            "SELECT id FROM loonstroken WHERE period LIKE ?", (f"{year}-%",))),
        "tx_count": len(db.q(
            "SELECT id FROM transactions WHERE substr(tx_date,1,4)=?", (year,))),
    }


def export_csv(result: dict) -> str:
    buf = io.StringIO()
    writer = csv.writer(buf, delimiter=";")
    writer.writerow(["Rick's Boekhoud Programma — IB-uitwerking", result["year"]])
    writer.writerow([])
    writer.writerow(["BOX I", "Bedrag (EUR)"])
    for label, value in result["box1"]:
        writer.writerow([label, f"{value:.2f}".replace(".", ",")])
    writer.writerow(["Totaal Box I", f"{result['box1_total']:.2f}".replace(".", ",")])
    writer.writerow([])
    writer.writerow(["BOX III", "Bedrag (EUR)"])
    for label, value in result["box3"]:
        writer.writerow([label, f"{value:.2f}".replace(".", ",")])
    writer.writerow(["Totaal Box III", f"{result['box3_total']:.2f}".replace(".", ",")])
    writer.writerow([])
    writer.writerow(["Let op", "Indicatieve berekening. Vul de officiële aangifte met deze cijfers als aandachtspunten; geen belastingadvies."])
    return buf.getvalue()


def export_transactions_csv(year: str) -> str:
    buf = io.StringIO()
    writer = csv.writer(buf, delimiter=";")
    writer.writerow(["Datum", "Omschrijving", "Tegenrekening", "Bedrag (EUR)", "Categorie", "Type"])
    for r in db.q(
        "SELECT tx_date, description, contra_account, amount, category, kind "
        "FROM transactions WHERE substr(tx_date,1,4)=? ORDER BY tx_date", (year,)):
        writer.writerow([
            r["tx_date"], r["description"], r["contra_account"],
            f"{r['amount']:.2f}".replace(".", ","), r["category"], r["kind"],
        ])
    return buf.getvalue()

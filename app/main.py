import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from nicegui import app as nicegui_app
from nicegui import ui

import categorize
import db as dbm
import ib
import import_bank
import import_loon

GREEN = "#00FF9D"
BLUE = "#3B82F6"
TEXT = "#D9E6F7"
MUTED = "#7E97B8"
CARD = "#13294B"
PANEL = "#0F2240"
BORDER = "#1C3A63"
RED = "#FF5D73"

MENU = [
    ("/", "Dashboard"),
    ("/transacties", "Transacties"),
    ("/import", "Import / Upload"),
    ("/kosten", "Kosteninzicht"),
    ("/loon", "Loonstrookjes"),
    ("/ib", "IB-aangifte"),
    ("/rapporten", "Rapporten"),
    ("/instellingen", "Instellingen"),
]

YEARS = ["2024", "2025", "2026"]


def eur(value: float) -> str:
    s = f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"€ {s}"


def scaffold(active: str):
    ui.add_head_html(f"""
    <style>
      body {{ background: {PANEL} !important; }}
      .q-drawer {{ background: #0B1B30 !important; border-right: 1px solid {BORDER} !important; }}
      .q-header {{ background: #0A1522 !important; }}
      .q-table {{ background: {CARD} !important; }}
    </style>
    """)
    ui.dark_mode(True)
    with ui.left_drawer(value=True, fixed=True, elevated=False).classes("w-56"):
        with ui.column().classes("gap-1 pt-2"):
            with ui.row().classes("items-center gap-2 mb-4 px-2"):
                ui.icon("account_balance").classes(f"text-[{GREEN}]")
                ui.label("RICK'S BOEKHOUD").classes(f"text-[{GREEN}] font-bold")
            for path, label in MENU:
                if path == active:
                    ui.button(label, icon="chevron_right", on_click=lambda p=path: ui.navigate.to(p)) \
                        .props(f'flat no-caps align=left').classes(
                        f"w-full text-[{GREEN}] font-semibold bg-[#153055] border border-[{GREEN}]")
                else:
                    ui.button(label, icon=None, on_click=lambda p=path: ui.navigate.to(p)) \
                        .props("flat no-caps align=left").classes("w-full text-[#D9E6F7]")
    with ui.header().classes("items-center justify-between h-12"):
        ui.label("Rick's Boekhoud Programma").classes("font-bold")
        ui.label(f"Lokaal versleuteld — SQLite").classes(f"text-[{GREEN}] text-xs")


def kpi_card(label: str, value: str, sub: str = "", color: str = TEXT):
    with ui.card().classes(f"bg-[{CARD}] border border-[{BORDER}] no-shadow min-w-[200px] flex-1") \
            .style("border-radius:10px"):
        ui.label(label).classes("text-xs text-[#7E97B8] tracking-wider")
        ui.label(value).classes("text-2xl font-bold mt-1")
        if sub:
            ui.label(sub).classes("text-xs").style(f"color:{color}")


def panel(title: str):
    with ui.card().classes(f"w-full bg-[{CARD}] border border-[{BORDER}] no-shadow") \
            .style("border-radius:10px"):
        ui.label(title).classes("font-bold text-base mb-1")
        return ui.column().classes("w-full gap-0")


# ------------------------- lock screen -------------------------

@ui.page("/lock")
def lock_page(set_new: bool = False):
    ui.add_head_html(f"<style>body{{background:{PANEL} !important;}}</style>")
    ui.dark_mode(True)
    with ui.column().classes("absolute-center items-center gap-4"):
        ui.icon("lock").classes("text-6xl").style(f"color:{GREEN}")
        ui.label("Rick's Boekhoud Programma").classes("text-2xl font-bold")
        if set_new or not dbm.has_master():
            ui.label("Stel een hoofdwachtwoord in. Dit versleutelt al je data lokaal (AES-256).") \
                .classes("text-sm text-[#7E97B8]")
            pw1 = ui.input("Nieuw hoofdwachtwoord", password=True, password_toggle_button=True) \
                .classes("w-72")
            pw2 = ui.input("Herhaal hoofdwachtwoord", password=True, password_toggle_button=True) \
                .classes("w-72")

            def create():
                if len(pw1.value) < 8:
                    ui.notify("Kies minimaal 8 tekens.", type="warning")
                    return
                if pw1.value != pw2.value:
                    ui.notify("Wachtwoorden zijn niet gelijk.", type="warning")
                    return
                dbm.create_master(pw1.value)
                ui.notify("Versleutelde databank aangemaakt.", type="positive")
                ui.navigate.to("/")
            ui.button("Start", on_click=create).props("unelevated").classes("w-72").style(
                f"background:{GREEN};color:#062318")
        else:
            ui.label("Voer je hoofdwachtwoord in om de databank te openen.") \
                .classes("text-sm text-[#7E97B8]")
            pw = ui.input("Hoofdwachtwoord", password=True, password_toggle_button=True).classes("w-72")

            def unlock():
                if dbm.unlock(pw.value):
                    ui.notify("Databank geopend.", type="positive")
                    ui.navigate.to("/")
                else:
                    ui.notify("Verkeerd wachtwoord.", type="negative")
            pw.on("keydown.enter", unlock)
            ui.button("Openen", on_click=unlock).props("unelevated").classes("w-72").style(
                f"background:{GREEN};color:#062318")


# ------------------------- dashboard -------------------------

@ui.page("/")
def dashboard():
    if not dbm.connected():
        ui.navigate.to("/lock")
        return
    scaffold("/")
    year_state = {"year": dbm.get_setting("huidig_jaar", "2025")}

    ui.label("Dashboard").classes("text-2xl font-bold mt-2")
    year_sel = ui.select(YEARS, value=year_state["year"], label="Belastingjaar",
                         on_change=lambda e: on_year(e.value)).classes("w-40")

    content = ui.column().classes("w-full gap-3 pb-8")

    def on_year(y):
        year_state["year"] = y
        dbm.set_setting("huidig_jaar", y)
        content.clear()
        build(content, year_state["year"])

    def build(c, year):
        y = year
        tx = dbm.q(
            "SELECT amount FROM transactions WHERE substr(tx_date,1,4)=? AND kind='inkomsten'", (y,))
        inkomen = sum(r["amount"] for r in tx)
        uitgaven = abs(sum(r["amount"] for r in dbm.q(
            "SELECT amount FROM transactions WHERE substr(tx_date,1,4)=? AND amount<0", (y,))))
        vast = dbm.q(
            "SELECT COALESCE(SUM(amount),0) s FROM transactions "
            "WHERE substr(tx_date,1,4)=? AND amount<0 AND kind='vast'", (y,))[0]["s"]
        variabel = dbm.q(
            "SELECT COALESCE(SUM(amount),0) s FROM transactions "
            "WHERE substr(tx_date,1,4)=? AND amount<0 AND kind='variabel'", (y,))[0]["s"]
        with c:
            with ui.row().classes("w-full gap-3 flex-wrap"):
                kpi_card("TOTAAL SALDO", eur(inkomen - uitgaven), "inkomsten - uitgaven", GREEN)
                kpi_card(f"INKOMMEN {y}", eur(inkomen), "loon + overig", TEXT)
                kpi_card(f"UITGAVEN {y}", eur(uitgaven), "alle kostenposten", RED)
                kpi_card(f"VASTE LASTEN P/M {y}", eur(vast / max(1, _maanden(y))),
                         f"variabel: {eur(abs(variabel) / max(1, _maanden(y)))}", MUTED)
            with ui.row().classes("w-full gap-3 flex-wrap"):
                with ui.card().classes(f"bg-[{CARD}] border border-[{BORDER}] no-shadow flex-1 min-w-[420px]") \
                        .style("border-radius:10px"):
                    ui.label("Inkomsten vs. Uitgaven per maand").classes("font-bold")
                    months = [f"{y}-{m:02d}" for m in range(1, 13)]
                    inc = [month_sum(y, m, ">0") for m in range(1, 13)]
                    out = [abs(month_sum(y, m, "<0")) for m in range(1, 13)]
                    ui.echart({
                        "backgroundColor": "transparent",
                        "grid": {"left": 50, "right": 20, "top": 30, "bottom": 30},
                        "xAxis": {"type": "category",
                                  "data": ["jan", "feb", "mrt", "apr", "mei", "jun",
                                           "jul", "aug", "sep", "okt", "nov", "dec"],
                                  "axisLabel": {"color": MUTED},
                                  "axisLine": {"lineStyle": {"color": BORDER}}},
                        "yAxis": {"type": "value", "axisLabel": {"color": MUTED},
                                  "splitLine": {"lineStyle": {"color": BORDER, "opacity": 0.5}}},
                        "series": [
                            {"name": "Inkomsten", "type": "line", "data": inc, "smooth": True,
                             "lineStyle": {"color": GREEN}, "itemStyle": {"color": GREEN},
                             "areaStyle": {"color": GREEN, "opacity": 0.12}},
                            {"name": "Uitgaven", "type": "line", "data": out, "smooth": True,
                             "lineStyle": {"color": BLUE}, "itemStyle": {"color": BLUE},
                             "areaStyle": {"color": BLUE, "opacity": 0.18}},
                        ],
                        "legend": {"textStyle": {"color": TEXT}, "top": 0},
                        "tooltip": {"trigger": "axis"},
                    }).classes("w-full h-64")
                with ui.card().classes(f"bg-[{CARD}] border border-[{BORDER}] no-shadow min-w-[320px]") \
                        .style("border-radius:10px"):
                    ui.label("Vast vs. Variabel").classes("font-bold")
                    ui.echart({
                        "backgroundColor": "transparent",
                        "series": [{
                            "type": "pie", "radius": ["55%", "80%"],
                            "label": {"color": TEXT},
                            "data": [
                                {"name": "Vast", "value": round(abs(vast), 2),
                                 "itemStyle": {"color": GREEN}},
                                {"name": "Variabel", "value": round(abs(variabel), 2),
                                 "itemStyle": {"color": BLUE}},
                            ],
                        }],
                        "legend": {"bottom": 0, "textStyle": {"color": TEXT}},
                    }).classes("w-full h-64")
            with ui.card().classes(f"bg-[{CARD}] border border-[{BORDER}] no-shadow w-full") \
                    .style("border-radius:10px"):
                ui.label(f"Grootste kostenposten {y}").classes("font-bold")
                cats = dbm.q(
                    "SELECT category, COALESCE(SUM(amount),0) s FROM transactions "
                    "WHERE substr(tx_date,1,4)=? AND amount<0 GROUP BY category ORDER BY s LIMIT 8",
                    (y,))
                labels = [r["category"] for r in cats]
                values = [abs(r["s"]) for r in cats]
                ui.echart({
                    "backgroundColor": "transparent",
                    "grid": {"left": 150, "right": 40, "top": 10, "bottom": 20},
                    "xAxis": {"type": "value", "axisLabel": {"color": MUTED},
                              "splitLine": {"show": False}},
                    "yAxis": {"type": "category", "data": labels[::-1],
                              "axisLabel": {"color": TEXT},
                              "axisLine": {"lineStyle": {"color": BORDER}}},
                    "series": [{"type": "bar", "data": values[::-1], "barWidth": 14,
                                "itemStyle": {"color": GREEN, "borderRadius": 7}}],
                    "tooltip": {"trigger": "axis"},
                }).classes("w-full h-72")

    build(content, year_state["year"])


def _maanden(year: str) -> int:
    now = dbm.stamp()
    current = int(now[:4])
    if int(year) > current:
        return 12
    if int(year) < current:
        return 12
    return max(1, int(now[5:7]))


def month_sum(year: str, month: int, direction: str) -> float:
    rows = dbm.q(
        f"SELECT COALESCE(SUM(amount),0) s FROM transactions "
        f"WHERE substr(tx_date,1,7)=? AND amount{direction}",
        (f"{year}-{month:02d}",))
    return rows[0]["s"]


# ------------------------- transacties -------------------------

@ui.page("/transacties")
def transacties():
    if not dbm.connected():
        ui.navigate.to("/lock")
        return
    scaffold("/transacties")
    ui.label("Transacties").classes("text-2xl font-bold mt-2")
    years = [r[0] for r in dbm.q("SELECT DISTINCT substr(tx_date,1,4) FROM transactions ORDER BY 1")] \
        or ["2025"]
    state = {"year": dbm.get_setting("huidig_jaar", "2025"), "cat": "", "kind": ""}
    cat_options = categorize.all_categories()
    flt_year = ui.select(years, value=state["year"], label="Jaar", on_change=lambda e: refresh()).classes("w-32")
    flt_cat = ui.select(cat_options, value=None, label="Categorie", with_input=True,
                        on_change=lambda e: refresh()).classes("w-56")
    flt_kind = ui.select(["vast", "variabel", "inkomsten"], value=None, label="Type",
                         on_change=lambda e: refresh()).classes("w-40")

    columns = [
        {"name": "datum", "label": "Datum", "field": "datum", "align": "left"},
        {"name": "omschrijving", "label": "Omschrijving", "field": "omschrijving", "align": "left"},
        {"name": "tegenrekening", "label": "Tegenrekening", "field": "tegenrekening", "align": "left"},
        {"name": "bedrag", "label": "Bedrag", "field": "bedrag", "align": "right"},
        {"name": "categorie", "label": "Categorie", "field": "categorie", "align": "left"},
        {"name": "type", "label": "Type", "field": "type", "align": "left"},
    ]

    table = ui.table(columns=columns, rows=[], row_key="id", pagination=20) \
        .classes("w-full").props("dark flat")

    def refresh():
        rows_sql = ("SELECT id, tx_date, description, contra_account, amount, category, kind "
                    "FROM transactions WHERE substr(tx_date,1,4)=?")
        params: list = [state["year"]]
        if state["cat"]:
            rows_sql += " AND category=?"
            params.append(state["cat"])
        if state["kind"]:
            rows_sql += " AND kind=?"
            params.append(state["kind"])
        data = []
        for r in dbm.q(rows_sql, tuple(params)):
            data.append({
                "id": r["id"],
                "datum": r["tx_date"],
                "omschrijving": r["description"],
                "tegenrekening": r["contra_account"],
                "bedrag": eur(r["amount"]),
                "categorie": r["category"],
                "type": r["kind"],
                "_amount": r["amount"],
            })
        table.rows = data
        table.update()

    def on_year_selected(e):
        state["year"] = e.value
        refresh()

    flt_year.on_value_change(lambda e: on_year_selected(e))
    flt_cat.on_value_change(lambda e: (state.__setitem__("cat", e.value or ""), refresh()))
    flt_kind.on_value_change(lambda e: (state.__setitem__("kind", e.value or ""), refresh()))

    def edit_row(e):
        payload = e.args[0] if isinstance(e.args, tuple) else e.args
        row = next((r for r in table.rows
                    if r["id"] == (payload if isinstance(payload, int) else payload["id"])), None)
        if not row:
            return
        with ui.dialog() as dlg, ui.card().classes(f"bg-[{PANEL}] text-[{TEXT}]"):
            ui.label("Transactie aanpassen").classes("font-bold")
            ui.label(row["omschrijving"]).classes("text-sm text-[#7E97B8]")
            cat_sel = ui.select(cat_options, value=row["categorie"]).classes("w-full")
            kind_sel = ui.select(categorize.KINDS, value=row["type"]).classes("w-full")
            def save():
                dbm.execute("UPDATE transactions SET category=?, kind=? WHERE id=?",
                            (cat_sel.value, kind_sel.value, row["id"]))
                dlg.close()
                refresh()
                ui.notify("Aangepast.", type="positive")
            with ui.row():
                ui.button("Opslaan", on_click=save).props("unelevated").style(
                    f"background:{GREEN};color:#062318")
                ui.button("Annuleren", on_click=dlg.close).props("flat")
        dlg.open()

    table.on("row-click", edit_row)
    refresh()


# ------------------------- import -------------------------

@ui.page("/import")
def import_page():
    if not dbm.connected():
        ui.navigate.to("/lock")
        return
    scaffold("/import")
    ui.label("Import / Upload").classes("text-2xl font-bold mt-2")
    with ui.row().classes("w-full gap-3 flex-wrap"):
        with ui.card().classes(f"bg-[{CARD}] border border-[{BORDER}] no-shadow flex-1 min-w-[380px]") \
                .style("border-radius:10px"):
            ui.badge("BANKBESTAND", color="transparent").style(f"color:{GREEN};background:none")
            ui.label("Importeren voor transacties").classes("text-lg font-bold")
            ui.label("CAMT.053 (XML) • CSV • MT940").classes("text-sm text-[#7E97B8]")
            upload = ui.upload(on_upload=handle_bank, multiple=True, auto_upload=True) \
                .props("accept=.xml,.csv,.sta,.940,.txt,.mt940 dark").classes("w-full mt-2")
        with ui.card().classes(f"bg-[{CARD}] border border-[{BORDER}] no-shadow flex-1 min-w-[380px]") \
                .style("border-radius:10px"):
            ui.badge("LOONSTROOK / JAARINFORMATIE", color="transparent").style(
                f"color:{BLUE};background:none")
            ui.label("PDF van je werkgever inlezen").classes("text-lg font-bold")
            ui.label("Cijfers gaan automatisch naar IB-aangifte").classes("text-sm text-[#7E97B8]")
            upload2 = ui.upload(on_upload=handle_loon, multiple=True, auto_upload=True) \
                .props("accept=.pdf dark").classes("w-full mt-2")
    ui.separator()
    with ui.card().classes(f"bg-[{CARD}] border border-[{BORDER}] no-shadow w-full") \
            .style("border-radius:10px"):
        ui.label("LAATSTE IMPORT").classes("text-xs tracking-wider text-[#7E97B8] font-bold")


def handle_bank(e):
    name = e.name
    data = e.content.read()
    try:
        rows, fmt = import_bank.parse_any(name, data)
    except Exception as ex:
        ui.notify(f"Kon bestand niet lezen ({fmt if isinstance(ex, ValueError) else 'fout'}): {ex}",
                  type="negative")
        return
    if not rows:
        ui.notify("Geen transacties gevonden in dit bestand.", type="warning")
        return
    duplicated = name
    added = dbm.insert_transactions(rows, duplicated)
    ui.notify(f"{fmt}: {len(rows)} transacties gevonden, {added} nieuw toegevoegd.",
              type="positive")


def handle_loon(e):
    name = e.name
    data = e.content.read()
    try:
        fields = import_loon.parse_loonstrook_pdf(data)
    except Exception as ex:
        ui.notify(f"Kon PDF niet lezen: {ex}", type="negative")
        return
    show_loon_dialog(name, fields)


def show_loon_dialog(name: str, fields: dict):
    with ui.dialog() as dlg, ui.card().classes(f"bg-[{PANEL}] text-[{TEXT}]"):
        ui.label("Loonstrook controleren en opslaan").classes("font-bold")
        ui.label(f"Bestand: {name}").classes("text-sm text-[#7E97B8]")
        ui.label("Controleer de waarden (uit de PDF gelezen) en pas aan indien nodig.") \
            .classes("text-xs text-[#7E97B8]")
        period = ui.input("Periode (JJJJ-MM)", value=fields["period"] or "2025-12").classes("w-full")
        brutoloon = ui.number("Brutoloon", value=fields["brutoloon"] or 0, format="%.2f").classes("w-full")
        loonheffing = ui.number("Loonheffing", value=fields["loonheffing"] or 0, format="%.2f") \
            .classes("w-full")
        pensioen = ui.number("Pensioenpremie", value=fields["pensioen"] or 0, format="%.2f").classes("w-full")
        vakantiegeld = ui.number("Vakantiegeld", value=fields["vakantiegeld"] or 0, format="%.2f") \
            .classes("w-full")
        def save():
            dbm.save_loonstrook(period.value.strip(), float(brutoloon.value or 0),
                                float(loonheffing.value or 0), float(pensioen.value or 0),
                                float(vakantiegeld.value or 0), name)
            dlg.close()
            ui.navigate.reload()
            ui.notify("Loonstrook opgeslagen.", type="positive")
        with ui.row():
            ui.button("Opslaan", on_click=save).props("unelevated").style(
                f"background:{GREEN};color:#062318")
            ui.button("Annuleren", on_click=dlg.close).props("flat")
    dlg.open()


# ------------------------- kosteninzicht -------------------------

@ui.page("/kosten")
def kosten():
    if not dbm.connected():
        ui.navigate.to("/lock")
        return
    scaffold("/kosten")
    ui.label("Kosteninzicht").classes("text-2xl font-bold mt-2")
    year = dbm.get_setting("huidig_jaar", "2025")

    with ui.card().classes(f"bg-[{CARD}] border border-[{BORDER}] no-shadow w-full") \
            .style("border-radius:10px"):
        ui.label(f"Uitgaven per categorie {year}").classes("font-bold")
        cats = dbm.q(
            "SELECT category, COALESCE(SUM(amount),0) s, kind FROM transactions "
            "WHERE substr(tx_date,1,4)=? AND amount<0 GROUP BY category ORDER BY s", (year,))
        labels = [r["category"] for r in cats]
        values = [abs(r["s"]) for r in cats]
        kleuren = [GREEN if r["kind"] == "vast" else BLUE for r in cats]
        ui.echart({
            "backgroundColor": "transparent",
            "grid": {"left": 160, "right": 40, "top": 10, "bottom": 20},
            "xAxis": {"type": "value", "axisLabel": {"color": MUTED},
                      "splitLine": {"show": False}},
            "yAxis": {"type": "category", "data": labels[::-1],
                      "axisLabel": {"color": TEXT}, "axisLine": {"lineStyle": {"color": BORDER}}},
            "series": [{"type": "bar", "data": [
                {"value": v, "itemStyle": {"color": c}} for v, c in zip(values[::-1], kleuren[::-1])
            ], "barWidth": 14, "itemStyle": {"borderRadius": 7}}],
            "tooltip": {"trigger": "axis"},
        }).classes("w-full h-[420px]")

    with ui.row().classes("w-full gap-3 flex-wrap"):
        totaal = sum(abs(r["s"]) for r in cats) if cats else 0
        with ui.card().classes(f"bg-[{CARD}] border border-[{BORDER}] no-shadow flex-1") \
                .style("border-radius:10px"):
            ui.label("Overzicht").classes("font-bold")
            for r in cats:
                pct = abs(r["s"]) / totaal * 100 if totaal else 0
                with ui.row().classes("w-full justify-between items-center"):
                    with ui.row().classes("items-center gap-2"):
                        ui.icon("circle", size="xs").style(
                            f"color:{GREEN if r['kind']=='vast' else BLUE}")
                        ui.label(r["category"]).classes("text-sm")
                    ui.label(f"{eur(abs(r['s']))} — {pct:.0f}%").classes("text-sm text-[#7E97B8]")
        with ui.card().classes(f"bg-[{CARD}] border border-[{BORDER}] no-shadow min-w-[320px]") \
                .style("border-radius:10px"):
            ui.label("Vaste lasten per maand").classes("font-bold")
            vast = dbm.q(
                "SELECT COALESCE(SUM(amount),0) s FROM transactions "
                "WHERE substr(tx_date,1,4)=? AND kind='vast' AND amount<0", (year,))[0]["s"]
            ui.label(eur(abs(vast) / max(1, _maanden(year)))).classes(
                "text-3xl font-bold mt-2").style(f"color:{GREEN}")
            ui.label("Gemiddelde over de maanden met data").classes("text-xs text-[#7E97B8]")


# ------------------------- loonstrookjes -------------------------

@ui.page("/loon")
def loon():
    if not dbm.connected():
        ui.navigate.to("/lock")
        return
    scaffold("/loon")
    ui.label("Loonstrookjes").classes("text-2xl font-bold mt-2")
    ui.label("Laad je loonstroken (PDF) in via Import / Upload — of vul hieronder handmatig aan.") \
        .classes("text-sm text-[#7E97B8]")
    with ui.card().classes(f"bg-[{CARD}] border border-[{BORDER}] no-shadow w-full") \
            .style("border-radius:10px"):
        ui.label("Handmatig loonstrook toevoegen").classes("font-bold")
        period = ui.input("Periode (JJJJ-MM)", value="2025-01")
        brutoloon = ui.number("Brutoloon", value=0, format="%.2f")
        loonheffing = ui.number("Loonheffing", value=0, format="%.2f")
        pensioen = ui.number("Pensioenpremie", value=0, format="%.2f")
        vakantiegeld = ui.number("Vakantiegeld", value=0, format="%.2f")
        def add():
            dbm.save_loonstrook(period.value.strip(), float(brutoloon.value or 0),
                                float(loonheffing.value or 0), float(pensioen.value or 0),
                                float(vakantiegeld.value or 0), "handmatig")
            ui.notify("Toegevoegd.", type="positive")
            ui.navigate.reload()
        ui.button("Toevoegen", on_click=add).props("unelevated").style(
            f"background:{GREEN};color:#062318")

    columns = [
        {"name": "period", "label": "Periode", "field": "period", "align": "left"},
        {"name": "brutoloon", "label": "Brutoloon", "field": "brutoloon", "align": "right"},
        {"name": "loonheffing", "label": "Loonheffing", "field": "loonheffing", "align": "right"},
        {"name": "pensioen", "label": "Pensioen", "field": "pensioen", "align": "right"},
        {"name": "vakantiegeld", "label": "Vakantiegeld", "field": "vakantiegeld", "align": "right"},
        {"name": "bron", "label": "Bron", "field": "bron", "align": "left"},
    ]
    data = [{
        "period": r["period"],
        "brutoloon": eur(r["brutoloon"]),
        "loonheffing": eur(r["loonheffing"]),
        "pensioen": eur(r["pensioen"]),
        "vakantiegeld": eur(r["vakantiegeld"]),
        "bron": r["source"],
    } for r in dbm.q("SELECT * FROM loonstroken ORDER BY period DESC")]
    ui.table(columns=columns, rows=data, row_key="period", pagination=12) \
        .classes("w-full").props("dark flat")


# ------------------------- IB-aangifte -------------------------

@ui.page("/ib")
def ib_page():
    if not dbm.connected():
        ui.navigate.to("/lock")
        return
    scaffold("/ib")
    ui.label("IB-aangifte — uitwerking").classes("text-2xl font-bold mt-2")
    state = {"year": dbm.get_setting("huidig_jaar", "2025")}

    def render():
        result = ib.compute_year(state["year"])
        with holder_col:
            holder_col.clear()
            with ui.row().classes("w-full gap-3 flex-wrap"):
                with ui.card().classes(f"bg-[{CARD}] border border-[{BORDER}] no-shadow flex-1 min-w-[460px]") \
                        .style("border-radius:10px"):
                    for section, rows, total in (
                            ("BOX I — Inkomsten en aftrekposten", result["box1"], result["box1_total"]),
                            ("BOX III — Vermogen (eindsaldo)", result["box3"], result["box3_total"])):
                        with ui.row().classes("items-center gap-2 mt-3"):
                            ui.icon("flag").classes("text-[#00FF9D]")
                            ui.label(section).classes("font-bold")
                        for label, value in rows:
                            with ui.row().classes("w-full justify-between items-center"):
                                ui.label(label).classes("text-sm text-[#7E97B8]")
                                ui.label(ib.eur(value)).classes("text-sm font-semibold")
                        with ui.row().classes("w-full justify-between items-center pt-1 border-t") \
                                .style(f"border-color:{BORDER} !important;"):
                            ui.label("Totaal").classes("font-bold")
                            ui.label(ib.eur(total)).classes("font-bold text-[#00FF9D]")
                    with ui.row().classes("mt-4 gap-2"):
                        def export():
                            csv_text = ib.export_csv(result)
                            ui.download(csv_text.encode("utf-8"),
                                        f"ib_uitwerking_{state['year']}.csv",
                                        "text/csv")
                        ui.button("Excel exporteren (CSV)", on_click=export).props("unelevated") \
                            .style(f"background:{GREEN};color:#062318")
                with ui.card().classes(f"bg-[{CARD}] border border-[{BORDER}] no-shadow min-w-[300px]") \
                        .style("border-radius:10px"):
                    ui.label("VERWERKTE BRONNEN").classes("text-xs tracking-wider text-[#7E97B8] font-bold")
                    with ui.row().classes("w-full justify-between"):
                        ui.label("Loonstroken").classes("text-sm")
                        ui.label(f"{result['loonstroken_count']}").classes("text-sm font-bold")
                    with ui.row().classes("w-full justify-between"):
                        ui.label("Bankafschriften (regels)").classes("text-sm")
                        ui.label(f"{result['tx_count']}").classes("text-sm font-bold")
                    ui.label("Tips voor januari").classes("font-bold mt-3")
                    for tip in ("Laad december-afschriften in vóór de uitwerking",
                                "Vul eigenwoningforfait in bij Instellingen",
                                "Controleer de categorie 'Woning / Hypotheek'"):
                        ui.label(f"• {tip}").classes("text-xs text-[#7E97B8]")

    holder_col = ui.column().classes("w-full")
    year_sel = ui.select(YEARS, value=state["year"], label="Belastingjaar",
                         on_change=lambda e: (state.__setitem__("year", e.value), render())) \
        .classes("w-40")
    render()


# ------------------------- rapporten -------------------------

@ui.page("/rapporten")
def rapporten():
    if not dbm.connected():
        ui.navigate.to("/lock")
        return
    scaffold("/rapporten")
    ui.label("Rapporten & Export").classes("text-2xl font-bold mt-2")
    with ui.card().classes(f"bg-[{CARD}] border border-[{BORDER}] no-shadow w-full max-w-2xl") \
            .style("border-radius:10px"):
        ui.label("Transacties exported").classes("font-bold")
        ui.label("Alle transacties van het gekozen jaar naar CSV (Excel-compatibel).") \
            .classes("text-sm text-[#7E97B8]")
        year_sel = ui.select(YEARS, value=dbm.get_setting("huidig_jaar", "2025")).classes("w-40")

        def export_tx():
            csv_text = ib.export_transactions_csv(year_sel.value)
            ui.download(csv_text.encode("utf-8"),
                        f"transacties_{year_sel.value}.csv", "text/csv")
            ui.notify("Transacties geëxporteerd.", type="positive")
        ui.button("Download transacties CSV", on_click=export_tx).props("unelevated") \
            .style(f"background:{GREEN};color:#062318")


# ------------------------- instellingen -------------------------

@ui.page("/instellingen")
def instellingen():
    if not dbm.connected():
        ui.navigate.to("/lock")
        return
    scaffold("/instellingen")
    ui.label("Instellingen").classes("text-2xl font-bold mt-2")
    year = dbm.get_setting("huidig_jaar", "2025")

    with ui.card().classes(f"bg-[{CARD}] border border-[{BORDER}] no-shadow w-full max-w-2xl") \
            .style("border-radius:10px"):
        ui.label("Belasting-instellingen per jaar").classes("font-bold")
        ui.label("Deze waarde gebruikt de IB-uitwerking (Box I en Box III).") \
            .classes("text-sm text-[#7E97B8]")
        for y in YEARS:
            forfait = ui.number(f"Eigenwoningforfait {y} (€)",
                                value=float(dbm.get_setting(f"eigenwoningforfait_{y}", "0") or 0),
                                format="%.2f").classes("w-64")
            hypo = ui.number(f"Hypotheekrenteaftrek {y} (leeg = automatisch uit bankafschriften)",
                             value=dbm.get_setting(f"hypotheekrente_{y}", "") or None,
                             format="%.2f").classes("w-64")
            beginsaldo = ui.number(f"Beginsaldo banktegoeden op 1-1-{y} (€)",
                                   value=float(dbm.get_setting(f"beginsaldo_{y}", "0") or 0),
                                   format="%.2f").classes("w-64")
            schulden = ui.number(f"Schulden per 31-12-{y} (€)",
                                 value=float(dbm.get_setting(f"schulden_{y}", "0") or 0),
                                 format="%.2f").classes("w-64")
            def save_slot(y=y, forfait=forfait, hypo=hypo, beginsaldo=beginsaldo, schulden=schulden):
                dbm.set_setting(f"eigenwoningforfait_{y}", str(forfait.value or 0))
                dbm.set_setting(f"hypotheekrente_{y}", "" if hypo.value is None else str(hypo.value))
                dbm.set_setting(f"beginsaldo_{y}", str(beginsaldo.value or 0))
                dbm.set_setting(f"schulden_{y}", str(schulden.value or 0))
                ui.notify(f"Instellingen {y} opgeslagen.", type="positive")
            ui.button(f"Opslaan {y}", on_click=save_slot).props("unelevated").classes("mt-1") \
                .style(f"background:{GREEN};color:#062318")

    with ui.card().classes(f"bg-[{CARD}] border border-[{BORDER}] no-shadow w-full max-w-2xl") \
            .style("border-radius:10px"):
        ui.label("Data & Privacy").classes("font-bold")
        ui.label(f"Databank: {dbm.APP_DIR / 'data.enc'}").classes("text-xs break-all text-[#7E97B8]")
        ui.label("Je data staat versleuteld (AES-256 via Fernet, PBKDF2 300k iteraties) in je eigen "
                 "gebruikersmap. Er wordt niets naar het internet gestuurd.") \
            .classes("text-sm text-[#7E97B8]")

        def backup():
            if dbm.DATA_ENC.exists():
                ui.download(dbm.DATA_ENC.read_bytes(), "back-up-boekhouding.enc", "application/octet-stream")
            else:
                ui.notify("Geen databank gevonden.", type="warning")
        ui.button("Back-up downloaden (versleuteld)", on_click=backup).props("outline")


@nicegui_app.on_shutdown
def on_shutdown():
    dbm.lock_down()


def main() -> None:
    if "-no-native" in sys.argv:
        ui.run(title="Rick's Boekhoud Programma", host="127.0.0.1", dark=True,
               reload=False, port=8080, show=False, storage_secret="boekhoud-secret")
    else:
        ui.run(title="Rick's Boekhoud Programma", host="127.0.0.1", dark=True,
               native=True, window_size=(1280, 720), reload=False, show=False,
               storage_secret="boekhoud-secret")


if __name__ in {"__main__", "__mp_main__"}:
    main()

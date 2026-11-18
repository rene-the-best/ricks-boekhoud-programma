import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

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
STRIPE = "#0F2240"
PANEL = "#0A1522"
DARK = "#081220"
BORDER = "#1C3A63"
RED = "#FF5D73"
ACCENT_BG = "#153055"
SIDEBAR = "#0B1B30"
FONT = ("Segoe UI", 9)

MENU = [
    ("Dashboard", "dashboard"),
    ("Transacties", "transacties"),
    ("Import / Upload", "import"),
    ("Kosteninzicht", "kosten"),
    ("Spaarpotjes", "potjes"),
    ("Loonstrookjes", "loon"),
    ("IB-aangifte", "ib"),
    ("Rapporten", "rapporten"),
    ("Instellingen", "instellingen"),
]

YEARS = ["2024", "2025", "2026"]


def eur(value: float) -> str:
    s = f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"€ {s}"


def _num(text: str) -> float:
    t = (text or "").strip().replace("€", "").replace(" ", "")
    if "," in t:
        t = t.replace(".", "").replace(",", ".")
    try:
        return float(t or "0")
    except ValueError:
        return 0.0


def _clean_canvas(canvas: tk.Canvas):
    canvas.delete("all")
    for ch in canvas.winfo_children():
        ch.destroy()


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Rick's Boekhoud Programma")
        self.geometry("1300x760")
        self.minsize(1120, 660)
        self.configure(bg=DARK)
        self.menu_buttons: dict[str, tk.Button] = {}
        self.content = None
        self.status_label = None
        self.show_lock()

    # ---------------- statusbalk ----------------
    def notify(self, msg: str, color: str = GREEN):
        try:
            if self.status_label is not None and self.status_label.winfo_exists():
                self.status_label.configure(text="●  " + msg, fg=color)
        except Exception:
            pass

    # ---------------- lock / hoofdwachtwoord ----------------
    def show_lock(self, set_new: bool | None = None):
        for w in self.winfo_children():
            w.destroy()
        frame = tk.Frame(self, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
        frame.place(relx=0.5, rely=0.5, anchor="center")
        inner = tk.Frame(frame, bg=CARD)
        inner.pack(padx=44, pady=32)
        tk.Label(inner, text="◉", font=("Segoe UI", 22, "bold"), fg=GREEN, bg=CARD).pack()
        tk.Label(inner, text="RICK'S BOEKHOUD PROGRAMMA", font=("Segoe UI", 16, "bold"),
                 fg=TEXT, bg=CARD).pack(pady=(2, 0))
        tk.Label(inner, text="v2.0 — professioneel, lokaal, versleuteld", font=("Segoe UI", 8),
                 fg=MUTED, bg=CARD).pack(pady=(0, 12))
        set_new = set_new if set_new is not None else not dbm.has_master()
        if set_new:
            tk.Label(inner, text="Stel een hoofdwachtwoord in.\nDit versleutelt al je data lokaal (AES-256).",
                     fg=MUTED, bg=CARD, font=FONT, justify="left").pack(pady=(0, 10))
            pw1 = tk.Entry(inner, show="●", width=32, bg=DARK, fg=TEXT, insertbackground=GREEN,
                           relief="flat", bd=6)
            pw2 = tk.Entry(inner, show="●", width=32, bg=DARK, fg=TEXT, insertbackground=GREEN,
                           relief="flat", bd=6)
            pw1.pack(ipady=2)
            pw2.pack(pady=(6, 10), ipady=2)
            pw1.focus_set()

            def create():
                if len(pw1.get()) < 8:
                    messagebox.showwarning("Te kort", "Kies minimaal 8 tekens.")
                    return
                if pw1.get() != pw2.get():
                    messagebox.showwarning("Niet gelijk", "De wachtwoorden zijn niet gelijk.")
                    return
                dbm.create_master(pw1.get())
                self.notify("Databank aangemaakt — welkom!")
                self.show_main()
            tk.Button(inner, text="Start", command=create, bg=GREEN, fg="#062318",
                      font=("Segoe UI", 10, "bold"), relief="flat", width=30,
                      cursor="hand2").pack(ipady=3)
        else:
            tk.Label(inner, text="Voer je hoofdwachtwoord in.", fg=MUTED, bg=CARD,
                     font=FONT).pack(pady=(0, 10))
            pw = tk.Entry(inner, show="●", width=32, bg=DARK, fg=TEXT, insertbackground=GREEN,
                          relief="flat", bd=6)
            pw.pack(ipady=2)

            def unlock(event=None):
                if dbm.unlock(pw.get()):
                    self.show_main()
                else:
                    messagebox.showerror("Fout", "Verkeerd wachtwoord.")
            pw.bind("<Return>", unlock)
            tk.Button(inner, text="Openen", command=unlock, bg=GREEN, fg="#062318",
                      font=("Segoe UI", 10, "bold"), relief="flat", width=30,
                      cursor="hand2").pack(pady=(10, 0), ipady=3)
            pw.focus_set()

    # ---------------- hoofdscherm ----------------
    def show_main(self):
        for w in self.winfo_children():
            w.destroy()
        sidebar = tk.Frame(self, bg=SIDEBAR, width=232)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)
        header = tk.Frame(self, bg=PANEL, height=40)
        header.pack(side="top", fill="x")
        header.pack_propagate(False)
        tk.Label(header, text="RICK'S BOEKHOUD PROGRAMMA", font=("Segoe UI", 10, "bold"),
                 fg=TEXT, bg=PANEL).pack(side="left", padx=14)
        tk.Label(header, text="Lokaal versleuteld  —  AES-256  —  geen internet",
                 font=("Segoe UI", 9), fg=GREEN, bg=PANEL).pack(side="right", padx=14)
        self.content = tk.Frame(self, bg=PANEL)
        self.content.pack(side="right", fill="both", expand=True)
        status = tk.Frame(self, bg=DARK, height=26)
        status.pack(side="bottom", fill="x")
        status.pack_propagate(False)
        self.status_label = tk.Label(status, text="", fg=GREEN, bg=DARK,
                                     font=("Segoe UI", 8), anchor="w")
        self.status_label.pack(side="left", padx=14)
        tk.Label(status, text="Rick's Boekhoud Programma  •  v2.0", fg=MUTED, bg=DARK,
                 font=("Segoe UI", 8)).pack(side="right", padx=14)

        logo_row = tk.Frame(sidebar, bg=SIDEBAR)
        logo_row.pack(fill="x", pady=(16, 2))
        tk.Label(logo_row, text="◉", font=("Segoe UI", 16, "bold"), fg=GREEN,
                 bg=SIDEBAR).pack(side="left", padx=(18, 8))
        logo_txt = tk.Frame(logo_row, bg=SIDEBAR)
        logo_txt.pack(side="left")
        tk.Label(logo_txt, text="RICK'S", font=("Segoe UI", 11, "bold"), fg=TEXT,
                 bg=SIDEBAR).pack(anchor="w")
        tk.Label(logo_txt, text="BOEKHOUD PROGRAMMA", font=("Segoe UI", 7), fg=MUTED,
                 bg=SIDEBAR).pack(anchor="w")
        tk.Frame(sidebar, bg=BORDER, height=1).pack(fill="x", padx=10, pady=(12, 8))
        tk.Label(sidebar, text="HOOFDMENU", font=("Segoe UI", 7, "bold"), fg=MUTED,
                 bg=SIDEBAR).pack(anchor="w", padx=20, pady=(0, 4))
        for label, key in MENU:
            btn = tk.Button(sidebar, text="   " + label, anchor="w", relief="flat", bd=0,
                            font=FONT, bg=SIDEBAR, fg=TEXT, padx=10, pady=7,
                            activebackground=ACCENT_BG, activeforeground=GREEN, cursor="hand2",
                            command=lambda k=key: self.navigate(k))
            btn.pack(fill="x", padx=6, pady=1)
            self.menu_buttons[key] = btn
        tk.Frame(sidebar, bg=BORDER, height=1).pack(side="bottom", fill="x", padx=10, pady=(0, 6))
        tk.Button(sidebar, text="⏻  Vergrendelen", anchor="w", relief="flat", bd=0,
                  font=FONT, bg=SIDEBAR, fg=MUTED, padx=20, pady=6,
                  activebackground=ACCENT_BG, activeforeground=GREEN, cursor="hand2",
                  command=self.lock_now).pack(side="bottom", fill="x", padx=6, pady=(0, 8))
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.navigate("dashboard")

    def lock_now(self):
        dbm.lock_down()
        self.show_lock()

    def navigate(self, key: str):
        for k, btn in self.menu_buttons.items():
            if k == key:
                btn.configure(bg=ACCENT_BG, fg=GREEN, font=("Segoe UI", 9, "bold"))
            else:
                btn.configure(bg=SIDEBAR, fg=TEXT, font=FONT)
        for w in self.content.winfo_children():
            w.destroy()
        self.status_label.configure(text="")
        page = {
            "dashboard": self.page_dashboard,
            "transacties": self.page_transacties,
            "import": self.page_import,
            "kosten": self.page_kosten,
            "potjes": self.page_potjes,
            "loon": self.page_loon,
            "ib": self.page_ib,
            "rapporten": self.page_rapporten,
            "instellingen": self.page_instellingen,
        }[key]
        page(self.content)

    # ---------------- kleine bouwstenen ----------------
    def title_bar(self, parent, title, subtitle="", right=""):
        top = tk.Frame(parent, bg=PANEL)
        top.pack(fill="x", padx=16, pady=(14, 6))
        tk.Label(top, text=title, font=("Segoe UI", 16, "bold"), fg=TEXT, bg=PANEL).pack(side="left")
        if subtitle:
            tk.Label(top, text=subtitle, font=("Segoe UI", 9), fg=MUTED, bg=PANEL) \
                .pack(side="left", padx=14)
        if right:
            tk.Label(top, text=right, font=("Segoe UI", 9, "bold"), fg=GREEN, bg=PANEL) \
                .pack(side="right")
        return top

    def card(self, parent, **pack):
        frame = tk.Frame(parent, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
        frame.pack(**pack)
        return frame

    def kpi(self, parent, label, value, sub="", color=GREEN):
        box = self.card(parent)
        box.pack(side="left", fill="both", expand=True, padx=6, pady=6)
        box.configure(padx=14, pady=10)
        tk.Label(box, text=label.upper(), font=("Segoe UI", 7, "bold"), fg=MUTED, bg=CARD) \
            .pack(anchor="w")
        tk.Label(box, text=value, font=("Segoe UI", 17, "bold"), fg=TEXT, bg=CARD) \
            .pack(anchor="w", pady=(2, 0))
        if sub:
            tk.Label(box, text=sub, font=("Segoe UI", 8), fg=color, bg=CARD).pack(anchor="w")
        return box

    def green_button(self, parent, text, command, **pack):
        btn = tk.Button(parent, text=text, command=command, bg=GREEN, fg="#062318",
                        font=("Segoe UI", 9, "bold"), relief="flat", padx=16, pady=6,
                        activebackground="#00c47c", activeforeground="#062318", cursor="hand2")
        btn.pack(**pack)
        return btn

    def outline_button(self, parent, text, command, fg=TEXT, **pack):
        btn = tk.Button(parent, text=text, command=command, bg=DARK, fg=fg,
                        font=("Segoe UI", 8, "bold"), relief="flat", padx=12, pady=5,
                        activebackground=ACCENT_BG, activeforeground=GREEN,
                        highlightbackground=BORDER, highlightthickness=1, cursor="hand2")
        btn.pack(**pack)
        return btn

    def combo(self, parent, values, width=8, initial=""):
        box = ttk.Combobox(parent, values=values, width=width, state="readonly")
        if initial:
            box.set(initial)
        return box

    def form_entry(self, parent, label, initial="", width=24):
        tk.Label(parent, text=label, font=("Segoe UI", 8), fg=MUTED, bg=parent["bg"]) \
            .pack(anchor="w", padx=16, pady=(6, 0))
        e = tk.Entry(parent, width=width, bg=DARK, fg=TEXT, insertbackground=GREEN,
                     relief="flat", bd=5)
        if initial:
            e.insert(0, initial)
        e.pack(anchor="w", padx=16, ipady=2)
        return e

    def table(self, parent, columns_def, **pack):
        wrap = tk.Frame(parent, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
        wrap.pack(fill="both", expand=True, padx=16, pady=8, **pack)
        cols = tuple(c[0] for c in columns_def)
        tree = ttk.Treeview(wrap, columns=cols, show="headings", selectmode="browse")
        for cid, text, width, anchor in columns_def:
            tree.heading(cid, text=text)
            tree.column(cid, width=width, anchor=anchor)
        scrollbar = ttk.Scrollbar(wrap, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        style_table(tree)
        return wrap, tree

    # ---------------- pagina: dashboard ----------------
    def page_dashboard(self, root):
        year = dbm.get_setting("huidig_jaar", "2025")
        self.title_bar(root, "Dashboard", "Overzicht van je boekhouding", right=f"Belastingjaar {year}")
        inkomen = ib.month_income(year)
        uitgaven = ib.month_spend(year)
        vast = ib.month_vast(year)
        variabel = ib.month_variabel(year)
        maanden = ib.maanden_met_data(year)
        beginsaldo = float(dbm.get_setting(f"beginsaldo_{year}", "0") or 0)
        bank = beginsaldo + dbm.q(
            "SELECT COALESCE(SUM(amount),0) s FROM transactions WHERE substr(tx_date,1,4)<=?",
            (year,))[0]["s"]
        potjes = dbm.potjes_total()
        row = tk.Frame(root, bg=PANEL)
        row.pack(fill="x", padx=10)
        self.kpi(row, "Totaal saldo (bank − potjes)", eur(bank - potjes),
                 f"bank {eur(bank)}  •  potjes {eur(potjes)}", GREEN)
        self.kpi(row, f"Inkomsten {year}", eur(inkomen), "loon + overig")
        self.kpi(row, f"Uitgaven {year}", eur(uitgaven), "alle kostenposten", RED)
        self.kpi(row, f"Vaste lasten p/m {year}", eur(vast / max(1, maanden)),
                 f"variabel: {eur(abs(variabel) / max(1, maanden))}", BLUE)
        self.kpi(row, "Spaarpotjes totaal", eur(potjes), "opzij gezet", GREEN)

        charts_row = tk.Frame(root, bg=PANEL)
        charts_row.pack(fill="both", expand=True, padx=10, pady=6)
        c1 = self.card(charts_row)
        c1.pack(side="left", fill="both", expand=True, padx=6)
        tk.Label(c1, text="Inkomsten vs. Uitgaven per maand", font=("Segoe UI", 10, "bold"),
                 fg=TEXT, bg=CARD).pack(anchor="w", padx=14, pady=(10, 0))
        canvas_line = tk.Canvas(c1, bg=CARD, highlightthickness=0, height=230)
        canvas_line.pack(fill="both", expand=True, padx=10, pady=6)
        draw_line_chart(canvas_line, year)
        canvas_line.bind("<Configure>", lambda e: draw_line_chart(canvas_line, year))

        c2 = self.card(charts_row)
        c2.pack(side="left", fill="y", padx=6)
        c2.configure(width=340)
        tk.Label(c2, text="Vast vs. Variabel", font=("Segoe UI", 10, "bold"), fg=TEXT,
                 bg=CARD).pack(anchor="w", padx=14, pady=(10, 0))
        canvas_donut = tk.Canvas(c2, bg=CARD, highlightthickness=0, height=200, width=320)
        canvas_donut.pack(padx=10, pady=6)
        draw_donut(canvas_donut, abs(vast), abs(variabel))
        canvas_donut.bind("<Configure>",
                          lambda e: draw_donut(canvas_donut, abs(vast), abs(variabel)))

        c3 = self.card(root)
        c3.pack(fill="both", expand=True, padx=16, pady=(0, 12))
        tk.Label(c3, text=f"Grootste kostenposten {year}", font=("Segoe UI", 10, "bold"),
                 fg=TEXT, bg=CARD).pack(anchor="w", padx=14, pady=(10, 0))
        canvas_bar = tk.Canvas(c3, bg=CARD, highlightthickness=0, height=180)
        canvas_bar.pack(fill="both", expand=True, padx=10, pady=6)
        draw_top_categories(canvas_bar, year)
        canvas_bar.bind("<Configure>", lambda e: draw_top_categories(canvas_bar, year))

    # ---------------- pagina: transacties ----------------
    def page_transacties(self, root):
        self.title_bar(root, "Transacties", "Spatie = afletteren  •  dubbelklik = aanpassen")
        controls = tk.Frame(root, bg=PANEL)
        controls.pack(fill="x", padx=16, pady=4)
        years = [r[0] for r in dbm.q(
            "SELECT DISTINCT substr(tx_date,1,4) FROM transactions ORDER BY 1")] or ["2025"]
        tk.Label(controls, text="Jaar", fg=MUTED, bg=PANEL, font=FONT).pack(side="left")
        year_box = self.combo(controls, years, 6)
        year_box.set(dbm.get_setting("huidig_jaar", "2025"))
        if year_box.get() not in years:
            years.insert(0, year_box.get())
            year_box.configure(values=years)
        year_box.pack(side="left", padx=(6, 16))
        tk.Label(controls, text="Categorie", fg=MUTED, bg=PANEL, font=FONT).pack(side="left")
        cat_box = self.combo(controls, ["(alle)"] + categorize.all_categories(), 20, "(alle)")
        cat_box.pack(side="left", padx=(6, 16))
        tk.Label(controls, text="Type", fg=MUTED, bg=PANEL, font=FONT).pack(side="left")
        kind_box = self.combo(controls, ["(alle)", "vast", "variabel", "inkomsten"], 9, "(alle)")
        kind_box.pack(side="left", padx=6)
        alleen_open = tk.BooleanVar(value=False)
        tk.Checkbutton(controls, text="Alleen niet-afgeletterd", variable=alleen_open,
                       command=lambda: refresh(), bg=PANEL, fg=TEXT, font=FONT,
                       activebackground=PANEL, activeforeground=GREEN, selectcolor=ACCENT_BG,
                       relief="flat", cursor="hand2").pack(side="left", padx=18)

        actions = tk.Frame(controls, bg=PANEL)
        actions.pack(side="right")
        self.outline_button(actions, "☑  Alles afletteren",
                            lambda: set_all(True)).pack(side="left", padx=4)
        self.outline_button(actions, "☐  Alles niet-afletteren",
                            lambda: set_all(False)).pack(side="left", padx=4)

        _, table = self.table(root, [
            ("vink", "", 40, "center"),
            ("datum", "Datum", 90, "w"),
            ("omschrijving", "Omschrijving", 290, "w"),
            ("tegenrekening", "Tegenrekening", 150, "w"),
            ("bedrag", "Bedrag", 110, "e"),
            ("categorie", "Categorie", 160, "w"),
            ("type", "Type", 90, "e"),
        ])

        status = tk.Label(root, text="", fg=MUTED, bg=PANEL, font=FONT, anchor="w")
        status.pack(fill="x", padx=18)

        def refresh():
            jaar = year_box.get()
            cat = "" if cat_box.get() == "(alle)" else cat_box.get()
            kind = "" if kind_box.get() == "(alle)" else kind_box.get()
            table.delete(*table.get_children())
            sql = ("SELECT id, tx_date, description, contra_account, amount, category, kind, "
                   "afletterd FROM transactions WHERE substr(tx_date,1,4)=?")
            params: list = [jaar]
            if cat:
                sql += " AND category=?"
                params.append(cat)
            if kind:
                sql += " AND kind=?"
                params.append(kind)
            if alleen_open.get():
                sql += " AND afletterd=0"
            sql += " ORDER BY tx_date DESC"
            total_out = 0.0
            n_done = 0
            rows = dbm.q(sql, tuple(params))
            for i, r in enumerate(rows):
                done = bool(r["afletterd"])
                vink = "✔" if done else ""
                values = (vink, r["tx_date"], r["description"][:56],
                          r["contra_account"][:20], eur(r["amount"]), r["category"], r["kind"])
                if done:
                    base_tag = "done"
                elif r["amount"] >= 0:
                    base_tag = "in"
                else:
                    base_tag = "out"
                tags = [base_tag]
                if i % 2 == 1:
                    tags.append("stripe")
                table.insert("", "end", iid=str(r["id"]), values=values, tags=tuple(tags))
                if done:
                    n_done += 1
                if r["amount"] < 0 and not done:
                    total_out += r["amount"]
            n_open = len(rows) - n_done
            status.config(text=f"{len(rows)} transacties  •  afgeletterd: {n_done}  •  "
                               f"open: {n_open}  •  openstaande uitgaven: {eur(total_out)}")

        def set_all(value: bool):
            jaar = year_box.get()
            dbm.set_afletterd_all(jaar, value)
            self.notify(f"Alle transacties van {jaar} afgeletterd" if value
                        else f"Alle vinkjes van {jaar} gewist")
            refresh()

        def toggle_selected(event=None):
            sel = table.selection()
            for iid in sel:
                dbm.toggle_afletterd(int(iid))
            if sel:
                self.notify("Afletteren bijgewerkt")
            refresh()
            return "break"

        year_box.bind("<<ComboboxSelected>>", lambda e: refresh())
        cat_box.bind("<<ComboboxSelected>>", lambda e: refresh())
        kind_box.bind("<<ComboboxSelected>>", lambda e: refresh())
        table.bind("<space>", toggle_selected)
        table.bind("<Double-1>", lambda e: edit(e))
        refresh()

        def edit(event):
            sel = table.selection()
            if not sel:
                return
            tx_id = sel[0]
            row = dbm.q("SELECT * FROM transactions WHERE id=?", (int(tx_id),))[0]
            dialog = tk.Toplevel(self)
            dialog.title("Transactie aanpassen")
            dialog.configure(bg=CARD)
            dialog.geometry("440x340")
            dialog.transient(self)
            tk.Label(dialog, text=row["description"][:56], fg=MUTED, bg=CARD,
                     font=("Segoe UI", 9), wraplength=380).pack(anchor="w", padx=16, pady=(16, 4))
            tk.Label(dialog, text="Datum: " + row["tx_date"] + "    Bedrag: " + eur(row["amount"]),
                     fg=TEXT, bg=CARD, font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=16)
            tk.Label(dialog, text="Categorie", fg=MUTED, bg=CARD, font=("Segoe UI", 8)) \
                .pack(anchor="w", padx=16, pady=(14, 0))
            cat_sel = ttk.Combobox(dialog, values=categorize.all_categories(),
                                   state="readonly", width=28)
            cat_sel.set(row["category"])
            cat_sel.pack(anchor="w", padx=16)
            tk.Label(dialog, text="Type", fg=MUTED, bg=CARD, font=("Segoe UI", 8)) \
                .pack(anchor="w", padx=16, pady=(10, 0))
            kind_sel = ttk.Combobox(dialog, values=categorize.KINDS, state="readonly", width=28)
            kind_sel.set(row["kind"])
            kind_sel.pack(anchor="w", padx=16)
            af_var = tk.BooleanVar(value=bool(row["afletterd"]))
            tk.Checkbutton(dialog, text="Afgeletterd (vinkje)", variable=af_var, bg=CARD,
                           fg=TEXT, font=("Segoe UI", 9, "bold"), activebackground=CARD,
                           activeforeground=GREEN, selectcolor=DARK, relief="flat",
                           cursor="hand2").pack(anchor="w", padx=16, pady=(14, 0))

            def save():
                dbm.execute(
                    "UPDATE transactions SET category=?, kind=?, afletterd=? WHERE id=?",
                    (cat_sel.get(), kind_sel.get(), 1 if af_var.get() else 0, int(tx_id)))
                dialog.destroy()
                self.notify("Wijziging bewaard")
                refresh()
            self.green_button(dialog, "Opslaan", save).pack(pady=16)

    # ---------------- pagina: import ----------------
    def page_import(self, root):
        self.title_bar(root, "Import / Upload",
                       "Bankbestand (CAMT.053 / CSV / MT940) en loonstroken (PDF)")
        row = tk.Frame(root, bg=PANEL)
        row.pack(fill="x", padx=16, pady=6)
        c1 = self.card(row)
        c1.pack(side="left", fill="both", expand=True, padx=6, ipady=16, ipadx=10)
        tk.Label(c1, text="BANKBESTAND", font=("Segoe UI", 8, "bold"), fg=GREEN, bg=CARD) \
            .pack(anchor="w", padx=16)
        tk.Label(c1, text="Importeren voor transacties", font=("Segoe UI", 12, "bold"),
                 fg=TEXT, bg=CARD).pack(anchor="w", padx=16, pady=(2, 0))
        tk.Label(c1, text="CAMT.053 (XML)  |  CSV  |  MT940 — dubbele regels worden herkend",
                 font=("Segoe UI", 9), fg=MUTED, bg=CARD).pack(anchor="w", padx=16)
        self.green_button(c1, "Bestand kiezen...", self.pick_bank).pack(anchor="w", padx=16, pady=(14, 0))

        c2 = self.card(row)
        c2.pack(side="left", fill="both", expand=True, padx=6, ipady=16, ipadx=10)
        tk.Label(c2, text="LOONSTROOK / JAARINFORMATIE", font=("Segoe UI", 8, "bold"),
                 fg=BLUE, bg=CARD).pack(anchor="w", padx=16)
        tk.Label(c2, text="PDF van je werkgever inlezen", font=("Segoe UI", 12, "bold"),
                 fg=TEXT, bg=CARD).pack(anchor="w", padx=16, pady=(2, 0))
        tk.Label(c2, text="Cijfers gaan automatisch naar de IB-aangifte", font=("Segoe UI", 9),
                 fg=MUTED, bg=CARD).pack(anchor="w", padx=16)
        self.green_button(c2, "PDF kiezen...", self.pick_loon).pack(anchor="w", padx=16, pady=(14, 0))

        c3 = self.card(root)
        c3.pack(fill="both", expand=True, padx=16, pady=8)
        tk.Label(c3, text="WERKWIJZE", font=("Segoe UI", 8, "bold"), fg=MUTED, bg=CARD) \
            .pack(anchor="w", padx=16, pady=(10, 2))
        for tip in ("1.  Kies je bankbestand — transacties verschijnen op de pagina Transacties.",
                    "2.  Vink af wat je hebt gecontroleerd (spatiebalk of dubbelklik).",
                    "3.  Laad je loonstrook-PDF in voor de IB-uitwerking."):
            tk.Label(c3, text=tip, font=("Segoe UI", 9), fg=TEXT, bg=CARD) \
                .pack(anchor="w", padx=16, pady=1)

    def pick_bank(self):
        paths = filedialog.askopenfilenames(
            parent=self, title="Kies bankbestand(en)",
            filetypes=[("Bankbestanden", "*.xml *.csv *.sta *.940 *.txt"), ("Alle bestanden", "*.*")])
        totaal = nieuw = 0
        for path in paths:
            with open(path, "rb") as f:
                data = f.read()
            try:
                rows, fmt = import_bank.parse_any(os.path.basename(path), data)
            except Exception as ex:
                messagebox.showerror("Fout", f"Kan {os.path.basename(path)} niet lezen:\n{ex}", parent=self)
                continue
            nieuw += dbm.insert_transactions(rows, os.path.basename(path))
            totaal += len(rows)
        if totaal:
            messagebox.showinfo("Import klaar",
                                f"{totaal} transacties gevonden,\n{nieuw} nieuw toegevoegd.\n\n"
                                f"Controleer en vink af op de pagina Transacties.", parent=self)
            self.notify(f"Import: {nieuw} nieuw van {totaal} transacties")
            self.navigate("transacties")

    def pick_loon(self):
        path = filedialog.askopenfilename(
            parent=self, title="Kies loonstrook (PDF)",
            filetypes=[("PDF", "*.pdf"), ("Alle bestanden", "*.*")])
        if not path:
            return
        with open(path, "rb") as f:
            data = f.read()
        try:
            fields = import_loon.parse_loonstrook_pdf(data)
        except Exception as ex:
            messagebox.showerror("Fout", f"Kan PDF niet lezen:\n{ex}", parent=self)
            return
        self.loon_dialog(os.path.basename(path), fields)

    def loon_dialog(self, name: str, fields: dict):
        dialog = tk.Toplevel(self)
        dialog.title("Loonstrook controleren en opslaan")
        dialog.configure(bg=CARD)
        dialog.geometry("440x440")
        dialog.transient(self)
        tk.Label(dialog, text="Bestand: " + name, fg=MUTED, bg=CARD,
                 font=("Segoe UI", 9)).pack(anchor="w", padx=16, pady=(16, 0))
        tk.Label(dialog, text="Controleer de waarden (uit de PDF gelezen)\nen pas aan indien nodig.",
                 fg=TEXT, bg=CARD, font=("Segoe UI", 10, "bold"), justify="left") \
            .pack(anchor="w", padx=16, pady=(4, 8))
        entries = {}
        for key, label in (("period", "Periode (JJJJ-MM)"), ("brutoloon", "Brutoloon"),
                           ("loonheffing", "Loonheffing"), ("pensioen", "Pensioenpremie"),
                           ("vakantiegeld", "Vakantiegeld")):
            entries[key] = self.form_entry(dialog, label,
                                           "" if fields.get(key) is None else str(fields.get(key)), 28)

        def save():
            try:
                dbm.save_loonstrook(
                    entries["period"].get().strip(),
                    _num(entries["brutoloon"].get()),
                    _num(entries["loonheffing"].get()),
                    _num(entries["pensioen"].get()),
                    _num(entries["vakantiegeld"].get()),
                    name)
            except ValueError:
                messagebox.showerror("Fout", "Bedragen moeten getallen zijn.", parent=self)
                return
            dialog.destroy()
            self.notify("Loonstrook opgeslagen")
            self.navigate("loon")
        self.green_button(dialog, "Opslaan", save).pack(pady=16)

    # ---------------- pagina: kosten ----------------
    def page_kosten(self, root):
        self.title_bar(root, "Kosteninzicht", "Alle kostenposten per categorie",
                       right="groen = vast  •  blauw = variabel")
        controls = tk.Frame(root, bg=PANEL)
        controls.pack(fill="x", padx=16, pady=2)
        tk.Label(controls, text="Jaar", fg=MUTED, bg=PANEL, font=FONT).pack(side="left")
        year_box = self.combo(controls, YEARS, 6, dbm.get_setting("huidig_jaar", "2025"))
        year_box.pack(side="left", padx=6)

        kpis = tk.Frame(root, bg=PANEL)
        kpis.pack(fill="x", padx=10, pady=(2, 0))
        c_chart = self.card(root)
        c_chart.pack(fill="both", expand=True, padx=16, pady=6)
        lbl = tk.Label(c_chart, text="Uitgaven per categorie", font=("Segoe UI", 10, "bold"),
                       fg=TEXT, bg=CARD)
        lbl.pack(anchor="w", padx=14, pady=(10, 0))
        canvas = tk.Canvas(c_chart, bg=CARD, highlightthickness=0)
        canvas.pack(fill="both", expand=True, padx=10, pady=8)

        def render():
            year = year_box.get()
            vast = abs(ib.month_vast(year))
            variabel = abs(ib.month_variabel(year))
            maanden = ib.maanden_met_data(year)
            for w in kpis.winfo_children():
                w.destroy()
            self.kpi(kpis, "Vast totaal", eur(vast), f"gem. {eur(vast / max(1, maanden))} p/m", GREEN)
            self.kpi(kpis, "Variabel totaal", eur(variabel),
                     f"gem. {eur(variabel / max(1, maanden))} p/m", BLUE)
            self.kpi(kpis, "Totaal uitgaven", eur(vast + variabel),
                     f"{maanden} maanden met data", RED)
            lbl.config(text=f"Uitgaven per categorie {year}")
            draw_categories_bar(canvas, year)
        year_box.bind("<<ComboboxSelected>>", lambda e: render())
        canvas.bind("<Configure>",
                    lambda e: draw_categories_bar(canvas, year_box.get()))
        render()

    # ---------------- pagina: spaarpotjes ----------------
    def page_potjes(self, root):
        totaal = dbm.potjes_total()
        self.title_bar(root, "Spaarpotjes", "Spaar per doel — storten, opnemen, voortgang zien")

        head = tk.Frame(root, bg=PANEL)
        head.pack(fill="x", padx=16, pady=(0, 4))
        self.green_button(head, "+  Nieuw spaarpotje",
                          self.potje_add_dialog).pack(side="right")
        sum_card = self.card(head)
        sum_card.pack(side="left", fill="x", expand=True, padx=0, ipady=8, ipadx=6)
        tk.Label(sum_card, text="TOTAAL IN SPAARPOTJES", font=("Segoe UI", 7, "bold"),
                 fg=MUTED, bg=CARD).pack(side="left", padx=14)
        tk.Label(sum_card, text=eur(totaal), font=("Segoe UI", 14, "bold"), fg=GREEN,
                 bg=CARD).pack(side="left", padx=14)
        tk.Label(sum_card, text=f"{len(dbm.potjes_list())} potjes", font=("Segoe UI", 9),
                 fg=MUTED, bg=CARD).pack(side="right", padx=14)

        scroll = tk.Canvas(root, bg=PANEL, highlightthickness=0)
        scroll.pack(fill="both", expand=True, padx=16, pady=6)
        sb = ttk.Scrollbar(root, orient="vertical", command=scroll.yview)
        sb.pack(side="right", fill="y")
        scroll.configure(yscrollcommand=sb.set)
        inner = tk.Frame(scroll, bg=PANEL)
        scroll.create_window((0, 0), window=inner, anchor="nw", width=900)

        def on_inner(e):
            scroll.configure(scrollregion=scroll.bbox("all"))
            scroll.itemconfigure("all", width=scroll.winfo_width())
        inner.bind("<Configure>", on_inner)

        potjes = dbm.potjes_list()
        if not potjes:
            empty = self.card(inner)
            empty.pack(fill="x", pady=8, ipady=24)
            tk.Label(empty, text="Nog geen spaarpotjes", font=("Segoe UI", 12, "bold"),
                     fg=TEXT, bg=CARD).pack()
            tk.Label(empty, text="Maak je eerste potje aan — bijvoorbeeld Vakantie, Reserve of "
                                 "Auto.\nSpaar er elke maand extra in bij via Storten.",
                     font=("Segoe UI", 9), fg=MUTED, bg=CARD, justify="center").pack(pady=(4, 0))
        for r in potjes:
            self.potje_card(inner, r)

    def potje_card(self, parent, row):
        c = self.card(parent)
        c.pack(fill="x", pady=6, ipady=10)
        head = tk.Frame(c, bg=CARD)
        head.pack(fill="x", padx=14)
        tk.Label(head, text="🫙  " + row["naam"], font=("Segoe UI", 11, "bold"), fg=TEXT,
                 bg=CARD).pack(side="left")
        tk.Label(head, text=eur(row["saldo"]), font=("Segoe UI", 12, "bold"), fg=GREEN,
                 bg=CARD).pack(side="right")
        doel = row["doel"] or 0
        pct = min(100.0, row["saldo"] / doel * 100.0) if doel > 0 else 0.0
        sub = tk.Frame(c, bg=CARD)
        sub.pack(fill="x", padx=14, pady=(2, 6))
        tk.Label(sub, text=f"Doel: {eur(doel)}" if doel > 0 else "Geen doelbedrag",
                 fg=MUTED, bg=CARD, font=FONT).pack(side="left")
        tk.Label(sub, text=f"{pct:.0f}%" if doel > 0 else "—", fg=GREEN, bg=CARD,
                 font=("Segoe UI", 8, "bold")).pack(side="right")
        bar = tk.Canvas(c, bg=CARD, highlightthickness=0, height=8)
        bar.pack(fill="x", padx=14, pady=(0, 8))

        def draw_bar(e=None):
            bar.delete("all")
            w = bar.winfo_width()
            if w <= 2:
                return
            bar.create_rectangle(0, 0, w, 8, fill=ACCENT_BG, outline="")
            if doel > 0:
                bar.create_rectangle(0, 0, w * pct / 100.0, 8, fill=GREEN, outline="")
        draw_bar()
        bar.bind("<Configure>", draw_bar)
        btns = tk.Frame(c, bg=CARD)
        btns.pack(fill="x", padx=14)
        self.outline_button(btns, "＋  Storten",
                            lambda r=row: self.potje_mutate_dialog(r["id"], r["naam"], 1)) \
            .pack(side="left", padx=(0, 6))
        self.outline_button(btns, "－  Opnemen",
                            lambda r=row: self.potje_mutate_dialog(r["id"], r["naam"], -1)) \
            .pack(side="left", padx=6)
        self.outline_button(btns, "Historie",
                            lambda r=row: self.potje_history(r["id"], r["naam"])) \
            .pack(side="left", padx=6)
        self.outline_button(btns, "Verwijderen",
                            lambda r=row: self.potje_delete_dialog(r["id"], r["naam"]),
                            fg=RED).pack(side="left", padx=6)

    def potje_add_dialog(self):
        dialog = tk.Toplevel(self)
        dialog.title("Nieuw spaarpotje")
        dialog.configure(bg=CARD)
        dialog.geometry("400x260")
        dialog.transient(self)
        tk.Label(dialog, text="Maak een spaarpotje", font=("Segoe UI", 12, "bold"),
                 fg=TEXT, bg=CARD).pack(anchor="w", padx=16, pady=(16, 2))
        tk.Label(dialog, text="Bijvoorbeeld: Vakantie, Reserve, Auto, Cadeaus.",
                 font=("Segoe UI", 9), fg=MUTED, bg=CARD).pack(anchor="w", padx=16)
        naam = self.form_entry(dialog, "Naam", "", 28)
        doel = self.form_entry(dialog, "Doelbedrag (€, kan leeg blijven)", "", 28)

        def save():
            naam_v = naam.get().strip()
            if not naam_v:
                messagebox.showwarning("Ontbreekt", "Vul een naam in.", parent=self)
                return
            dbm.potje_add(naam_v, _num(doel.get()))
            dialog.destroy()
            self.notify(f"Spaarpotje '{naam_v}' aangemaakt")
            self.navigate("potjes")
        self.green_button(dialog, "Aanmaken", save).pack(pady=16)

    def potje_mutate_dialog(self, pid: int, naam: str, sign: int):
        dialog = tk.Toplevel(self)
        dialog.title("Spaarpotje vullen" if sign > 0 else "Uit spaarpotje opnemen")
        dialog.configure(bg=CARD)
        dialog.geometry("400x280")
        dialog.transient(self)
        tk.Label(dialog, text=("🫙  " if sign > 0 else "🫙  ") + naam,
                 font=("Segoe UI", 12, "bold"), fg=TEXT, bg=CARD).pack(anchor="w", padx=16, pady=(16, 2))
        saldo = dbm.q("SELECT saldo FROM potjes WHERE id=?", (pid,))[0]["saldo"]
        tk.Label(dialog, text=f"Nu in het potje: {eur(saldo)}", font=("Segoe UI", 9),
                 fg=GREEN, bg=CARD).pack(anchor="w", padx=16)
        amount = self.form_entry(dialog, "Bedrag (€)", "", 28)
        note = self.form_entry(dialog, "Notitie (optioneel)", "", 28)

        def save():
            value = _num(amount.get())
            if value <= 0:
                messagebox.showwarning("Fout", "Vul een positief bedrag in.", parent=self)
                return
            if sign < 0:
                if value > saldo + 0.005:
                    messagebox.showwarning("Te weinig", 
                                           f"Er staat maar {eur(saldo)} in dit potje.", parent=self)
                    return
                value = -value
            dbm.potje_mutate(pid, value, note.get().strip())
            dialog.destroy()
            self.notify("Spaarpotje bijgewerkt")
            self.navigate("potjes")
        self.green_button(dialog, "Storten" if sign > 0 else "Opnemen", save).pack(pady=16)

    def potje_history(self, pid: int, naam: str):
        dialog = tk.Toplevel(self)
        dialog.title(f"Historie — {naam}")
        dialog.configure(bg=DARK)
        dialog.geometry("560x420")
        dialog.transient(self)
        muts = list(dbm.potje_mutaties(pid))
        saldo_now = dbm.q("SELECT saldo FROM potjes WHERE id=?", (pid,))[0]["saldo"]
        saldo = saldo_now - sum(m["amount"] for m in muts)
        tk.Label(dialog, text=f"Saldo-ontwikkeling van '{naam}'", font=("Segoe UI", 11, "bold"),
                 fg=TEXT, bg=DARK).pack(anchor="w", padx=16, pady=(14, 6))
        wrap = tk.Frame(dialog, bg=DARK)
        wrap.pack(fill="both", expand=True, padx=16)
        txt = tk.Text(wrap, bg=CARD, fg=TEXT, font=("Consolas", 9), relief="flat", bd=10,
                      insertbackground=GREEN, wrap="none")
        sbar = ttk.Scrollbar(wrap, orient="vertical", command=txt.yview)
        txt.configure(yscrollcommand=sbar.set)
        txt.pack(side="left", fill="both", expand=True)
        sbar.pack(side="right", fill="y")
        txt.insert("end", "  Datum          Bedrag        Saldo        Notitie\n")
        txt.insert("end", "  " + "─" * 66 + "\n")
        if not muts:
            txt.insert("end", "  Nog geen mutaties.\n")
        for m in muts:
            saldo += m["amount"]
            teken = "+" if m["amount"] >= 0 else ""
            note = m["note"] or ""
            txt.insert("end", f"  {m['mut_date']}    {teken}{eur(m['amount']):>14}    "
                              f"{eur(saldo):>14}    {note}\n")
        txt.configure(state="disabled")
        self.green_button(dialog, "Sluiten", dialog.destroy).pack(pady=10)

    def potje_delete_dialog(self, pid: int, naam: str):
        if messagebox.askyesno(
                "Spaarpotje verwijderen",
                f"Spaarpotje '{naam}' verwijderen?\nDe historie van dit potje gaat verloren.",
                parent=self):
            dbm.potje_delete(pid)
            self.notify(f"Spaarpotje '{naam}' verwijderd", RED)
            self.navigate("potjes")

    # ---------------- pagina: loonstrookjes ----------------
    def page_loon(self, root):
        self.title_bar(root, "Loonstrookjes", "PDF's inladen via Import, of hieronder handmatig")
        c = self.card(root)
        c.pack(fill="x", padx=16, pady=6, ipady=6)
        row = tk.Frame(c, bg=CARD)
        row.pack(fill="x", padx=14, pady=10)
        entries = {}
        for i, (key, label) in enumerate((("period", "Periode (JJJJ-MM)"),
                                          ("brutoloon", "Brutoloon"),
                                          ("loonheffing", "Loonheffing"),
                                          ("pensioen", "Pensioen"),
                                          ("vakantiegeld", "Vakantiegeld"))):
            tk.Label(row, text=label, fg=MUTED, bg=CARD, font=("Segoe UI", 8)) \
                .grid(row=0, column=i, padx=6, sticky="w")
            e = tk.Entry(row, width=14, bg=DARK, fg=TEXT, insertbackground=GREEN,
                         relief="flat", bd=5)
            e.grid(row=1, column=i, padx=6, ipady=2)
            entries[key] = e
        entries["period"].insert(0, "2025-01")

        def add():
            try:
                dbm.save_loonstrook(
                    entries["period"].get().strip(),
                    _num(entries["brutoloon"].get()),
                    _num(entries["loonheffing"].get()),
                    _num(entries["pensioen"].get()),
                    _num(entries["vakantiegeld"].get()),
                    "handmatig")
            except ValueError:
                messagebox.showerror("Fout", "Bedragen moeten getallen zijn.", parent=self)
                return
            self.notify("Loonstrook toegevoegd")
            self.navigate("loon")
        self.green_button(row, "Toevoegen", add).grid(row=2, column=0, columnspan=5,
                                                      sticky="w", padx=6, pady=(10, 0))

        _, table = self.table(root, [
            ("period", "Periode", 90, "w"),
            ("brutoloon", "Brutoloon", 110, "e"),
            ("loonheffing", "Loonheffing", 110, "e"),
            ("pensioen", "Pensioen", 110, "e"),
            ("vakantiegeld", "Vakantiegeld", 110, "e"),
            ("bron", "Bron", 220, "w"),
        ])
        for r in dbm.q("SELECT * FROM loonstroken ORDER BY period DESC"):
            table.insert("", "end", values=(
                r["period"], eur(r["brutoloon"]), eur(-abs(r["loonheffing"])),
                eur(-abs(r["pensioen"])), eur(r["vakantiegeld"]), r["source"]))

    # ---------------- pagina: ib ----------------
    def page_ib(self, root):
        self.title_bar(root, "IB-aangifte — uitwerking",
                       "Indicatief — controleer altijd de officiële cijfers in Mijn Belastingdienst")
        top = tk.Frame(root, bg=PANEL)
        top.pack(fill="x", padx=16)
        tk.Label(top, text="Belastingjaar", fg=MUTED, bg=PANEL, font=FONT).pack(side="left")
        year_box = self.combo(top, YEARS, 6, dbm.get_setting("huidig_jaar", "2025"))
        year_box.pack(side="left", padx=8)

        holder = tk.Frame(root, bg=PANEL)
        holder.pack(fill="both", expand=True, padx=10, pady=8)

        def render():
            for w in holder.winfo_children():
                w.destroy()
            result = ib.compute_year(year_box.get())
            left = self.card(holder)
            left.pack(side="left", fill="both", expand=True, padx=6)
            right = self.card(holder)
            right.pack(side="left", fill="y", padx=6, ipadx=10, ipady=10)
            right.configure(width=330)
            for section, rows, total in (
                    ("BOX I — Inkomsten en aftrekposten", result["box1"], result["box1_total"]),
                    ("BOX III — Vermogen (eindsaldo)", result["box3"], result["box3_total"])):
                tk.Label(left, text=section, font=("Segoe UI", 10, "bold"), fg=GREEN, bg=CARD) \
                    .pack(anchor="w", padx=16, pady=(12, 2))
                for label, value in rows:
                    line = tk.Frame(left, bg=CARD)
                    line.pack(fill="x", padx=16)
                    tk.Label(line, text=label, font=("Segoe UI", 9), fg=MUTED, bg=CARD) \
                        .pack(side="left")
                    tk.Label(line, text=ib.eur(value), font=("Segoe UI", 9, "bold"),
                             fg=TEXT, bg=CARD).pack(side="right")
                line = tk.Frame(left, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
                line.pack(fill="x", padx=16, pady=(4, 2))
                tk.Label(left, text="Totaal", font=("Segoe UI", 10, "bold"), fg=TEXT, bg=CARD) \
                    .pack(side="left", padx=16)
                tk.Label(left, text=ib.eur(total), font=("Segoe UI", 10, "bold"), fg=GREEN,
                         bg=CARD).pack(side="right", padx=16)
            tk.Label(left, text="Let op: spaarpotjes-geld is geld en telt mee als vermogen "
                                "in Box III (als opzij gezet tegoed).",
                     font=("Segoe UI", 8), fg=MUTED, bg=CARD, wraplength=560, justify="left") \
                .pack(anchor="w", padx=16, pady=(8, 0))

            tk.Label(right, text="VERWERKTE BRONNEN", font=("Segoe UI", 8, "bold"), fg=MUTED,
                     bg=CARD).pack(anchor="w", padx=14, pady=(10, 2))
            for k, v in (("Loonstroken", result["loonstroken_count"]),
                         ("Bankafschriften (regels)", result["tx_count"])):
                line = tk.Frame(right, bg=CARD)
                line.pack(fill="x", padx=14)
                tk.Label(line, text=k, font=("Segoe UI", 9), fg=MUTED, bg=CARD).pack(side="left")
                tk.Label(line, text=str(v), font=("Segoe UI", 9, "bold"), fg=TEXT, bg=CARD) \
                    .pack(side="right")
            tk.Label(right, text="Tips voor januari", font=("Segoe UI", 10, "bold"),
                     fg=TEXT, bg=CARD).pack(anchor="w", padx=14, pady=(14, 2))
            for tip in ("Laad december-afschriften in vóór de uitwerking",
                        "Vul eigenwoningforfait in bij Instellingen",
                        "Controleer de categorie 'Woning / Hypotheek'",
                        "Spaarpotjes tellen mee in Box III"):
                tk.Label(right, text="•  " + tip, font=("Segoe UI", 8), fg=MUTED, bg=CARD,
                         wraplength=290, justify="left").pack(anchor="w", padx=14, pady=1)

            def export():
                path = filedialog.asksaveasfilename(
                    parent=self, defaultextension=".csv",
                    initialfile=f"ib_uitwerking_{year_box.get()}.csv",
                    filetypes=[("CSV", "*.csv")])
                if path:
                    with open(path, "w", newline="", encoding="utf-8-sig") as f:
                        f.write(ib.export_csv(result))
                    messagebox.showinfo("Opgeslagen", f"CSV opgeslagen:\n{path}", parent=self)
                    self.notify("IB-uitwerking geëxporteerd")
            self.green_button(right, "Excel exporteren (CSV)", export).pack(pady=12)

        year_box.bind("<<ComboboxSelected>>", lambda e: render())
        render()

    # ---------------- pagina: rapporten ----------------
    def page_rapporten(self, root):
        self.title_bar(root, "Rapporten & Export")
        c = self.card(root)
        c.pack(fill="both", expand=True, padx=16, pady=6, ipady=14)
        tk.Label(c, text="Transacties exporteren", font=("Segoe UI", 12, "bold"),
                 fg=TEXT, bg=CARD).pack(anchor="w", padx=16)
        tk.Label(c, text="Alle transacties van het gekozen jaar naar CSV (Excel-compatibel).",
                 font=("Segoe UI", 9), fg=MUTED, bg=CARD).pack(anchor="w", padx=16, pady=(2, 8))
        year_box = self.combo(c, YEARS, 8, dbm.get_setting("huidig_jaar", "2025"))
        year_box.pack(anchor="w", padx=16)

        def export_tx():
            path = filedialog.asksaveasfilename(
                parent=self, defaultextension=".csv",
                initialfile=f"transacties_{year_box.get()}.csv", filetypes=[("CSV", "*.csv")])
            if path:
                with open(path, "w", newline="", encoding="utf-8-sig") as f:
                    f.write(ib.export_transactions_csv(year_box.get()))
                messagebox.showinfo("Opgeslagen", f"CSV opgeslagen:\n{path}", parent=self)
                self.notify("Transacties geëxporteerd")
        self.green_button(c, "Download transacties CSV", export_tx).pack(anchor="w", padx=16, pady=10)

    # ---------------- pagina: instellingen ----------------
    def page_instellingen(self, root):
        self.title_bar(root, "Instellingen", "Per jaar instelbare waarden voor de IB-uitwerking")
        scroll = tk.Canvas(root, bg=PANEL, highlightthickness=0)
        scroll.pack(side="left", fill="both", expand=True)
        sb = ttk.Scrollbar(root, orient="vertical", command=scroll.yview)
        sb.pack(side="right", fill="y")
        scroll.configure(yscrollcommand=sb.set)
        inner = tk.Frame(scroll, bg=PANEL)
        scroll.create_window((0, 0), window=inner, anchor="nw")
        inner.bind("<Configure>", lambda e: scroll.configure(scrollregion=scroll.bbox("all")))

        def on_scroll(e):
            scroll.configure(scrollregion=scroll.bbox("all"))
        root.bind("<Enter>", on_scroll, add="+")

        for y in YEARS:
            c = self.card(inner)
            c.pack(fill="x", padx=16, pady=6, ipady=10)
            tk.Label(c, text=f"Belastingjaar {y}", font=("Segoe UI", 11, "bold"),
                     fg=TEXT, bg=CARD).pack(anchor="w", padx=16)
            fields = {}
            for key, label in (
                    (f"eigenwoningforfait_{y}", "Eigenwoningforfait (€)"),
                    (f"hypotheekrente_{y}", "Hypotheekrenteaftrek (€, leeg = automatisch)"),
                    (f"beginsaldo_{y}", f"Beginsaldo banktegoeden op 1-1-{y} (€)"),
                    (f"schulden_{y}", f"Schulden per 31-12-{y} (€)")):
                fields[key] = self.form_entry(c, label, dbm.get_setting(key, ""), 24)

            def save_slot(y=y, fields=fields):
                for key, e in fields.items():
                    value = e.get().strip().replace("€", "")
                    dbm.set_setting(key, "" if not value else str(_num(value)))
                messagebox.showinfo("Opgeslagen", f"Instellingen {y} bewaard.", parent=self)
            self.green_button(c, f"Opslaan {y}", save_slot).pack(anchor="w", padx=16, pady=(10, 0))

        c2 = self.card(inner)
        c2.pack(fill="x", padx=16, pady=6, ipady=10)
        tk.Label(c2, text="Data & Privacy", font=("Segoe UI", 11, "bold"), fg=TEXT, bg=CARD) \
            .pack(anchor="w", padx=16)
        tk.Label(c2, text=f"Databank: {dbm.DATA_ENC}", font=("Segoe UI", 8), fg=MUTED,
                 bg=CARD, wraplength=800, justify="left").pack(anchor="w", padx=16)
        tk.Label(c2, text="Je data staat versleuteld (AES-256 via Fernet, PBKDF2 300k iteraties) op "
                          "je eigen pc. Er wordt niets naar het internet gestuurd.",
                 font=("Segoe UI", 9), fg=MUTED, bg=CARD, wraplength=800, justify="left") \
            .pack(anchor="w", padx=16, pady=4)

        def backup():
            if dbm.DATA_ENC.exists():
                path = filedialog.asksaveasfilename(
                    parent=self, defaultextension=".enc", initialfile="back-up-boekhouding.enc")
                if path:
                    with open(path, "wb") as f:
                        f.write(dbm.DATA_ENC.read_bytes())
                    messagebox.showinfo("Back-up", f"Back-up opgeslagen:\n{path}", parent=self)
                    self.notify("Back-up gemaakt", GREEN)
            else:
                messagebox.showwarning("Geen databank", "Er is nog geen databank.", parent=self)
        self.green_button(c2, "Back-up maken (versleuteld)", backup).pack(anchor="w", padx=16, pady=(6, 0))

    def on_close(self):
        dbm.lock_down()
        self.destroy()


# ---------------- tekenfuncties voor grafieken (tk.Canvas) ----------------

def draw_line_chart(canvas: tk.Canvas, year: str):
    _clean_canvas(canvas)
    w = int(canvas.winfo_width() or 700)
    h = int(canvas.winfo_height() or 230)
    pad_l, pad_r, pad_t, pad_b = 46, 12, 14, 24
    inc = [ib.month_income_in(year, m) for m in range(1, 13)]
    out = [ib.month_spend_in(year, m) for m in range(1, 13)]
    months = ["jan", "feb", "mrt", "apr", "mei", "jun", "jul", "aug", "sep", "okt", "nov", "dec"]
    all_vals = inc + out + [2600]
    vmax = max(all_vals) * 1.08 or 1
    if all(v == 0 for v in inc) and all(v == 0 for v in out):
        tk.Label(canvas, text="Nog geen data — laad eerst een bankbestand in via Import.",
                 fg=MUTED, bg=CARD, font=("Segoe UI", 10)).place(relx=0.5, rely=0.5, anchor="center")
        return

    def xy(i, v):
        x = pad_l + (w - pad_l - pad_r) * i / 11
        y = pad_t + (h - pad_t - pad_b) * (1 - v / vmax)
        return x, y

    for gy in range(5):
        v = vmax * gy / 4
        y1 = xy(0, v)[1]
        canvas.create_line(pad_l, y1, w - pad_r, y1, fill=BORDER, dash=(2, 4))
        canvas.create_text(pad_l - 6, y1, text=f"{v:,.0f}", fill=MUTED,
                           font=("Segoe UI", 7), anchor="e")
    base = h - pad_b
    for i, m in enumerate(months):
        x = xy(i, 0)[0]
        canvas.create_rectangle(x - 0.5, pad_t, x + 0.5, base, fill=CARD, outline="")
        canvas.create_text(x, base + 9, text=m, fill=MUTED, font=("Segoe UI", 7))
    pts_in = " ".join(f"{x:.0f},{y:.0f}" for x, y in [xy(i, v) for i, v in enumerate(inc)])
    pts_out = " ".join(f"{x:.0f},{y:.0f}" for x, y in [xy(i, v) for i, v in enumerate(out)])
    canvas.create_polygon(f"{pad_l},{base} " + pts_in + f" {w - pad_r},{base}",
                          fill=GREEN, stipple="gray25", outline="")
    canvas.create_polygon(f"{pad_l},{base} " + pts_out + f" {w - pad_r},{base}",
                          fill=BLUE, stipple="gray25", outline="")
    canvas.create_line(pts_in, fill=GREEN, width=2)
    canvas.create_line(pts_out, fill=BLUE, width=2)
    canvas.create_text(pad_l + 4, pad_t - 4, text="— inkomsten", fill=GREEN,
                       font=("Segoe UI", 7), anchor="w")
    canvas.create_text(pad_l + 74, pad_t - 4, text="— uitgaven", fill=BLUE,
                       font=("Segoe UI", 7), anchor="w")


def draw_donut(canvas: tk.Canvas, vast: float, variabel: float):
    _clean_canvas(canvas)
    total = vast + variabel
    w = int(canvas.winfo_width() or 320)
    cx, cy, r1, r2 = w // 2, 110, 92, 56
    if total <= 0:
        tk.Label(canvas, text="Nog geen kosten ingeladen.", fg=MUTED, bg=CARD,
                 font=("Segoe UI", 9)).place(relx=0.5, rely=0.45, anchor="center")
        canvas.create_text(cx, cy, text="—", fill=TEXT, font=("Segoe UI", 16, "bold"))
        canvas.create_text(cx, cy + 20, text="kosten p/m", fill=MUTED, font=("Segoe UI", 8))
    else:
        start = 90
        for value, color in ((vast, GREEN), (variabel, BLUE)):
            extent = -360 * (value / total)
            canvas.create_arc(cx - r1, cy - r1, cx + r1, cy + r1, start=start, extent=extent,
                              style="pieslice", fill=color, outline=CARD, width=3)
            start += extent
        canvas.create_oval(cx - r2, cy - r2, cx + r2, cy + r2, fill=CARD, outline=CARD)
        canvas.create_text(cx, cy - 10, text=eur(total / 12), fill=TEXT,
                           font=("Segoe UI", 13, "bold"))
        canvas.create_text(cx, cy + 8, text="kosten p/m", fill=MUTED, font=("Segoe UI", 8))
    base_y = (canvas.winfo_height() or 200) - 16
    canvas.create_text(16, base_y, text="● Vast", fill=GREEN, font=("Segoe UI", 8), anchor="w")
    canvas.create_text(90, base_y, text="● Variabel", fill=BLUE, font=("Segoe UI", 8), anchor="w")


def draw_top_categories(canvas: tk.Canvas, year: str):
    _clean_canvas(canvas)
    w = int(canvas.winfo_width() or 900)
    h = int(canvas.winfo_height() or 180)
    cats = dbm.q(
        "SELECT category, COALESCE(SUM(amount),0) s, kind FROM transactions "
        "WHERE substr(tx_date,1,4)=? AND amount<0 GROUP BY category ORDER BY s LIMIT 6", (year,))
    if not cats:
        tk.Label(canvas, text="Nog geen uitgaven ingeladen.", fg=MUTED, bg=CARD,
                 font=("Segoe UI", 10)).place(relx=0.5, rely=0.5, anchor="center")
        return
    values = [abs(r["s"]) for r in cats]
    vmax = max(values) or 1
    pad_l = 170
    bar_h = 16
    gap = (h - 12) / max(1, len(cats))
    for i, (r, v) in enumerate(zip(cats, values)):
        y = 8 + i * gap
        x_end = pad_l + (w - pad_l - 90) * v / vmax
        color = GREEN if r["kind"] == "vast" else BLUE
        canvas.create_rectangle(pad_l, y, x_end, y + bar_h, fill=color, outline="")
        canvas.create_text(pad_l - 10, y + bar_h / 2, text=r["category"][:24], fill=TEXT,
                           font=("Segoe UI", 8), anchor="e")
        canvas.create_text(x_end + 8, y + bar_h / 2, text=eur(v), fill=MUTED,
                           font=("Segoe UI", 8), anchor="w")


def draw_categories_bar(canvas: tk.Canvas, year: str):
    _clean_canvas(canvas)
    w = int(canvas.winfo_width() or 900)
    h = int(canvas.winfo_height() or 400)
    cats = dbm.q(
        "SELECT category, COALESCE(SUM(amount),0) s, kind FROM transactions "
        "WHERE substr(tx_date,1,4)=? AND amount<0 GROUP BY category ORDER BY s", (year,))
    if not cats:
        tk.Label(canvas, text="Nog geen uitgaven ingeladen — gebruik Import / Upload.",
                 fg=MUTED, bg=CARD, font=("Segoe UI", 10)).place(relx=0.5, rely=0.5, anchor="center")
        return
    values = [abs(r["s"]) for r in cats]
    vmax = max(values) or 1
    pad_l = 190
    gap = (h - 20) / len(cats)
    bar_h = min(18, gap * 0.6)
    for i, (r, v) in enumerate(zip(cats, values)):
        y = 12 + i * gap
        x_end = pad_l + (w - pad_l - 90) * v / vmax
        color = GREEN if r["kind"] == "vast" else BLUE
        canvas.create_rectangle(pad_l, y, x_end, y + bar_h, fill=color, outline="")
        canvas.create_text(pad_l - 10, y + bar_h / 2, text=r["category"][:26], fill=TEXT,
                           font=("Segoe UI", 8), anchor="e")
        canvas.create_text(x_end + 8, y + bar_h / 2, text=eur(v), fill=MUTED,
                           font=("Segoe UI", 8), anchor="w")


def style_table(table: ttk.Treeview):
    style = ttk.Style(table)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass
    style.configure("Treeview", background=CARD, foreground=TEXT, fieldbackground=CARD,
                    bordercolor=BORDER, borderwidth=0, rowheight=26, font=FONT)
    style.configure("Treeview.Heading", background="#0A1A30", foreground=MUTED,
                    font=("Segoe UI", 8, "bold"), borderwidth=0, relief="flat")
    style.map("Treeview", background=[("selected", ACCENT_BG)],
              foreground=[("selected", GREEN)])
    style.map("Treeview.Heading", background=[("active", "#0A1A30")])
    table.tag_configure("in", foreground=GREEN)
    table.tag_configure("out", foreground=TEXT)
    table.tag_configure("done", foreground="#8FB38F")
    table.tag_configure("stripe", background=STRIPE)


def main():
    app = App()
    app.protocol("WM_DELETE_WINDOW", app.on_close)
    app.mainloop()


if __name__ == "__main__":
    main()

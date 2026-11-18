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
PANEL = "#0F2240"
DARK = "#081220"
BORDER = "#1C3A63"
RED = "#FF5D73"

MENU = [
    ("Dashboard", "dashboard"),
    ("Transacties", "transacties"),
    ("Import / Upload", "import"),
    ("Kosteninzicht", "kosten"),
    ("Loonstrookjes", "loon"),
    ("IB-aangifte", "ib"),
    ("Rapporten", "rapporten"),
    ("Instellingen", "instellingen"),
]

YEARS = ["2024", "2025", "2026"]


def eur(value: float) -> str:
    s = f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"€ {s}"


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Rick's Boekhoud Programma")
        self.geometry("1280x720")
        self.minsize(1100, 640)
        self.configure(bg=DARK)
        self.menu_buttons: dict[str, tk.Button] = {}
        self.show_lock()

    # ---------------- lock / hoofdwachtwoord ----------------
    def show_lock(self, set_new: bool | None = None):
        for w in self.winfo_children():
            w.destroy()
        frame = tk.Frame(self, bg=DARK)
        frame.place(relx=0.5, rely=0.5, anchor="center")
        tk.Label(frame, text="●", font=("Segoe UI", 20, "bold"), fg=GREEN, bg=DARK).pack()
        tk.Label(frame, text="RICK'S BOEKHOUD PROGRAMMA", font=("Segoe UI", 16, "bold"),
                 fg=TEXT, bg=DARK).pack(pady=(0, 6))
        set_new = set_new if set_new is not None else not dbm.has_master()
        if set_new:
            tk.Label(frame, text="Stel een hoofdwachtwoord in.\nDit versleutelt al je data lokaal (AES-256).",
                     fg=MUTED, bg=DARK, font=("Segoe UI", 10), justify="left").pack(pady=(0, 10))
            pw1 = tk.Entry(frame, show="●", width=32, bg=CARD, fg=TEXT, insertbackground=TEXT,
                           relief="flat", bd=6)
            pw2 = tk.Entry(frame, show="●", width=32, bg=CARD, fg=TEXT, insertbackground=TEXT,
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
                self.show_main()
            tk.Button(frame, text="Start", command=create, bg=GREEN, fg="#062318",
                      font=("Segoe UI", 10, "bold"), relief="flat", width=30).pack(ipady=3)
        else:
            tk.Label(frame, text="Voer je hoofdwachtwoord in.", fg=MUTED, bg=DARK,
                     font=("Segoe UI", 10)).pack(pady=(0, 10))
            pw = tk.Entry(frame, show="●", width=32, bg=CARD, fg=TEXT, insertbackground=TEXT,
                          relief="flat", bd=6)
            pw.pack(ipady=2)

            def unlock(event=None):
                if dbm.unlock(pw.get()):
                    self.show_main()
                else:
                    messagebox.showerror("Fout", "Verkeerd wachtwoord.")
            pw.bind("<Return>", unlock)
            tk.Button(frame, text="Openen", command=unlock, bg=GREEN, fg="#062318",
                      font=("Segoe UI", 10, "bold"), relief="flat", width=30).pack(pady=(10, 0), ipady=3)
            pw.focus_set()

    # ---------------- hoofdscherm ----------------
    def show_main(self):
        for w in self.winfo_children():
            w.destroy()
        sidebar = tk.Frame(self, bg="#0B1B30", width=220)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)
        header = tk.Frame(self, bg="#0A1522", height=36)
        header.pack(side="top", fill="x")
        header.pack_propagate(False)
        tk.Label(header, text="RICK'S BOEKHOUD PROGRAMMA", font=("Segoe UI", 10, "bold"),
                 fg=TEXT, bg="#0A1522").pack(side="left", padx=14)
        tk.Label(header, text="Lokaal versleuteld — SQLite", font=("Segoe UI", 9),
                 fg=GREEN, bg="#0A1522").pack(side="right", padx=14)
        self.content = tk.Frame(self, bg=PANEL)
        self.content.pack(side="right", fill="both", expand=True)

        logo_row = tk.Frame(sidebar, bg="#0B1B30")
        logo_row.pack(fill="x", pady=(14, 10))
        tk.Label(logo_row, text="●", font=("Segoe UI", 11, "bold"), fg=GREEN,
                 bg="#0B1B30").pack(side="left", padx=(16, 6))
        tk.Label(logo_row, text="MENU", font=("Segoe UI", 10, "bold"), fg=GREEN,
                 bg="#0B1B30").pack(side="left")
        for label, key in MENU:
            btn = tk.Button(sidebar, text=label, anchor="w", relief="flat", bd=0,
                            font=("Segoe UI", 10), bg="#0B1B30", fg=TEXT, padx=18, pady=8,
                            activebackground="#153055", activeforeground=GREEN,
                            command=lambda k=key: self.navigate(k))
            btn.pack(fill="x", padx=6, pady=1)
            self.menu_buttons[key] = btn
        tk.Button(sidebar, text="Vergrendelen", anchor="w", relief="flat", bd=0,
                  font=("Segoe UI", 9), bg="#0B1B30", fg=MUTED, padx=18, pady=6,
                  activebackground="#153055",
                  command=self.lock_now).pack(side="bottom", fill="x")
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.navigate("dashboard")

    def lock_now(self):
        dbm.lock_down()
        self.show_lock()

    def navigate(self, key: str):
        for k, btn in self.menu_buttons.items():
            if k == key:
                btn.configure(bg="#153055", fg=GREEN, font=("Segoe UI", 10, "bold"))
            else:
                btn.configure(bg="#0B1B30", fg=TEXT, font=("Segoe UI", 10))
        for w in self.content.winfo_children():
            w.destroy()
        page = {
            "dashboard": self.page_dashboard,
            "transacties": self.page_transacties,
            "import": self.page_import,
            "kosten": self.page_kosten,
            "loon": self.page_loon,
            "ib": self.page_ib,
            "rapporten": self.page_rapporten,
            "instellingen": self.page_instellingen,
        }[key]
        page(self.content)

    # ---------------- kleine bouwstenen ----------------
    def title_bar(self, parent, title, subtitle=""):
        top = tk.Frame(parent, bg=PANEL)
        top.pack(fill="x", padx=16, pady=(14, 6))
        tk.Label(top, text=title, font=("Segoe UI", 16, "bold"), fg=TEXT, bg=PANEL) \
            .pack(side="left")
        if subtitle:
            tk.Label(top, text=subtitle, font=("Segoe UI", 9), fg=MUTED, bg=PANEL) \
                .pack(side="left", padx=14)
        return top

    def card(self, parent, **pack):
        frame = tk.Frame(parent, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
        frame.pack(**pack)
        return frame

    def kpi(self, parent, label, value, sub="", color=TEXT):
        box = self.card(parent)
        box.pack(side="left", fill="both", expand=True, padx=6, pady=6)
        box.configure(padx=14, pady=10)
        tk.Label(box, text=label, font=("Segoe UI", 8, "bold"), fg=MUTED, bg=CARD) \
            .pack(anchor="w")
        tk.Label(box, text=value, font=("Segoe UI", 18, "bold"), fg=TEXT, bg=CARD) \
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

    # ---------------- pagina: dashboard ----------------
    def page_dashboard(self, root):
        self.title_bar(root, "Dashboard", "Belastingjaar-overzicht")
        year = dbm.get_setting("huidig_jaar", "2025")
        row = tk.Frame(root, bg=PANEL)
        row.pack(fill="x", padx=10)
        inkomen = ib.month_income(year)
        uitgaven = ib.month_spend(year)
        vast = ib.month_vast(year)
        variabel = ib.month_variabel(year)
        maanden = ib.maanden_met_data(year)
        self.kpi(row, "TOTAAL SALDO", eur(inkomen - uitgaven), "inkomsten - uitgaven", GREEN)
        self.kpi(row, f"INKOMMEN {year}", eur(inkomen), "loon + overig")
        self.kpi(row, f"UITGAVEN {year}", eur(uitgaven), "alle kostenposten", RED)
        self.kpi(row, f"VASTE LASTEN P/M {year}", eur(vast / max(1, maanden)),
                 f"variabel: {eur(abs(variabel) / max(1, maanden))}", MUTED)

        charts_row = tk.Frame(root, bg=PANEL)
        charts_row.pack(fill="both", expand=True, padx=10, pady=6)
        c1 = self.card(charts_row)
        c1.pack(side="left", fill="both", expand=True, padx=6)
        tk.Label(c1, text="Inkomsten vs. Uitgaven per maand", font=("Segoe UI", 10, "bold"),
                 fg=TEXT, bg=CARD).pack(anchor="w", padx=14, pady=(10, 0))
        canvas_line = tk.Canvas(c1, bg=CARD, highlightthickness=0, height=230)
        canvas_line.pack(fill="both", expand=True, padx=10, pady=6)
        draw_line_chart(canvas_line, year)

        c2 = self.card(charts_row)
        c2.pack(side="left", fill="y", padx=6)
        c2.configure(width=340)
        tk.Label(c2, text="Vast vs. Variabel", font=("Segoe UI", 10, "bold"), fg=TEXT,
                 bg=CARD).pack(anchor="w", padx=14, pady=(10, 0))
        canvas_donut = tk.Canvas(c2, bg=CARD, highlightthickness=0, height=200, width=320)
        canvas_donut.pack(padx=10, pady=6)
        draw_donut(canvas_donut, abs(vast), abs(variabel))

        c3 = self.card(root)
        c3.pack(fill="both", expand=True, padx=16, pady=(0, 12))
        tk.Label(c3, f"Grootste kostenposten {year}", font=("Segoe UI", 10, "bold"), fg=TEXT,
                 bg=CARD).pack(anchor="w", padx=14, pady=(10, 0))
        canvas_bar = tk.Canvas(c3, bg=CARD, highlightthickness=0, height=180)
        canvas_bar.pack(fill="both", expand=True, padx=10, pady=6)
        draw_top_categories(canvas_bar, year)

    # ---------------- pagina: transacties ----------------
    def page_transacties(self, root):
        self.title_bar(root, "Transacties", "Klik op een regel om categorie/type aan te passen")
        controls = tk.Frame(root, bg=PANEL)
        controls.pack(fill="x", padx=16, pady=4)
        years = [r[0] for r in dbm.q(
            "SELECT DISTINCT substr(tx_date,1,4) FROM transactions ORDER BY 1")] or ["2025"]
        state = {"year": dbm.get_setting("huidig_jaar", "2025"), "cat": "", "kind": ""}

        tk.Label(controls, text="Jaar:", fg=MUTED, bg=PANEL, font=("Segoe UI", 9)) \
            .pack(side="left")
        year_box = ttk.Combobox(controls, values=years, width=8, state="readonly")
        year_box.set(state["year"])
        year_box.pack(side="left", padx=(6, 16))
        tk.Label(controls, text="Categorie:", fg=MUTED, bg=PANEL, font=("Segoe UI", 9)) \
            .pack(side="left")
        cat_box = ttk.Combobox(controls, values=["(alle)"] + categorize.all_categories(),
                               width=22, state="readonly")
        cat_box.set("(alle)")
        cat_box.pack(side="left", padx=(6, 16))
        tk.Label(controls, text="Type:", fg=MUTED, bg=PANEL, font=("Segoe UI", 9)).pack(side="left")
        kind_box = ttk.Combobox(controls, values=["(alle)", "vast", "variabel", "inkomsten"],
                                width=10, state="readonly")
        kind_box.set("(alle)")
        kind_box.pack(side="left", padx=6)

        wrap = tk.Frame(root, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
        wrap.pack(fill="both", expand=True, padx=16, pady=8)
        cols = ("datum", "omschrijving", "tegenrekening", "bedrag", "categorie", "type")
        table = ttk.Treeview(wrap, columns=cols, show="headings", selectmode="browse")
        for cid, text, w, anchor in (
            ("datum", "Datum", 90, "w"), ("omschrijving", "Omschrijving", 320, "w"),
            ("tegenrekening", "Tegenrekening", 160, "w"), ("bedrag", "Bedrag", 110, "e"),
            ("categorie", "Categorie", 170, "w"), ("type", "Type", 90, "e"),
        ):
            table.heading(cid, text=text)
            table.column(cid, width=w, anchor=anchor)
        scrollbar = ttk.Scrollbar(wrap, orient="vertical", command=table.yview)
        table.configure(yscrollcommand=scrollbar.set)
        table.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        style_table(table)

        status = tk.Label(root, text="", fg=MUTED, bg=PANEL, font=("Segoe UI", 9), anchor="w")
        status.pack(fill="x", padx=18)

        def refresh():
            nonlocal state
            state["year"] = year_box.get()
            state["cat"] = "" if cat_box.get() == "(alle)" else cat_box.get()
            state["kind"] = "" if kind_box.get() == "(alle)" else kind_box.get()
            table.delete(*table.get_children())
            sql = ("SELECT id, tx_date, description, contra_account, amount, category, kind "
                   "FROM transactions WHERE substr(tx_date,1,4)=?")
            params: list = [state["year"]]
            if state["cat"]:
                sql += " AND category=?"; params.append(state["cat"])
            if state["kind"]:
                sql += " AND kind=?"; params.append(state["kind"])
            sql += " ORDER BY tx_date DESC"
            total_out = 0.0
            for r in dbm.q(sql, tuple(params)):
                values = (r["tx_date"], r["description"][:60], r["contra_account"][:22],
                          eur(r["amount"]), r["category"], r["kind"])
                tag = "in" if r["amount"] >= 0 else "out"
                table.insert("", "end", iid=str(r["id"]), values=values, tags=(tag,))
                if r["amount"] < 0:
                    total_out += r["amount"]
            status.config(text=f"{len(table.get_children())} transacties  |  "
                               f"uitgaven: {eur(total_out)}")
        year_box.bind("<<ComboboxSelected>>", lambda e: refresh())
        cat_box.bind("<<ComboboxSelected>>", lambda e: refresh())
        kind_box.bind("<<ComboboxSelected>>", lambda e: refresh())

        def edit(event):
            sel = table.selection()
            if not sel:
                return
            tx_id = sel[0]
            row = dbm.q("SELECT * FROM transactions WHERE id=?", (int(tx_id),))[0]
            dialog = tk.Toplevel(self)
            dialog.title("Transactie aanpassen")
            dialog.configure(bg=PANEL)
            dialog.geometry("420x300")
            dialog.transient(self)
            tk.Label(dialog, text=row["description"][:60], fg=MUTED, bg=PANEL,
                     font=("Segoe UI", 9), wraplength=380).pack(anchor="w", padx=16, pady=(16, 4))
            tk.Label(dialog, text="Datum: " + row["tx_date"] + "   Bedrag: " + eur(row["amount"]),
                     fg=TEXT, bg=PANEL, font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=16)
            tk.Label(dialog, text="Categorie:", fg=MUTED, bg=PANEL, font=("Segoe UI", 9)) \
                .pack(anchor="w", padx=16, pady=(14, 0))
            cat_sel = ttk.Combobox(dialog, values=categorize.all_categories(),
                                   state="readonly", width=28)
            cat_sel.set(row["category"])
            cat_sel.pack(anchor="w", padx=16)
            tk.Label(dialog, text="Type:", fg=MUTED, bg=PANEL, font=("Segoe UI", 9)) \
                .pack(anchor="w", padx=16, pady=(10, 0))
            kind_sel = ttk.Combobox(dialog, values=categorize.KINDS, state="readonly", width=28)
            kind_sel.set(row["kind"])
            kind_sel.pack(anchor="w", padx=16)

            def save():
                dbm.execute("UPDATE transactions SET category=?, kind=? WHERE id=?",
                            (cat_sel.get(), kind_sel.get(), int(tx_id)))
                dialog.destroy()
                refresh()
                messagebox.showinfo("Opgeslagen", "Wijziging bewaard.", parent=self)
            self.green_button(dialog, "Opslaan", save).pack(pady=18)
        table.bind("<Double-1>", edit)
        refresh()

    # ---------------- pagina: import ----------------
    def page_import(self, root):
        self.title_bar(root, "Import / Upload",
                       "Bankbestand (CAMT.053 / CSV / MT940) en loonstroken (PDF)")
        row = tk.Frame(root, bg=PANEL)
        row.pack(fill="x", padx=16, pady=6)
        c1 = self.card(row)
        c1.pack(side="left", fill="both", expand=True, padx=6, ipady=16, ipadx=10)
        tk.Label(c1, text="BANKBESTAND", font=("Segoe UI", 9, "bold"), fg=GREEN, bg=CARD) \
            .pack(anchor="w", padx=16)
        tk.Label(c1, text="Importeren voor transacties", font=("Segoe UI", 12, "bold"),
                 fg=TEXT, bg=CARD).pack(anchor="w", padx=16, pady=(2, 0))
        tk.Label(c1, text="CAMT.053 (XML)  |  CSV  |  MT940", font=("Segoe UI", 9), fg=MUTED,
                 bg=CARD).pack(anchor="w", padx=16)
        self.green_button(c1, "Bestand kiezen...", self.pick_bank).pack(anchor="w", padx=16, pady=(14, 0))

        c2 = self.card(row)
        c2.pack(side="left", fill="both", expand=True, padx=6, ipady=16, ipadx=10)
        tk.Label(c2, text="LOONSTROOK / JAARINFORMATIE", font=("Segoe UI", 9, "bold"),
                 fg=BLUE, bg=CARD).pack(anchor="w", padx=16)
        tk.Label(c2, text="PDF van je werkgever inlezen", font=("Segoe UI", 12, "bold"),
                 fg=TEXT, bg=CARD).pack(anchor="w", padx=16, pady=(2, 0))
        tk.Label(c2, text="Cijfers gaan automatisch naar de IB-aangifte", font=("Segoe UI", 9),
                 fg=MUTED, bg=CARD).pack(anchor="w", padx=16)
        self.green_button(c2, "PDF kiezen...", self.pick_loon).pack(anchor="w", padx=16, pady=(14, 0))

        c3 = self.card(root)
        c3.pack(fill="both", expand=True, padx=16, pady=8)
        tk.Label(c3, text="LAATSTE IMPORT", font=("Segoe UI", 9, "bold"), fg=MUTED, bg=CARD) \
            .pack(anchor="w", padx=16, pady=(10, 2))
        tk.Label(c3, text=dbm.stamp(), font=("Segoe UI", 9), fg=MUTED, bg=CARD) \
            .pack(anchor="w", padx=16)

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
                                f"Controleer de categorieën op de pagina Transacties.", parent=self)
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
        dialog.configure(bg=PANEL)
        dialog.geometry("440x420")
        dialog.transient(self)
        tk.Label(dialog, text="Bestand: " + name, fg=MUTED, bg=PANEL,
                 font=("Segoe UI", 9)).pack(anchor="w", padx=16, pady=(16, 0))
        tk.Label(dialog, text="Controleer de waarden (uit de PDF gelezen)\nen pas aan indien nodig.",
                 fg=TEXT, bg=PANEL, font=("Segoe UI", 10, "bold"), justify="left") \
            .pack(anchor="w", padx=16, pady=(4, 8))
        entries = {}
        for key, label in (("period", "Periode (JJJJ-MM)"), ("brutoloon", "Brutoloon"),
                           ("loonheffing", "Loonheffing"), ("pensioen", "Pensioenpremie"),
                           ("vakantiegeld", "Vakantiegeld")):
            tk.Label(dialog, text=label, fg=MUTED, bg=PANEL, font=("Segoe UI", 9)) \
                .pack(anchor="w", padx=16, pady=(6, 0))
            value = fields.get(key)
            entry = tk.Entry(dialog, width=30, bg=CARD, fg=TEXT, insertbackground=TEXT,
                             relief="flat", bd=6)
            entry.insert(0, "" if value is None else str(value))
            entry.pack(anchor="w", padx=16, ipady=2)
            entries[key] = entry

        def save():
            try:
                dbm.save_loonstrook(
                    entries["period"].get().strip(),
                    float((entries["brutoloon"].get() or "0").replace(",", ".") or 0),
                    float((entries["loonheffing"].get() or "0").replace(",", ".") or 0),
                    float((entries["pensioen"].get() or "0").replace(",", ".") or 0),
                    float((entries["vakantiegeld"].get() or "0").replace(",", ".") or 0),
                    name)
            except ValueError:
                messagebox.showerror("Fout", "Bedragen moeten getallen zijn.", parent=self)
                return
            dialog.destroy()
            messagebox.showinfo("Opgeslagen", "Loonstrook opgeslagen.", parent=self)
            self.navigate("loon")
        self.green_button(dialog, "Opslaan", save).pack(pady=16)

    # ---------------- pagina: kosten ----------------
    def page_kosten(self, root):
        self.title_bar(root, "Kosteninzicht", "Alle kostenposten per categorie")
        year = dbm.get_setting("huidig_jaar", "2025")
        c = self.card(root)
        c.pack(fill="both", expand=True, padx=16, pady=6)
        tk.Label(c, text=f"Uitgaven per categorie {year} — groen = vast, blauw = variabel",
                 font=("Segoe UI", 10, "bold"), fg=TEXT, bg=CARD).pack(anchor="w", padx=14, pady=(10, 0))
        canvas = tk.Canvas(c, bg=CARD, highlightthickness=0)
        canvas.pack(fill="both", expand=True, padx=10, pady=8)
        draw_categories_bar(canvas, year)

    # ---------------- pagina: loonstrookjes ----------------
    def page_loon(self, root):
        self.title_bar(root, "Loonstrookjes", "Laad PDF's in via Import, of vul hieronder handmatig aan")
        c = self.card(root)
        c.pack(fill="x", padx=16, pady=6)
        row = tk.Frame(c, bg=CARD)
        row.pack(fill="x", padx=14, pady=12)
        entries = {}
        for i, (key, label) in enumerate((("period", "Periode (JJJJ-MM)"), ("brutoloon", "Brutoloon"),
                                          ("loonheffing", "Loonheffing"), ("pensioen", "Pensioen"),
                                          ("vakantiegeld", "Vakantiegeld"))):
            tk.Label(row, text=label, fg=MUTED, bg=CARD, font=("Segoe UI", 9)) \
                .grid(row=0, column=i, padx=6, sticky="w")
            e = tk.Entry(row, width=14, bg="#0A1A30", fg=TEXT, insertbackground=TEXT,
                         relief="flat", bd=5)
            e.grid(row=1, column=i, padx=6, ipady=2)
            entries[key] = e
        entries["period"].insert(0, "2025-01")

        def add():
            try:
                dbm.save_loonstrook(
                    entries["period"].get().strip(),
                    float(entries["brutoloon"].get().replace(",", ".") or 0),
                    float(entries["loonheffing"].get().replace(",", ".") or 0),
                    float(entries["pensioen"].get().replace(",", ".") or 0),
                    float(entries["vakantiegeld"].get().replace(",", ".") or 0),
                    "handmatig")
            except ValueError:
                messagebox.showerror("Fout", "Bedragen moeten getallen zijn.", parent=self)
                return
            messagebox.showinfo("Toegevoegd", "Loonstrook toegevoegd.", parent=self)
            self.navigate("loon")
        self.green_button(row, "Toevoegen", add).grid(row=2, column=0, columnspan=5,
                                                      sticky="w", padx=6, pady=(10, 0))

        wrap = tk.Frame(root, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
        wrap.pack(fill="both", expand=True, padx=16, pady=(0, 12))
        cols = ("period", "brutoloon", "loonheffing", "pensioen", "vakantiegeld", "bron")
        table = ttk.Treeview(wrap, columns=cols, show="headings", selectmode="browse")
        for cid, text, w, anchor in (
            ("period", "Periode", 90, "w"), ("brutoloon", "Brutoloon", 110, "e"),
            ("loonheffing", "Loonheffing", 110, "e"), ("pensioen", "Pensioen", 110, "e"),
            ("vakantiegeld", "Vakantiegeld", 110, "e"), ("bron", "Bron", 200, "w"),
        ):
            table.heading(cid, text=text)
            table.column(cid, width=w, anchor=anchor)
        scrollbar = ttk.Scrollbar(wrap, orient="vertical", command=table.yview)
        table.configure(yscrollcommand=scrollbar.set)
        table.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        style_table(table)
        for r in dbm.q("SELECT * FROM loonstroken ORDER BY period DESC"):
            table.insert("", "end", values=(
                r["period"], eur(r["brutoloon"]), eur(-abs(r["loonheffing"])),
                eur(-abs(r["pensioen"])), eur(r["vakantiegeld"]), r["source"]))

    # ---------------- pagina: ib ----------------
    def page_ib(self, root):
        self.title_bar(root, "IB-aangifte — uitwerking",
                       "Indicatief — controleer altijd de officiële cijfers in Mijn Belastingdienst")
        year_sel_frame = tk.Frame(root, bg=PANEL)
        year_sel_frame.pack(fill="x", padx=16)
        tk.Label(year_sel_frame, text="Belastingjaar:", fg=MUTED, bg=PANEL,
                 font=("Segoe UI", 9)).pack(side="left")
        year_box = ttk.Combobox(year_sel_frame, values=YEARS, width=8, state="readonly")
        year_box.set(dbm.get_setting("huidig_jaar", "2025"))
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
            right.configure(width=320)
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
                tk.Label(left, text="Totaal", font=("Segoe UI", 10, "bold"), fg=TEXT, bg=CARD,
                         ).pack(side="left", padx=16)
                tk.Label(left, text=ib.eur(total), font=("Segoe UI", 10, "bold"), fg=GREEN,
                         bg=CARD).pack(side="right", padx=16)
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
                        "Controleer de categorie 'Woning / Hypotheek'"):
                tk.Label(right, text="• " + tip, font=("Segoe UI", 8), fg=MUTED, bg=CARD,
                         wraplength=280, justify="left").pack(anchor="w", padx=14, pady=1)

            def export():
                path = filedialog.asksaveasfilename(
                    parent=self, defaultextension=".csv",
                    initialfile=f"ib_uitwerking_{year_box.get()}.csv",
                    filetypes=[("CSV", "*.csv")])
                if path:
                    with open(path, "w", newline="", encoding="utf-8-sig") as f:
                        f.write(ib.export_csv(result))
                    messagebox.showinfo("Opgeslagen", f"CSV opgeslagen:\n{path}", parent=self)
            self.green_button(right, "Excel exporteren (CSV)", export).pack(pady=12)

        def on_year(e=None):
            render()
        year_box.bind("<<ComboboxSelected>>", on_year)
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
        year_box = ttk.Combobox(c, values=YEARS, width=8, state="readonly")
        year_box.set(dbm.get_setting("huidig_jaar", "2025"))
        year_box.pack(anchor="w", padx=16)

        def export_tx():
            path = filedialog.asksaveasfilename(
                parent=self, defaultextension=".csv",
                initialfile=f"transacties_{year_box.get()}.csv", filetypes=[("CSV", "*.csv")])
            if path:
                with open(path, "w", newline="", encoding="utf-8-sig") as f:
                    f.write(ib.export_transactions_csv(year_box.get()))
                messagebox.showinfo("Opgeslagen", f"CSV opgeslagen:\n{path}", parent=self)
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

        for y in YEARS:
            c = self.card(inner)
            c.pack(fill="x", padx=16, pady=6, ipady=10)
            tk.Label(c, text=f"Belastingjaar {y}", font=("Segoe UI", 11, "bold"),
                     fg=TEXT, bg=CARD).pack(anchor="w", padx=16)
            fields = {}
            for key, label, default in (
                    (f"eigenwoningforfait_{y}", "Eigenwoningforfait (€)", ""),
                    (f"hypotheekrente_{y}", "Hypotheekrenteaftrek (€, leeg = automatisch)", ""),
                    (f"beginsaldo_{y}", f"Beginsaldo banktegoeden op 1-1-{y} (€)", ""),
                    (f"schulden_{y}", f"Schulden per 31-12-{y} (€)", "")):
                tk.Label(c, text=label, font=("Segoe UI", 8), fg=MUTED, bg=CARD) \
                    .pack(anchor="w", padx=16, pady=(6, 0))
                e = tk.Entry(c, width=24, bg="#0A1A30", fg=TEXT, insertbackground=TEXT,
                             relief="flat", bd=5)
                e.insert(0, dbm.get_setting(key, default))
                e.pack(anchor="w", padx=16, ipady=2)
                fields[key] = e

            def save_slot(y=y, fields=fields):
                for key, e in fields.items():
                    dbm.set_setting(key, e.get().strip().replace(",", "."))
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
            else:
                messagebox.showwarning("Geen databank", "Er is nog geen databank.", parent=self)
        self.green_button(c2, "Back-up maken (versleuteld)", backup).pack(anchor="w", padx=16, pady=(6, 0))

    def on_close(self):
        dbm.lock_down()
        self.destroy()


# ---------------- tekenfuncties voor grafieken (tk.Canvas) ----------------

def draw_line_chart(canvas: tk.Canvas, year: str):
    canvas.delete("all")
    w = int(canvas.winfo_width() or 700)
    h = int(canvas.winfo_height() or 230)
    pad_l, pad_r, pad_t, pad_b = 46, 12, 14, 24
    inc = [ib.month_income_in(year, m) for m in range(1, 13)]
    out = [ib.month_spend_in(year, m) for m in range(1, 13)]
    months = ["jan", "feb", "mrt", "apr", "mei", "jun", "jul", "aug", "sep", "okt", "nov", "dec"]
    all_vals = inc + out + [2600]
    vmax = max(all_vals) * 1.08 or 1

    def xy(i, v):
        x = pad_l + (w - pad_l - pad_r) * i / 11
        y = pad_t + (h - pad_t - pad_b) * (1 - v / vmax)
        return x, y

    if all(v == 0 for v in inc) and all(v == 0 for v in out):
        tk.Label(canvas, text="Nog geen data — laad eerst een bankbestand in via Import.",
                 fg=MUTED, bg=CARD, font=("Segoe UI", 10)).place(relx=0.5, rely=0.5, anchor="center")
        return
    for gy in range(5):
        v = vmax * gy / 4
        x1, y1 = xy(0, v), xy(0, v)[1]
        canvas.create_line(pad_l, y1, w - pad_r, y1, fill=BORDER, dash=(2, 4))
        canvas.create_text(pad_l - 6, y1, text=f"{v:.0f}" if vmax > 10000 else f"{v:,.0f}",
                           fill=MUTED, font=("Segoe UI", 7), anchor="e")
    for i, m in enumerate(months):
        x, y = xy(i, 0)
        x, y = x, h - pad_b
        canvas.create_rectangle(x - 0.5, pad_t, x + 0.5, y, fill=CARD, outline="")
        canvas.create_text(x, y + 9, text=m, fill=MUTED, font=("Segoe UI", 7))
    pts_in = " ".join(f"{x:.0f},{y:.0f}" for x, y in [xy(i, v) for i, v in enumerate(inc)])
    pts_out = " ".join(f"{x:.0f},{y:.0f}" for x, y in [xy(i, v) for i, v in enumerate(out)])
    base = h - pad_b
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
    canvas.delete("all")
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
        tk.Label(canvas, text="").place(x=0, y=0)
        canvas.create_oval(cx - r2, cy - r2, cx + r2, cy + r2, fill=CARD, outline=CARD)
        canvas.create_text(cx, cy - 10, text=eur(total / 12), fill=TEXT,
                           font=("Segoe UI", 13, "bold"))
        canvas.create_text(cx, cy + 8, text="kosten p/m", fill=MUTED, font=("Segoe UI", 8))
    base_y = (canvas.winfo_height() or 200) - 16
    canvas.create_text(16, base_y, text="● Vast", fill=GREEN,
                       font=("Segoe UI", 8), anchor="w")
    canvas.create_text(90, base_y, text="● Variabel", fill=BLUE, font=("Segoe UI", 8), anchor="w")


def draw_top_categories(canvas: tk.Canvas, year: str):
    canvas.delete("all")
    w = int(canvas.winfo_width() or 900)
    h = int(canvas.winfo_height() or 180)
    cats = dbm.q(
        "SELECT category, COALESCE(SUM(amount),0) s FROM transactions "
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
        x_end = pad_l + (w - pad_l - 60) * v / vmax
        color = GREEN if r["kind"] == "vast" else BLUE
        canvas.create_rectangle(pad_l, y, x_end, y + bar_h, fill=color, outline="")
        canvas.create_text(pad_l - 10, y + bar_h // 2, text=r["category"][:24], fill=TEXT,
                           font=("Segoe UI", 8), anchor="e")
        canvas.create_text(x_end + 8, y + bar_h // 2, text=f"{v / values[0] * 100:.0f}%"
                           if values[0] else "", fill=MUTED, font=("Segoe UI", 8), anchor="w")


def draw_categories_bar(canvas: tk.Canvas, year: str):
    canvas.delete("all")
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
        x_end = pad_l + (w - pad_l - 70) * v / vmax
        color = GREEN if r["kind"] == "vast" else BLUE
        canvas.create_rectangle(pad_l, y, x_end, y + bar_h, fill=color, outline="")
        canvas.create_text(pad_l - 10, y + bar_h / 2, text=r["category"][:26], fill=TEXT,
                           font=("Segoe UI", 8), anchor="e")
        canvas.create_text(x_end + 8, y + bar_h / 2, text=f"{eur(v)}  ({v / values[0] * 100:.0f}%"
                           if values[0] else eur(v), fill=MUTED, font=("Segoe UI", 8), anchor="w")


def style_table(table: ttk.Treeview):
    style = ttk.Style(table)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass
    style.configure("Treeview", background=CARD, foreground=TEXT, fieldbackground=CARD,
                    bordercolor=BORDER, borderwidth=0, rowheight=26, font=("Segoe UI", 9))
    style.configure("Treeview.Heading", background="#0A1A30", foreground=MUTED,
                    font=("Segoe UI", 8, "bold"), borderwidth=0, relief="flat")
    style.map("Treeview", background=[("selected", "#153055")],
              foreground=[("selected", GREEN)])
    style.map("Treeview.Heading", background=[("active", "#0A1A30")])
    table.tag_configure("in", foreground=GREEN)
    table.tag_configure("out", foreground=TEXT)


def main():
    app = App()
    app.protocol("WM_DELETE_WINDOW", app.on_close)
    app.mainloop()


if __name__ == "__main__":
    main()
